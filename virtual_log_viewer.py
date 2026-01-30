"""
VRChat ログビューアー - 仮想スクロール対応ログビューア

VS Codeのような仮想スクロールを実装し、大量のログでも高速に表示
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import List, Callable, Optional, Tuple
from models import LogInfo
from constants import DARK_THEME, LOG_COLORS


class VirtualLogViewer(tk.Frame):
    """仮想スクロール対応のログビューアーウィジェット"""
    
    def __init__(
        self, 
        parent, 
        on_double_click: Optional[Callable] = None,
        on_right_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.logs: List[LogInfo] = []  # 全ログデータ
        self.visible_logs: List[Tuple[int, LogInfo]] = []  # 表示中のログ（インデックス付き）
        self.grouped_indices: set = set()  # グループ化されたインデックス
        self.expanded_groups: set = set()  # 展開されているグループ
        
        # コールバック
        self.on_double_click = on_double_click
        self.on_right_click = on_right_click
        
        # スクロール関連
        self.first_visible_line = 0
        self.line_height = 20  # 1行の高さ（ピクセル）
        self.visible_lines = 0  # 表示可能な行数
        
        # フォント設定
        self.log_font = tkfont.Font(family="Consolas", size=9)
        self.line_height = self.log_font.metrics('linespace') + 2
        
        # UI構築
        self._setup_ui()
    
    def _setup_ui(self):
        """UIを構築"""
        # メインコンテナ
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Canvas（スクロール可能な描画領域）
        self.canvas = tk.Canvas(
            self,
            bg=DARK_THEME['background'],
            highlightthickness=0,
            borderwidth=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # スクロールバー
        self.v_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self._on_scroll
        )
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.h_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )
        
        # イベントバインディング
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)  # Linux
        self.canvas.bind('<Button-5>', self._on_mousewheel)  # Linux
        self.canvas.bind('<Double-Button-1>', self._on_canvas_double_click)
        self.canvas.bind('<Button-3>', self._on_canvas_right_click)
        
        # キーボードスクロール
        self.canvas.bind('<Up>', lambda e: self._scroll_by_lines(-1))
        self.canvas.bind('<Down>', lambda e: self._scroll_by_lines(1))
        self.canvas.bind('<Prior>', lambda e: self._scroll_by_lines(-10))  # PageUp
        self.canvas.bind('<Next>', lambda e: self._scroll_by_lines(10))    # PageDown
        self.canvas.bind('<Home>', lambda e: self._scroll_to(0))
        self.canvas.bind('<End>', lambda e: self._scroll_to(len(self.logs) - 1))
        
        self.canvas.focus_set()
    
    def set_logs(self, logs: List[LogInfo]):
        """ログデータを設定"""
        self.logs = logs
        self.first_visible_line = 0
        self.grouped_indices.clear()
        self.expanded_groups.clear()
        self._update_scrollregion()
        self._render_visible_logs()
    
    def clear(self):
        """ログをクリア"""
        self.logs = []
        self.visible_logs = []
        self.grouped_indices.clear()
        self.expanded_groups.clear()
        self.canvas.delete("all")
        self._update_scrollregion()
    
    def add_log(self, log: LogInfo):
        """ログを追加（増分更新）"""
        self.logs.append(log)
        self._update_scrollregion()
        
        # 最下部にいる場合は自動スクロール
        if self.first_visible_line + self.visible_lines >= len(self.logs) - 1:
            self._scroll_to(len(self.logs) - 1)
        else:
            self._render_visible_logs()
    
    def mark_as_group(self, start_idx: int, end_idx: int):
        """指定範囲をグループとしてマーク"""
        for i in range(start_idx, end_idx + 1):
            self.grouped_indices.add(i)
    
    def toggle_group(self, group_start_idx: int):
        """グループの展開/折りたたみを切り替え"""
        if group_start_idx in self.expanded_groups:
            self.expanded_groups.remove(group_start_idx)
        else:
            self.expanded_groups.add(group_start_idx)
        self._render_visible_logs()
    
    def _update_scrollregion(self):
        """スクロール領域を更新"""
        total_height = len(self.logs) * self.line_height
        self.canvas.configure(scrollregion=(0, 0, 3000, total_height))
        
        # スクロールバーの表示比率を更新
        if len(self.logs) > 0:
            visible_ratio = self.visible_lines / len(self.logs)
            if visible_ratio >= 1.0:
                self.v_scrollbar.set(0, 1)
            else:
                first_ratio = self.first_visible_line / len(self.logs)
                last_ratio = (self.first_visible_line + self.visible_lines) / len(self.logs)
                self.v_scrollbar.set(first_ratio, last_ratio)
    
    def _on_canvas_configure(self, event):
        """キャンバスサイズ変更時の処理"""
        self.visible_lines = max(1, event.height // self.line_height)
        self._render_visible_logs()
    
    def _on_scroll(self, *args):
        """スクロールバー操作時の処理"""
        if args[0] == 'moveto':
            # スクロールバーをドラッグ
            ratio = float(args[1])
            new_first = int(ratio * len(self.logs))
            self.first_visible_line = max(0, min(new_first, len(self.logs) - self.visible_lines))
        elif args[0] == 'scroll':
            # スクロールバーの矢印クリック
            delta = int(args[1])
            unit = args[2]
            if unit == 'units':
                self._scroll_by_lines(delta)
            elif unit == 'pages':
                self._scroll_by_lines(delta * self.visible_lines)
        
        self._render_visible_logs()
    
    def _on_mousewheel(self, event):
        """マウスホイール操作時の処理"""
        if event.num == 4 or event.delta > 0:
            # 上スクロール
            self._scroll_by_lines(-3)
        elif event.num == 5 or event.delta < 0:
            # 下スクロール
            self._scroll_by_lines(3)
    
    def _scroll_by_lines(self, delta: int):
        """指定行数だけスクロール"""
        new_first = self.first_visible_line + delta
        self.first_visible_line = max(0, min(new_first, max(0, len(self.logs) - self.visible_lines)))
        self._update_scrollregion()
        self._render_visible_logs()
    
    def _scroll_to(self, line_index: int):
        """指定行までスクロール"""
        self.first_visible_line = max(0, min(line_index, max(0, len(self.logs) - self.visible_lines)))
        self._update_scrollregion()
        self._render_visible_logs()
    
    def _render_visible_logs(self):
        """表示中の行のみをレンダリング（仮想スクロール）"""
        self.canvas.delete("all")
        
        if not self.logs:
            return
        
        # 表示範囲を計算
        start_idx = self.first_visible_line
        end_idx = min(start_idx + self.visible_lines + 1, len(self.logs))
        
        # 表示する行をレンダリング
        y_offset = 0
        for idx in range(start_idx, end_idx):
            if idx >= len(self.logs):
                break
            
            log = self.logs[idx]
            self._render_log_line(log, idx, y_offset)
            y_offset += self.line_height
        
        self.visible_logs = [(i, self.logs[i]) for i in range(start_idx, end_idx)]
    
    def _render_log_line(self, log: LogInfo, index: int, y_pos: int):
        """1行のログをレンダリング"""
        x_start = 5
        
        # グループ化された行の場合
        if index in self.grouped_indices:
            # グループヘッダーの場合
            if index == min([i for i in self.grouped_indices if i >= index], default=index):
                self._render_group_header(log, index, y_pos)
                return
            # グループの子要素で折りたたまれている場合はスキップ
            elif index not in self.expanded_groups:
                return
        
        # タイムスタンプ
        if log.timestamp:
            self.canvas.create_text(
                x_start, y_pos + 2,
                text=log.timestamp,
                anchor='nw',
                font=self.log_font,
                fill='#858585',
                tags=f'line_{index}'
            )
            x_start += 160
        
        # レベル
        if log.level:
            level_color = self._get_level_color(log.tags)
            self.canvas.create_text(
                x_start, y_pos + 2,
                text=log.level,
                anchor='nw',
                font=self.log_font,
                fill=level_color,
                tags=f'line_{index}'
            )
            x_start += 80
        
        # 内容
        content_color = self._get_level_color(log.tags)
        self.canvas.create_text(
            x_start, y_pos + 2,
            text=log.content[:200] if len(log.content) > 200 else log.content,  # 長すぎる場合は切り詰め
            anchor='nw',
            font=self.log_font,
            fill=content_color,
            tags=f'line_{index}'
        )
    
    def _render_group_header(self, log: LogInfo, index: int, y_pos: int):
        """グループヘッダーをレンダリング"""
        # 背景
        self.canvas.create_rectangle(
            0, y_pos,
            3000, y_pos + self.line_height,
            fill=DARK_THEME['group_header_bg'],
            outline='',
            tags=f'group_{index}'
        )
        
        # 展開/折りたたみアイコン
        icon = "▼" if index in self.expanded_groups else "▶"
        self.canvas.create_text(
            5, y_pos + 2,
            text=icon,
            anchor='nw',
            font=self.log_font,
            fill=DARK_THEME['group_header_fg'],
            tags=f'group_{index}'
        )
        
        # グループ名
        self.canvas.create_text(
            25, y_pos + 2,
            text=f"📁 {log.content}",
            anchor='nw',
            font=(self.log_font.actual()['family'], self.log_font.actual()['size'], 'bold'),
            fill=DARK_THEME['group_header_fg'],
            tags=f'group_{index}'
        )
    
    def _get_level_color(self, tags: List[str]) -> str:
        """ログレベルに応じた色を取得"""
        if not tags:
            return DARK_THEME['foreground']
        
        for tag in tags:
            if tag in LOG_COLORS:
                return LOG_COLORS[tag]
        
        return DARK_THEME['foreground']
    
    def _on_canvas_double_click(self, event):
        """ダブルクリック時の処理"""
        line_idx = self.first_visible_line + (event.y // self.line_height)
        
        if 0 <= line_idx < len(self.logs):
            # グループヘッダーの場合は展開/折りたたみ
            if line_idx in self.grouped_indices:
                self.toggle_group(line_idx)
            elif self.on_double_click:
                self.on_double_click(line_idx, self.logs[line_idx])
    
    def _on_canvas_right_click(self, event):
        """右クリック時の処理"""
        line_idx = self.first_visible_line + (event.y // self.line_height)
        
        if 0 <= line_idx < len(self.logs) and self.on_right_click:
            self.on_right_click(event, line_idx, self.logs[line_idx])
    
    def get_selected_logs(self) -> List[LogInfo]:
        """選択されているログを取得（全選択用）"""
        return self.logs.copy()
    
    def search_and_highlight(self, query: str):
        """検索してハイライト表示（今後の拡張用）"""
        # TODO: 検索機能の実装
        pass


class VirtualLogViewerWithHeader(tk.Frame):
    """ヘッダー付き仮想スクロールログビューア"""
    
    def __init__(
        self,
        parent,
        on_double_click: Optional[Callable] = None,
        on_right_click: Optional[Callable] = None
    ):
        super().__init__(parent)
        
        # ヘッダーフレーム
        header_frame = tk.Frame(self, bg=DARK_THEME['heading_background'], height=25)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        # ヘッダーラベル
        headers = [
            ("時刻", 160),
            ("レベル", 80),
            ("内容", 800)
        ]
        
        x_pos = 35  # インデント分のオフセット
        for label, width in headers:
            lbl = tk.Label(
                header_frame,
                text=label,
                bg=DARK_THEME['heading_background'],
                fg=DARK_THEME['heading_foreground'],
                font=("Consolas", 9, "bold"),
                anchor='w'
            )
            lbl.place(x=x_pos, y=2, width=width)
            x_pos += width
        
        # ログビューア（コールバックを渡す）
        self.log_viewer = VirtualLogViewer(
            self,
            on_double_click=on_double_click,
            on_right_click=on_right_click
        )
        self.log_viewer.pack(fill=tk.BOTH, expand=True)
    
    def __getattr__(self, name):
        """VirtualLogViewerのメソッドに委譲"""
        return getattr(self.log_viewer, name)
