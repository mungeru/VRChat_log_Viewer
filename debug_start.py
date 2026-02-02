"""
VRChat ログビューアー v2.1 - デバッグ起動

エラーメッセージを表示します
"""

import sys
import traceback
from pathlib import Path

print("=" * 70)
print("VRChat ログビューアー v2.1 - デバッグモード")
print("=" * 70)
print()

# カレントディレクトリを表示
print(f"📁 カレントディレクトリ: {Path.cwd()}")
print(f"📁 スクリプトディレクトリ: {Path(__file__).parent}")
print()

# lib/フォルダをインポートパスに追加
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))
    print(f"✓ lib/フォルダを検出: {lib_path}")
else:
    print(f"✗ lib/フォルダが見つかりません: {lib_path}")
    print()
    print("エラー: lib/フォルダが必要です")
    print("すべてのファイルを正しく配置してください")
    input("\nEnterキーを押して終了...")
    sys.exit(1)

print()

# 必要なファイルの存在確認
print("ファイル確認中...")
required_files = [
    "vrchat_log_viewer.py",
    "virtual_treeview.py",  # 仮想レンダリング
    "async_loader.py",
    "constants.py",
    "models.py",
    "progress_dialog.py",
    "utils.py",
    "ui_builder.py",
    "theme_manager.py",
    "plugin_manager.py"
]

all_files_exist = True
for filename in required_files:
    file_path = lib_path / filename
    exists = file_path.exists()
    status = "✓" if exists else "✗"
    print(f"  {status} {filename}")
    if not exists:
        all_files_exist = False

print()

if not all_files_exist:
    print("エラー: 必要なファイルが見つかりません！")
    print("lib/フォルダに以下のファイルが必要です:")
    for filename in required_files:
        print(f"  - {filename}")
    input("\nEnterキーを押して終了...")
    sys.exit(1)

print("✓ すべての必要なファイルが見つかりました")
print()
print("アプリケーションを起動中...")
print()

try:
    import tkinter as tk
    
    # メインアプリケーションをインポート
    from vrchat_log_viewer import VRChatLogViewer
    print("✓ メインモジュールのインポート成功")
    
    # アプリケーション起動
    print("✓ ウィンドウを作成中...")
    root = tk.Tk()
    
    print("✓ アプリケーションを初期化中...")
    app = VRChatLogViewer(root)
    
    print("✓ 起動完了！")
    print()
    print("=" * 70)
    print("アプリケーションが起動しました")
    print("このコンソールはウィンドウを閉じるまで開いたままにしてください")
    print("=" * 70)
    print()
    
    root.mainloop()
    
    print()
    print("アプリケーションが正常に終了しました")

except Exception as e:
    print()
    print("=" * 70)
    print("❌ エラーが発生しました！")
    print("=" * 70)
    print()
    print(f"エラー: {e}")
    print()
    print("詳細:")
    print(traceback.format_exc())
    print()
    print("=" * 70)
    print("解決方法:")
    print("1. Python 3.7以上がインストールされているか確認")
    print("2. lib/フォルダにすべてのファイルがあるか確認")
    print("3. このエラーメッセージをスクリーンショットして報告")
    print("=" * 70)
    print()
    input("Enterキーを押して終了...")
    sys.exit(1)
