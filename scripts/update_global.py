#!/usr/bin/env python3
"""HHC global kit güncelleyicisi. GitHub sürüm kontrolü → manifest+zip indir → SHA-256 doğrula → içerik senkronu."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys, tempfile, urllib.error, urllib.request, zipfile
from pathlib import Path, PurePosixPath

# install_global.py ile aynı scripts/ dizininde; import sırasında KIT hesaplaması güvenli.
from install_global import runtime_root, install_bootstrap

REPO = 'huseyincig/HHC-AI-Team-Kit'
TIMEOUT = 30


def _fetch_json(url: str, token: str | None = None, timeout: float = TIMEOUT) -> tuple[dict | None, str | None]:
    """urllib ile JSON GET; non-fatal (data, error) döner."""
    headers = {'User-Agent': 'HHC-AI-Team-Kit/updater'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode('utf-8'))
        return data, None
    except urllib.error.HTTPError as e:
        body = {}
        remaining = None
        try:
            body = json.loads(e.read().decode('utf-8'))
        except Exception:
            pass
        try:
            remaining = e.headers.get('X-RateLimit-Remaining')
        except Exception:
            pass
        error_msg = f'HTTP {e.code}: {e.reason}'
        if remaining == '0':
            error_msg += ' (rate limited)'
        return body, error_msg
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def _download(url: str, dest: str | Path, timeout: float = TIMEOUT) -> tuple[str | None, str | None]:
    """Chunked download → sha256; (sha_hex, error) döner."""
    headers = {'User-Agent': 'HHC-AI-Team-Kit/updater'}
    h = hashlib.sha256()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            with open(dest, 'wb') as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
                    f.write(chunk)
        return h.hexdigest(), None
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def _normalize_version(v: str) -> tuple[int, ...] | None:
    """'v1.1.1' → (1,1,1). Non-numerik → None (güvenli taraf: UP_TO_DATE)."""
    v = v.lstrip('vV')
    try:
        return tuple(int(x) for x in v.split('.'))
    except (ValueError, TypeError):
        return None


def _compare(a: tuple[int, ...], b: tuple[int, ...]) -> str:
    """Numerik tuple karşılaştırma; '>', '==', '<' döner."""
    if a > b:
        return '>'
    if a < b:
        return '<'
    return '=='


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _safe_manifest_rel(raw: str) -> str:
    """Manifest yolunu platformdan bağımsız güvenli relative POSIX yoluna doğrular."""
    if not isinstance(raw, str) or not raw or '\x00' in raw:
        raise ValueError(f'Geçersiz manifest yolu: {raw!r}')
    value=raw.replace('\\','/')
    path=PurePosixPath(value)
    if path.is_absolute() or any(part in ('','..') for part in path.parts):
        raise ValueError(f'Güvensiz manifest yolu: {raw!r}')
    if path.parts and len(path.parts[0]) >= 2 and path.parts[0][1] == ':':
        raise ValueError(f'Güvensiz manifest drive yolu: {raw!r}')
    return path.as_posix()


def _validate_staging(staging: Path, manifest_files: dict[str, str]) -> dict[str, str]:
    """Her manifest dosyasını current runtime'a dokunmadan önce existence + SHA ile doğrular."""
    checked: dict[str, str] = {}
    for raw, expected_sha in manifest_files.items():
        rel=_safe_manifest_rel(raw)
        if rel in checked:
            raise ValueError(f'Yinelenen manifest yolu: {rel}')
        if not isinstance(expected_sha,str) or not re.fullmatch(r'[0-9a-fA-F]{64}',expected_sha):
            raise ValueError(f'Geçersiz SHA-256: {raw!r}')
        src=staging.joinpath(*PurePosixPath(rel).parts)
        if src.is_symlink() or not src.is_file():
            raise ValueError(f'Manifest dosyası staging içinde yok veya güvenli değil: {rel}')
        actual=_sha256_file(src)
        if actual.lower()!=expected_sha.lower():
            raise ValueError(f'Manifest dosya bütünlüğü hatası: {rel}')
        checked[rel]=expected_sha.lower()
    return checked

