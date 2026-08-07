@echo off
setlocal
where python >nul 2>nul
if errorlevel 1 (
  echo HHC-KUR-001: Python bulunamadi. Python 3.11+ kurup tekrar deneyin.
  exit /b 1
)
python "%~dp0scripts\install_global.py" --install
exit /b %errorlevel%
