"""
VRChat ログビューアー - UI構築

tkinterを使用したUI構築処理を管理
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Dict
from constants import (
    DARK_THEME,
    LOG_COLORS,
    SHORTCUTS_HELP,
    ABOUT_TEXT
)


class UIBuilder:
    """UI構築を担当するクラス"""
    
    @staticmethod
    def setup_menubar(root: tk.Tk, callbacks: Dict[str, Callable]) -> None:
        """メニューバーを構築"""
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(
            label="ログフォルダを選択",
            command=callbacks.get('select_folder')
        )
        file_menu.add_command(
            label="再読み込み",
            command=callbacks.get('reload'),
            accelerator="Ctrl+R / F5"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="終了",
            command=root.quit,
            accelerator="Alt+F4"
        )
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        view_menu.add_checkbutton(
            label="自動更新",
            variable=callbacks.get('auto_update_var'),
            command=callbacks.get('toggle_auto_update')
        )
        view_menu.add_separator()
        view_menu.add_checkbutton(
            label="長い行を折りたたむ",
            variable=callbacks.get('collapse_long_lines'),
            command=callbacks.get('apply_filter')
        )
        view_menu.add_checkbutton(
            label="連続するタグをグループ化",
            variable=callbacks.get('collapse_repeated_tags'),
            command=callbacks.get('apply_filter')
        )
        
        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(
            label="コピー",
            command=callbacks.get('copy'),
            accelerator="Ctrl+C"
        )
        edit_menu.add_command(
            label="すべて選択",
            command=callbacks.get('select_all'),
            accelerator="Ctrl+A"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="検索",
            command=callbacks.get('focus_search'),
            accelerator="Ctrl+F"
        )
        
        # デザインメニュー
        design_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="デザイン", menu=design_menu)
        design_menu.add_command(
            label="テーマを選択...",
            command=callbacks.get('select_theme')
        )
        design_menu.add_command(
            label="テーマをカスタマイズ...",
            command=callbacks.get('customize_theme')
        )
        design_menu.add_separator()
        design_menu.add_command(
            label="テーマをエクスポート...",
            command=callbacks.get('export_theme')
        )
        design_menu.add_command(
            label="テーマをインポート...",
            command=callbacks.get('import_theme')
        )
        
        # プラグインメニュー
        plugin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="プラグイン", menu=plugin_menu)
        plugin_menu.add_command(
            label="プラグイン管理...",
            command=callbacks.get('manage_plugins')
        )
        plugin_menu.add_separator()
        
        # プラグインから提供されるメニュー項目を追加
        if callbacks.get('get_plugin_menu_items'):
            plugin_items = callbacks.get('get_plugin_menu_items')()
            for label, command in plugin_items:
                plugin_menu.add_command(label=label, command=command)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(
            label="キーボードショートカット",
            command=callbacks.get('show_shortcuts')
        )
        help_menu.add_command(
            label="バージョン情報",
            command=callbacks.get('show_about')
        )
    
    @staticmethod
    def setup_top_frame(parent: tk.Widget, log_path: str, callbacks: Dict[str, Callable]) -> Dict[str, tk.Widget]:
        """トップフレームを構築"""
        widgets = {}
        
        top_frame = ttk.Frame(parent, padding="5")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="ログパス:").pack(side=tk.LEFT)
        
        path_label = ttk.Label(top_frame, text=str(log_path), foreground="blue")
        path_label.pack(side=tk.LEFT, padx=5)
        widgets['path_label'] = path_label
        
        ttk.Button(
            top_frame,
            text="📁 フォルダを開く",
            command=callbacks.get('open_folder')
        ).pack(side=tk.LEFT, padx=5)
        
        update_indicator = ttk.Label(top_frame, text="●", foreground="gray")
        update_indicator.pack(side=tk.RIGHT, padx=10)
        widgets['update_indicator'] = update_indicator
        
        return widgets
    
    @staticmethod
    def setup_filter_frame(parent: tk.Widget, callbacks: Dict[str, Callable]) -> Dict[str, tk.Widget]:
        """フィルターフレームを構築"""
        widgets = {}
        
        filter_frame = ttk.LabelFrame(parent, text="フィルター", padding="5")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # ログファイル選択
        ttk.Label(filter_frame, text="ログファイル:").grid(row=0, column=0, sticky=tk.W, padx=5)
        file_combo = ttk.Combobox(filter_frame, width=40, state="readonly")
        file_combo.grid(row=0, column=1, padx=5, pady=2)
        file_combo.bind("<<ComboboxSelected>>", callbacks.get('on_file_selected'))
        widgets['file_combo'] = file_combo
        
        # 検索
        ttk.Label(filter_frame, text="検索:").grid(row=1, column=0, sticky=tk.W, padx=5)
        search_var = tk.StringVar()
        search_var.trace('w', callbacks.get('on_search_changed'))
        search_entry = ttk.Entry(filter_frame, textvariable=search_var, width=40)
        search_entry.grid(row=1, column=1, padx=5, pady=2)
        widgets['search_var'] = search_var
        widgets['search_entry'] = search_entry
        
        # ログレベルフィルター
        ttk.Label(filter_frame, text="ログレベル:").grid(row=2, column=0, sticky=tk.W, padx=5)
        level_frame = ttk.Frame(filter_frame)
        level_frame.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        level_vars = {}
        for var_name, label in [
            ('show_debug', "Debug"),
            ('show_info', "Info"),
            ('show_warning', "Warning"),
            ('show_error', "Error"),
            ('show_other', "その他")
        ]:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                level_frame,
                text=label,
                variable=var,
                command=callbacks.get('apply_filter')
            ).pack(side=tk.LEFT, padx=5)
            level_vars[var_name] = var
        
        widgets.update(level_vars)
        
        return widgets
    
    @staticmethod
    def setup_log_tree(parent: tk.Widget, callbacks: Dict[str, Callable]) -> ttk.Treeview:
        """ログツリービューを構築"""
        log_container = ttk.Frame(parent)
        log_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(
            "Dark.Treeview",
            background=DARK_THEME['background'],
            foreground=DARK_THEME['foreground'],
            fieldbackground=DARK_THEME['fieldbackground'],
            borderwidth=0
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=DARK_THEME['heading_background'],
            foreground=DARK_THEME['heading_foreground'],
            borderwidth=1
        )
        style.map(
            'Dark.Treeview',
            background=[('selected', DARK_THEME['selected'])]
        )
        
        # Treeview作成
        log_tree = ttk.Treeview(
            log_container,
            columns=("time", "level", "content"),
            show="tree headings",
            selectmode="extended",
            style="Dark.Treeview"
        )
        
        log_tree.heading("time", text="時刻")
        log_tree.heading("level", text="レベル")
        log_tree.heading("content", text="内容")
        
        log_tree.column("#0", width=30)
        log_tree.column("time", width=150)
        log_tree.column("level", width=80)
        log_tree.column("content", width=800)
        
        # スクロールバー
        log_scroll_y = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=log_tree.yview)
        log_scroll_x = ttk.Scrollbar(log_container, orient=tk.HORIZONTAL, command=log_tree.xview)
        log_tree.configure(yscrollcommand=log_scroll_y.set, xscrollcommand=log_scroll_x.set)
        
        log_tree.grid(row=0, column=0, sticky="nsew")
        log_scroll_y.grid(row=0, column=1, sticky="ns")
        log_scroll_x.grid(row=1, column=0, sticky="ew")
        
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # イベントバインディング
        log_tree.bind("<Double-Button-1>", callbacks.get('on_log_double_click'))
        log_tree.bind("<Button-3>", callbacks.get('show_log_context_menu'))
        
        # タグ設定（色分け）
        for tag, color in LOG_COLORS.items():
            log_tree.tag_configure(tag, foreground=color)
        
        log_tree.tag_configure(
            "group_header",
            background=DARK_THEME['group_header_bg'],
            foreground=DARK_THEME['group_header_fg'],
            font=("Consolas", 9, "bold")
        )
        
        return log_tree
    
    @staticmethod
    def setup_message_panel(parent: tk.Widget, callbacks: Dict[str, Callable]) -> Dict[str, tk.Widget]:
        """メッセージパネルを構築"""
        widgets = {}
        
        msg_frame = ttk.LabelFrame(parent, text="グループメッセージ", padding="5")
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ツールバー
        toolbar_frame = ttk.Frame(msg_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            toolbar_frame,
            text="🔄 更新",
            command=callbacks.get('refresh_messages')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            toolbar_frame,
            text="グループ名編集",
            command=callbacks.get('edit_group_name')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            toolbar_frame,
            text="エクスポート",
            command=callbacks.get('export_messages')
        ).pack(side=tk.LEFT, padx=2)
        
        # グループ選択
        group_select_frame = ttk.Frame(msg_frame)
        group_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(group_select_frame, text="グループ:").pack(side=tk.LEFT)
        group_combo = ttk.Combobox(group_select_frame, width=30, state="readonly")
        group_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        group_combo.bind("<<ComboboxSelected>>", callbacks.get('on_group_selected'))
        widgets['group_combo'] = group_combo
        
        # メッセージ検索
        search_msg_frame = ttk.Frame(msg_frame)
        search_msg_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_msg_frame, text="検索:").pack(side=tk.LEFT)
        msg_search_var = tk.StringVar()
        msg_search_var.trace('w', callbacks.get('filter_messages'))
        msg_search_entry = ttk.Entry(search_msg_frame, textvariable=msg_search_var, width=30)
        msg_search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        widgets['msg_search_var'] = msg_search_var
        
        # メッセージリスト
        msg_list_frame = ttk.Frame(msg_frame)
        msg_list_frame.pack(fill=tk.BOTH, expand=True)
        
        msg_tree = ttk.Treeview(
            msg_list_frame,
            columns=("date", "message"),
            show="tree headings",
            selectmode="browse"
        )
        
        msg_tree.heading("#0", text="ID")
        msg_tree.heading("date", text="日時")
        msg_tree.heading("message", text="メッセージ")
        
        msg_tree.column("#0", width=0, stretch=False)
        msg_tree.column("date", width=150)
        msg_tree.column("message", width=300)
        
        msg_scrollbar = ttk.Scrollbar(msg_list_frame, orient=tk.VERTICAL, command=msg_tree.yview)
        msg_tree.configure(yscrollcommand=msg_scrollbar.set)
        
        msg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        msg_tree.bind("<<TreeviewSelect>>", callbacks.get('on_message_select'))
        widgets['msg_tree'] = msg_tree
        
        # メッセージ詳細（読み取り専用）
        detail_frame = ttk.LabelFrame(msg_frame, text="メッセージ詳細", padding="5")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        msg_detail = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            font=("Yu Gothic UI", 10),
            height=10,
            state=tk.DISABLED
        )
        msg_detail.pack(fill=tk.BOTH, expand=True)
        msg_detail.bind("<Button-3>", callbacks.get('show_message_context_menu'))
        widgets['msg_detail'] = msg_detail
        
        # 統計
        msg_stats_frame = ttk.Frame(msg_frame)
        msg_stats_frame.pack(fill=tk.X, pady=5)
        
        msg_stats_label = ttk.Label(msg_stats_frame, text="メッセージ: 0件")
        msg_stats_label.pack(side=tk.LEFT)
        widgets['msg_stats_label'] = msg_stats_label
        
        return widgets
    
    @staticmethod
    def setup_statusbar(parent: tk.Widget) -> ttk.Label:
        """ステータスバーを構築"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_label = ttk.Label(status_frame, text="準備完了", relief=tk.SUNKEN)
        status_label.pack(fill=tk.X, padx=2, pady=2)
        
        return status_label


class DialogUtils:
    """ダイアログ表示に関するユーティリティ"""
    
    @staticmethod
    def show_shortcuts() -> None:
        """キーボードショートカット一覧を表示"""
        from tkinter import messagebox
        messagebox.showinfo("キーボードショートカット", SHORTCUTS_HELP)
    
    @staticmethod
    def show_about() -> None:
        """バージョン情報を表示"""
        from tkinter import messagebox
        messagebox.showinfo("バージョン情報", ABOUT_TEXT)
