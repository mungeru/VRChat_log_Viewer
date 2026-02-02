"""
VRChat ログビューアー - エラーログ付き起動スクリプト

エクスプローラーから起動時のエラーをログファイルに記録
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

# エラーログファイルのパス
ERROR_LOG_FILE = Path(__file__).parent / "error_log.txt"

def log_error(error_message):
    """エラーをログファイルに記録"""
    try:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n{'='*70}\n")
            f.write(f"エラー発生時刻: {timestamp}\n")
            f.write(f"{'='*70}\n")
            f.write(error_message)
            f.write(f"\n{'='*70}\n\n")
    except Exception as e:
        # ログ書き込みに失敗した場合でもプログラムは続行
        print(f"ログ書き込みエラー: {e}")

def main():
    """メイン起動処理"""
    try:
        # メインアプリケーションをインポート
        import tkinter as tk
        from vrchat_log_viewer import VRChatLogViewer
        
        # アプリケーション起動
        root = tk.Tk()
        app = VRChatLogViewer(root)
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"インポートエラー:\n{str(e)}\n\n"
        error_msg += f"トレースバック:\n{traceback.format_exc()}\n\n"
        error_msg += "必要なファイルが揃っているか確認してください。\n"
        error_msg += "必要なファイル:\n"
        error_msg += "- vrchat_log_viewer.pyw (メインファイル)\n"
        error_msg += "- async_loader.py\n"
        error_msg += "- constants.py\n"
        error_msg += "- models.py\n"
        error_msg += "- progress_dialog.py\n"
        error_msg += "- utils.py\n"
        error_msg += "- ui_builder.py\n"
        error_msg += "- theme_manager.py\n"
        error_msg += "- plugin_manager.py\n"
        
        log_error(error_msg)
        
        # エラーダイアログを表示
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "起動エラー",
                f"モジュールが見つかりません:\n\n{str(e)}\n\n"
                f"詳細は error_log.txt を確認してください。"
            )
        except:
            pass
        
    except Exception as e:
        error_msg = f"予期しないエラー:\n{str(e)}\n\n"
        error_msg += f"トレースバック:\n{traceback.format_exc()}\n"
        
        log_error(error_msg)
        
        # エラーダイアログを表示
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "予期しないエラー",
                f"アプリケーション起動中にエラーが発生しました:\n\n{str(e)}\n\n"
                f"詳細は error_log.txt を確認してください。"
            )
        except:
            pass

if __name__ == "__main__":
    main()
