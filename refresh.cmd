@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo  AI 미디어 리터러시 - 책 갱신
echo  (새 사건 감지 -> 페이지 재생성 -> 검증 -> push)
echo ============================================
echo.

set "PYEXE="
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
  where py >nul 2>nul && set "PYEXE=py -3"
)
if not defined PYEXE (
  for /d %%D in ("%LOCALAPPDATA%\hermes\tools\.reclaim-*") do (
    if exist "%%D\python.exe" set "PYEXE=%%D\python.exe"
  )
)
if not defined PYEXE (
  echo [ERROR] Python not found. Put python or py on PATH.
  pause
  exit /b 1
)

echo Python: %PYEXE%
echo.
%PYEXE% "_tools\refresh_all.py" --push
echo.
echo ============================================
echo  Done. Nothing is pushed when there is no change.
echo ============================================
pause
