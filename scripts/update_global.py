#!/usr/bin/env python3
"""HHC global kit self-update. GitHub releases kontrolü → manifest+zip indir → sha256 doğrula → content-sync."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sys, tempfile, urllib.error, urllib.request, zipfile
from pathlib import Path

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


def _content_sync(staging: str | Path, current: str | Path,
                  manifest_files: dict[str, str], self_script: str) -> int:
    """Manifest rehberli staging→current kopya; stale sil; self-skip; boş dizin temizle.
    Dönen: swapped dosya sayısı."""
    staging_path = Path(staging)
    current_path = Path(current)
    self_path = Path(self_script).resolve()
    swapped = 0

    # 1. Manifest'teki her dosyayı kopyala/atla
    for rel_path, expected_sha in manifest_files.items():
        dst = current_path / rel_path
        src = staging_path / rel_path
        if not src.is_file():
            continue
        # Kendi script'imizi atla (Windows self-kilit)
        try:
            if dst.resolve() == self_path:
                continue
        except Exception:
            pass
        need_copy = False
        if not dst.is_file():
            need_copy = True
        else:
            if _sha256_file(dst) != expected_sha:
                need_copy = True
        if need_copy:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            swapped += 1

    # 2. Manifest'te olmayan current dosyalarını sil (stale)
    current_files: set[str] = set()
    for p in current_path.rglob('*'):
        if p.is_file():
            rel = str(p.relative_to(current_path)).replace('\\', '/')
            try:
                if p.resolve() == self_path:
                    continue
            except Exception:
                pass
            current_files.add(rel)

    manifest_set = {k.replace('\\', '/') for k in manifest_files}
    for rel in sorted(current_files - manifest_set):
        p_file = current_path / rel
        try:
            if p_file.is_file():
                p_file.unlink()
        except Exception:
            pass

    # 3. Boş dizin temizle (alttan yukarı)
    for p in sorted(current_path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            try:
                p.rmdir()
            except Exception:
                pass

    return swapped


def main() -> int:
    ap = argparse.ArgumentParser(description='HHC global kit self-update (GitHub releases)')
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
        return 0

    # ── Uzak sürüm kontrolü ──
    print('Uzak sürüm kontrol ediliyor...', file=sys.stderr)
    api_url = f'https://api.github.com/repos/{REPO}/releases/latest'
    token = args.token if args.token else None
    release, err = _fetch_json(api_url, token, args.timeout)

    if err:
        # Non-fatal: ağ/API hatası → fallback
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
        return 0

    if not isinstance(release, dict):
        result = {'status': 'NO_RELEASES', 'current_version': current_ver,
                  'notice': 'Geçersiz GitHub API yanıtı.'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    tag_name = release.get('tag_name', '')
    if not tag_name:
        result = {'status': 'NO_RELEASES', 'current_version': current_ver,
                  'notice': 'Release tag_name bulunamadı.'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    latest_tuple = _normalize_version(tag_name)

    if latest_tuple is None or current_tuple is None:
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name,
                  'notice': 'Sürüm çözümlenemedi, güvenli taraf UP_TO_DATE.'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    cmp = _compare(latest_tuple, current_tuple)
    if cmp == '==':
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if cmp == '<':
        result = {'status': 'UP_TO_DATE', 'current_version': current_ver,
                  'latest_version': tag_name,
                  'notice': 'Uzak sürüm yerelden eski; downgrade yapılmaz.'}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # cmp == '>' → güncelleme gerekli
    print(f'Yeni sürüm bulundu: {tag_name}. İndiriliyor...', file=sys.stderr)

    assets = release.get('assets', [])
    if not isinstance(assets, list):
        assets = []

    manifest_asset = None
    zip_asset = None
    manifest_name = f'RELEASE-MANIFEST-{tag_name}.json'
    zip_name = f'HHC-AI-Team-Kit-{tag_name}.zip'
    for a in assets:
        aname = a.get('name', '')
        if aname == manifest_name:
            manifest_asset = a
        elif aname == zip_name:
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
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(staging)

        swapped = _content_sync(staging, current_path, manifest_files, __file__)

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
