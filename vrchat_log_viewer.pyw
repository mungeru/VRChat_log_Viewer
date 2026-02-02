"""
VRChat ログビューアー v2.1 - 起動スクリプト

このファイルをダブルクリックして起動してください
"""

import sys
from pathlib import Path

# lib/フォルダをインポートパスに追加
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    sys.path.insert(0, str(lib_path))
else:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "エラー",
        f"lib/フォルダが見つかりません:\n\n{lib_path}\n\n"
        "すべてのファイルを正しく配置してください。"
    )
    sys.exit(1)

# メインアプリケーションを起動
try:
    import tkinter as tk
    from vrchat_log_viewer import VRChatLogViewer
    
    root = tk.Tk()
    app = VRChatLogViewer(root)
    root.mainloop()
    
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "インポートエラー",
        f"必要なモジュールが見つかりません:\n\n{e}\n\n"
        "lib/フォルダにすべてのファイルがあるか確認してください。"
    )
    sys.exit(1)
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    import traceback
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "起動エラー",
        f"アプリケーションの起動に失敗しました:\n\n{e}\n\n"
        f"詳細:\n{traceback.format_exc()}"
    )
    sys.exit(1)
