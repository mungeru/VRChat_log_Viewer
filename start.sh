#!/bin/bash

echo "========================================"
echo "  VRChat ログビューアー v2.0"
echo "========================================"
echo ""
echo "起動中..."
echo ""

python3 vrchat_log_viewer_modular.py

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "  エラーが発生しました"
    echo "========================================"
    echo ""
    echo "Pythonがインストールされていることを確認してください。"
    echo "Python 3.7以上が必要です。"
    echo ""
    echo "Python公式サイト: https://www.python.org/"
    echo ""
    read -p "Enterキーを押して終了..."
fi
