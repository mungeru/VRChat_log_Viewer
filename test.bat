@echo off
chcp 65001 >nul
echo ========================================
echo   VRChat ログビューアー v2.0　テスト用多分いらないこの起動用.batファイル
echo ========================================
echo.
echo 起動中...
echo.

python vrchat_log_viewer_modular.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   エラーが発生しました
    echo ========================================
    echo.
    echo Pythonがインストールされていることを確認してください。
    echo Python 3.7以上が必要です。
    echo.
    echo Python公式サイト: https://www.python.org/
    echo.
    pause
)