def _atomic_copy(src: Path, dst: Path) -> None:
    """Aynı dizindeki geçici dosya üzerinden atomik değişim yap; hata halinde hedefi bozma."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + '.hhc-new')
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _content_sync(staging: str | Path, current: str | Path,
                  manifest_files: dict[str, str], self_script: str) -> int:
    """Manifest rehberli senkronizasyon. Updater kendisini en son atomik olarak yeniler."""
    staging_path = Path(staging)
    current_path = Path(current)
    self_path = Path(self_script).resolve()
    manifest_files = _validate_staging(staging_path, manifest_files)
    swapped = 0
    self_item: tuple[Path, Path, str] | None = None

    for rel_path, expected_sha in manifest_files.items():
        rel_parts=PurePosixPath(rel_path).parts
        dst = current_path.joinpath(*rel_parts)
        src = staging_path.joinpath(*rel_parts)
        if not src.is_file():
            continue
        try:
            is_self = dst.resolve() == self_path
        except Exception:
            is_self = False
        if is_self:
            self_item=(src,dst,expected_sha)
            continue
        if not dst.is_file() or _sha256_file(dst) != expected_sha:
            _atomic_copy(src,dst)
            swapped += 1

    # Çalışan updater en son değiştirilir. Başarısız olursa VERSION henüz ilerletilmediği için
    # sonraki çalıştırma yeniden deneyebilir ve eski sağlam dosya korunur.
    if self_item is not None:
        src,dst,expected_sha=self_item
        if not dst.is_file() or _sha256_file(dst) != expected_sha:
            _atomic_copy(src,dst)
            swapped += 1

    current_files: set[str] = set()
    for p in current_path.rglob('*'):
        if p.is_file() and not p.name.endswith('.hhc-new'):
            current_files.add(str(p.relative_to(current_path)).replace('\\','/'))
    manifest_set = {k.replace('\\','/') for k in manifest_files}
    for rel in sorted(current_files - manifest_set):
        p_file=current_path/rel
        try:
            if p_file.resolve()==self_path:
                continue
        except Exception:
            pass
        try:
            p_file.unlink()
        except OSError:
            pass

    for p in sorted(current_path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir():
            try:
                if not any(p.iterdir()): p.rmdir()
            except OSError:
                pass
    return swapped


def main() -> int:
    ap = argparse.ArgumentParser(description='HHC global kit güncellemesi (GitHub sürümleri)')
    ap.add_argument('--no-remote', action='store_true', help='Ağ kontrolünü atla, yalnız yerel')
    ap.add_argument('--token', default=os.environ.get('HHC_GITHUB_TOKEN', ''),
                    help='GitHub token (varsayılan HHC_GITHUB_TOKEN env)')
    ap.add_argument('--timeout', type=float, default=TIMEOUT,
                    help=f'Ağ zaman aşımı (saniye, varsayılan {TIMEOUT})')
    args = ap.parse_args()

    current_path = runtime_root()
    version_file = current_path / 'VERSION'

    if not version_file.is_file():
        result = {'status': 'ERROR',
                  'error': 'Global kit VERSION bulunamadı. HHC-KUR çalıştırın.',
                  'path': str(current_path)}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    current_ver = version_file.read_text().strip()
    current_tuple = _normalize_version(current_ver)

    if args.no_remote:
        result = {'status': 'LOCAL_ONLY', 'current_version': current_ver,
                  'notice': '--no-remote: ağ kontrolü atlandı.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    # ── Uzak sürüm kontrolü ──
    print('Uzak sürüm kontrol ediliyor...', file=sys.stderr)
    api_url = f'https://api.github.com/repos/{REPO}/releases/latest'
    token = args.token if args.token else None
    release, err = _fetch_json(api_url, token, args.timeout)

    if err:
        # Öldürücü olmayan ağ/API hatası → yerel davranışa dön
        err_lower = err.lower()
        if 'rate limited' in err_lower:
            status = 'RATE_LIMITED'
        elif '404' in err:
            status = 'NO_RELEASES'
        else:
            status = 'OFFLINE'
        result = {'status': status, 'current_version': current_ver,
                  'notice': f'Ağ/API hatası ({err}). Yerel senkron devam.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    if not isinstance(release, dict):
        result = {'status': 'NO_RELEASES', 'current_version': current_ver,
                  'notice': 'Geçersiz GitHub API yanıtı.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    tag_name = release.get('tag_name', '')
    if not tag_name:
        result = {'status': 'NO_RELEASES', 'current_version': current_ver,
                  'notice': 'Release tag_name bulunamadı.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    latest_tuple = _normalize_version(tag_name)

    if latest_tuple is None or current_tuple is None:
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name,
                  'notice': 'Sürüm çözümlenemedi, güvenli taraf UP_TO_DATE.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    cmp = _compare(latest_tuple, current_tuple)
    if cmp == '==':
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0
    if cmp == '<':
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name,
                  'notice': 'Uzak sürüm yerelden eski; downgrade yapılmaz.'}
        print(json.dumps(result, ensure_ascii=False))
        install_bootstrap(current_path)
        return 0

    # cmp == '>' → güncelleme gerekli
    print(f'Yeni sürüm bulundu: {tag_name}. İndiriliyor...', file=sys.stderr)

    assets = release.get('assets', [])
    if not isinstance(assets, list):
        assets = []

    manifest_asset = None
    zip_asset = None
    release_version = tag_name.lstrip('vV')
    manifest_names = {f'RELEASE-MANIFEST-{release_version}.json', f'RELEASE-MANIFEST-{tag_name}.json'}
    zip_names = {f'HHC-AI-Team-Kit-{release_version}.zip', f'HHC-AI-Team-Kit-{tag_name}.zip'}
    for a in assets:
        aname = a.get('name', '')
        if aname in manifest_names:
            manifest_asset = a
        elif aname in zip_names:
            zip_asset = a

    if not manifest_asset or not zip_asset:
        result = {'status': 'ERROR', 'current_version': current_ver,
                  'latest_version': tag_name,
                  'error': f'Release asset bulunamadı: {"manifest" if not manifest_asset else "zip"}'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    manifest_url = manifest_asset.get('browser_download_url', '')
    zip_url = zip_asset.get('browser_download_url', '')
    if not manifest_url.startswith('https://') or not zip_url.startswith('https://'):
        result = {'status': 'ERROR',
                  'error': 'Asset URL HTTPS değil; güvenlik nedeniyle durduruldu.'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    tmpdir = tempfile.mkdtemp(prefix='hhc-update-')
    try:
        # Manifest indir
        print('Manifest indiriliyor...', file=sys.stderr)
        manifest_data, err = _fetch_json(manifest_url, token, args.timeout)
        if err or not isinstance(manifest_data, dict):
            result = {'status': 'ERROR',
                      'error': f'Manifest indirilemedi: {err}'}
            print(json.dumps(result, ensure_ascii=False))
            return 0

        expected_archive_sha = manifest_data.get('archive_sha256', '')
        manifest_files = manifest_data.get('files', {})
        if not expected_archive_sha or not isinstance(manifest_files, dict) or not manifest_files:
            result = {'status': 'ERROR',
                      'error': 'Manifest eksik: archive_sha256 veya files yok/boş.'}
            print(json.dumps(result, ensure_ascii=False))
            return 0

        # Zip indir
        print('Zip indiriliyor...', file=sys.stderr)
        zip_path = Path(tmpdir) / 'update.zip'
        zip_sha, err = _download(zip_url, zip_path, args.timeout)
        if err or not zip_sha:
            result = {'status': 'ERROR',
                      'error': f'Zip indirilemedi: {err}'}
            print(json.dumps(result, ensure_ascii=False))
            return 0

        # Bütünlük doğrulama (sha256)
        if zip_sha != expected_archive_sha:
            result = {'status': 'ERROR',
                      'error': (f'Bütünlük hatası: zip sha256={zip_sha[:16]}… '
                                f'beklenen={expected_archive_sha[:16]}…')}
            print(json.dumps(result, ensure_ascii=False))
            return 0

        print('Bütünlük doğrulandı.', file=sys.stderr)

        # Zip aç ve content-sync
        staging = Path(tmpdir) / 'staging'
        staging.mkdir()
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(staging)
            swapped = _content_sync(staging, current_path, manifest_files, __file__)
        except (OSError, ValueError, zipfile.BadZipFile) as e:
            result = {'status': 'ERROR', 'current_version': current_ver,
                      'latest_version': tag_name,
                      'error': f'Release içerik doğrulaması başarısız: {e}'}
            print(json.dumps(result, ensure_ascii=False))
            return 0

        # VERSION'ı güncelle (lstrip 'vV' ile normalize)
        new_ver = tag_name.lstrip('vV')
        (current_path / 'VERSION').write_text(new_ver, encoding='utf-8', newline='')

        # Bootstrap yenile (OpenCode komutları)
        install_bootstrap(current_path)

        result = {'status': 'UPDATED', 'current_version': new_ver,
                  'latest_version': tag_name, 'swapped_files': swapped}
        print(json.dumps(result, ensure_ascii=False))
        print(f'Global kit güncellendi: {current_ver} → {new_ver} ({swapped} dosya değişti).',
              file=sys.stderr)
        return 0

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
