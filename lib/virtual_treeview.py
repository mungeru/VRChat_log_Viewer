"""
VRChat ログビューアー - 仮想レンダリング対応ログビュー

見えている範囲だけを描画して高速化
Geminiに教えてもらった方式を実装
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable


class VirtualLogTreeview:
    """仮想レンダリング対応のTreeview（見える範囲だけ描画）"""
    
    def __init__(self, parent, columns, callbacks):
        # コンテナ
        self.container = ttk.Frame(parent)
        
        # Treeview作成
        self.tree = ttk.Treeview(
            self.container,
            columns=columns,
            show="tree headings",
            selectmode="extended",
            style="Dark.Treeview"
        )
        
        # ヘッダー設定
        self.tree.heading("time", text="時刻")
        self.tree.heading("level", text="レベル")
        self.tree.heading("content", text="内容")
        
        # カラム幅
        self.tree.column("#0", width=30)
        self.tree.column("time", width=150)
        self.tree.column("level", width=80)
        self.tree.column("content", width=800)
        
        # スクロールバー
        self.scrollbar_y = ttk.Scrollbar(self.container, orient=tk.VERTICAL, command=self._on_scroll)
        self.scrollbar_x = ttk.Scrollbar(self.container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=self._on_scrollbar_set, xscrollcommand=self.scrollbar_x.set)
        
        # レイアウト
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # イベント
        self.tree.bind("<Double-Button-1>", callbacks.get('on_log_double_click'))
        self.tree.bind("<Button-3>", callbacks.get('show_log_context_menu'))
        self.tree.bind("<Configure>", self._on_resize)
        
        # 仮想レンダリング用データ
        self.all_logs = []  # 全ログデータ
        self.visible_range = (0, 0)  # 現在表示中の範囲
        self.total_items = 0
        self.viewport_lines = 50  # 1画面に表示する行数
        self.buffer_lines = 20  # 前後のバッファ行数
        
    def pack(self, **kwargs):
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.container.grid(**kwargs)
    
    def set_logs(self, logs):
        """ログデータを設定（仮想レンダリング）"""
        self.all_logs = logs
        self.total_items = len(logs)
        self._update_visible_range(0)
    
    def _update_visible_range(self, scroll_position: float):
        """表示範囲を更新"""
        if self.total_items == 0:
            return
        
        # 開始インデックスを計算
        max_start = max(0, self.total_items - self.viewport_lines)
        start = int(scroll_position * max_start)
        start = max(0, start - self.buffer_lines)
        
        # 終了インデックスを計算
        end = min(self.total_items, start + self.viewport_lines + (self.buffer_lines * 2))
        
        # 範囲が変わった場合のみ更新
        if (start, end) != self.visible_range:
            self.visible_range = (start, end)
            self._render_visible_items()
    
    def _render_visible_items(self):
        """表示範囲のアイテムのみを描画"""
        # クリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        start, end = self.visible_range
        
        # 上部スペーサー
        if start > 0:
            self.tree.insert("", "end", iid="spacer_top", values=("", "", f"↑ {start:,} 行（上にスクロール）"), tags=["spacer"])
            self.tree.tag_configure("spacer", foreground="#666666")
        
        # ログを描画
        for i in range(start, end):
            if i >= len(self.all_logs):
                break
            log = self.all_logs[i]
            self.tree.insert("", "end", iid=f"log_{i}", values=(log.timestamp, log.level, log.content), tags=log.tags)
        
        # 下部スペーサー
        if end < self.total_items:
            remaining = self.total_items - end
            self.tree.insert("", "end", iid="spacer_bottom", values=("", "", f"↓ {remaining:,} 行（下にスクロール）"), tags=["spacer"])
    
    def _on_scroll(self, *args):
        """スクロールイベント"""
        self.tree.yview(*args)
        self.tree.after(30, self._delayed_scroll_update)  # 30ms後に更新
    
    def _delayed_scroll_update(self):
        """遅延スクロール更新"""
        scroll_pos = self.tree.yview()
        if scroll_pos:
            self._update_visible_range(scroll_pos[0])
    
    def _on_scrollbar_set(self, first, last):
        """スクロールバー位置設定"""
        self.scrollbar_y.set(first, last)
        try:
            self._update_visible_range(float(first))
        except:
            pass
    
    def _on_resize(self, event):
        """ウィンドウリサイズ時"""
        # ビューポート高さを再計算
        height = event.height
        self.viewport_lines = max(10, height // 20)  # 20pxで1行と仮定
        start, _ = self.visible_range
        self._update_visible_range(start / max(1, self.total_items - self.viewport_lines))
    
    # 委譲メソッド
    def tag_configure(self, tag, **kwargs):
        self.tree.tag_configure(tag, **kwargs)
    
    def selection(self):
        return self.tree.selection()
    
    def selection_set(self, items):
        self.tree.selection_set(items)
    
    def get_children(self, item=""):
        return self.tree.get_children(item)
    
    def item(self, item, **kwargs):
        return self.tree.item(item, **kwargs)
    
    def bind(self, event, callback):
        self.tree.bind(event, callback)
    
    def get_log_by_iid(self, iid):
        """iidからログデータを取得"""
        if iid.startswith("log_"):
            index = int(iid.split("_")[1])
            if 0 <= index < len(self.all_logs):
                return self.all_logs[index]
        return None
