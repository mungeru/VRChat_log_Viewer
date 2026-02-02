"""
VRChat ログビューアー - プログレスダイアログ

読み込み進捗を表示するダイアログ
"""

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """プログレスバー付きダイアログ"""
    
    def __init__(self, parent, title="読み込み中..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        # ウィンドウを閉じるボタンを無効化
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # メッセージラベル
        self.message_label = ttk.Label(
            main_frame,
            text="準備中...",
            font=("", 10)
        )
        self.message_label.pack(pady=(0, 10))
        
        # プログレスバー
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            length=360
        )
        self.progress.pack(pady=10)
        
        # パーセンテージラベル
        self.percent_label = ttk.Label(
            main_frame,
            text="0%",
            font=("", 9)
        )
        self.percent_label.pack(pady=(0, 10))
        
        # キャンセルボタン
        self.cancel_button = ttk.Button(
            main_frame,
            text="キャンセル",
            command=self._on_cancel
        )
        self.cancel_button.pack()
        
        self.cancelled = False
        self.on_cancel_callback = None
    
    def set_progress(self, message: str, percentage: int):
        """進捗を更新"""
        try:
            self.message_label.config(text=message)
            self.progress['value'] = percentage
            self.percent_label.config(text=f"{percentage}%")
            self.dialog.update_idletasks()  # 描画を強制更新
            self.dialog.update()  # イベント処理
        except tk.TclError:
            # ダイアログが破棄された場合
            pass
    
    def set_on_cancel(self, callback):
        """キャンセルコールバックを設定"""
        self.on_cancel_callback = callback
    
    def _on_cancel(self):
        """キャンセルボタンが押された"""
        self.cancelled = True
        self.cancel_button.config(state='disabled', text="キャンセル中...")
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def close(self):
        """ダイアログを閉じる"""
        try:
            self.dialog.grab_release()
            self.dialog.destroy()
        except:
            pass
