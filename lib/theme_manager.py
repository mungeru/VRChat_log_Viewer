"""
VRChat ログビューアー - テーマ管理システム

カスタムテーマの作成・管理・適用を行うモジュール
"""

import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict, field
import tkinter as tk
from tkinter import colorchooser, messagebox


@dataclass
class ColorScheme:
    """カラースキームのデータクラス"""
    # 名前と説明
    name: str = "ダークテーマ"
    description: str = "デフォルトのダークテーマ"
    author: str = "システム"
    
    # 背景色
    background: str = "#1e1e1e"
    foreground: str = "#d4d4d4"
    fieldbackground: str = "#1e1e1e"
    
    # ヘッダー
    heading_background: str = "#2d2d30"
    heading_foreground: str = "#cccccc"
    
    # 選択時
    selected: str = "#094771"
    
    # グループヘッダー
    group_header_bg: str = "#2d2d30"
    group_header_fg: str = "#cccccc"
    
    # ログレベル別の色
    log_debug: str = "#6a9955"
    log_info: str = "#4fc1ff"
    log_warning: str = "#dcdcaa"
    log_error: str = "#f48771"
    log_notification: str = "#9cdcfe"
    log_collapsed: str = "#858585"
    
    # ボタン・その他UI要素
    button_bg: str = "#0e639c"
    button_fg: str = "#ffffff"
    entry_bg: str = "#3c3c3c"
    entry_fg: str = "#cccccc"
    
    # 新規追加: 読みやすさ向上のための専用色
    text_area_bg: str = "#2d2d30"      # テキストエリア専用背景（少し明るめ）
    text_area_fg: str = "#e0e0e0"      # テキストエリア専用文字色（明るめ）
    input_field_bg: str = "#3c3c3c"    # 入力欄背景
    input_field_fg: str = "#ffffff"    # 入力欄文字色（白）
    status_bar_bg: str = "#007acc"     # ステータスバー背景（青）
    status_bar_fg: str = "#ffffff"     # ステータスバー文字色
    panel_border: str = "#404040"      # パネル区切り線
    hover_bg: str = "#2a2a2a"          # ホバー時の背景
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'ColorScheme':
        """辞書から作成"""
        # 古いテーマファイルとの互換性のため、デフォルト値を設定
        defaults = {
            'text_area_bg': '#2d2d30',
            'text_area_fg': '#e0e0e0',
            'input_field_bg': '#3c3c3c',
            'input_field_fg': '#ffffff',
            'status_bar_bg': '#007acc',
            'status_bar_fg': '#ffffff',
            'panel_border': '#404040',
            'hover_bg': '#2a2a2a'
        }
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
        return ColorScheme(**data)


class ThemeManager:
    """テーマ管理クラス"""
    
    def __init__(self):
        self.themes_dir = Path("themes")
        self.themes_dir.mkdir(exist_ok=True)
        
        self.current_theme: ColorScheme = ColorScheme()
        self.available_themes: Dict[str, ColorScheme] = {}
        
        # デフォルトテーマを作成
        self._create_default_themes()
        
        # 保存されたテーマを読み込み
        self.load_themes()
        
        # 最後に使用したテーマを読み込み
        self.load_last_used_theme()
    
    def _create_default_themes(self):
        """デフォルトテーマを作成"""
        # ダークテーマ（デフォルト）
        dark_theme = ColorScheme(
            name="ダークテーマ",
            description="目に優しいダークモード",
            author="システム"
        )
        
        # ライトテーマ
        light_theme = ColorScheme(
            name="ライトテーマ",
            description="明るいライトモード",
            author="システム",
            background="#ffffff",
            foreground="#000000",
            fieldbackground="#ffffff",
            heading_background="#f0f0f0",
            heading_foreground="#000000",
            selected="#0078d7",
            group_header_bg="#e0e0e0",
            group_header_fg="#000000",
            log_debug="#008000",
            log_info="#0000ff",
            log_warning="#ff8c00",
            log_error="#ff0000",
            log_notification="#800080",
            log_collapsed="#808080",
            button_bg="#0078d7",
            button_fg="#ffffff",
            entry_bg="#f0f0f0",
            entry_fg="#000000",
            # 新規追加
            text_area_bg="#f8f8f8",
            text_area_fg="#000000",
            input_field_bg="#ffffff",
            input_field_fg="#000000",
            status_bar_bg="#0078d7",
            status_bar_fg="#ffffff",
            panel_border="#cccccc",
            hover_bg="#e6e6e6"
        )
        
        # ブルーテーマ
        blue_theme = ColorScheme(
            name="ブルーテーマ",
            description="青を基調としたテーマ",
            author="システム",
            background="#0d1117",
            foreground="#c9d1d9",
            fieldbackground="#0d1117",
            heading_background="#161b22",
            heading_foreground="#58a6ff",
            selected="#1f6feb",
            group_header_bg="#161b22",
            group_header_fg="#58a6ff",
            log_debug="#7ee787",
            log_info="#58a6ff",
            log_warning="#d29922",
            log_error="#f85149",
            log_notification="#a371f7",
            log_collapsed="#6e7681",
            button_bg="#238636",
            button_fg="#ffffff",
            entry_bg="#161b22",
            entry_fg="#c9d1d9",
            # 新規追加
            text_area_bg="#161b22",
            text_area_fg="#e6edf3",
            input_field_bg="#0d1117",
            input_field_fg="#ffffff",
            status_bar_bg="#1f6feb",
            status_bar_fg="#ffffff",
            panel_border="#30363d",
            hover_bg="#1c2128"
        )
        
        # モノクロームテーマ
        mono_theme = ColorScheme(
            name="モノクローム",
            description="白黒のシンプルなテーマ",
            author="システム",
            background="#000000",
            foreground="#ffffff",
            fieldbackground="#000000",
            heading_background="#1a1a1a",
            heading_foreground="#ffffff",
            selected="#404040",
            group_header_bg="#1a1a1a",
            group_header_fg="#ffffff",
            log_debug="#b0b0b0",
            log_info="#ffffff",
            log_warning="#d0d0d0",
            log_error="#ffffff",
            log_notification="#c0c0c0",
            log_collapsed="#606060",
            button_bg="#404040",
            button_fg="#ffffff",
            entry_bg="#1a1a1a",
            entry_fg="#ffffff",
            # 新規追加
            text_area_bg="#1a1a1a",
            text_area_fg="#ffffff",
            input_field_bg="#2a2a2a",
            input_field_fg="#ffffff",
            status_bar_bg="#505050",
            status_bar_fg="#ffffff",
            panel_border="#333333",
            hover_bg="#2a2a2a"
        )
        
        # ノルディックテーマ
        nordic_theme = ColorScheme(
            name="ノルディック",
            description="北欧風の落ち着いたテーマ",
            author="システム",
            background="#2e3440",
            foreground="#d8dee9",
            fieldbackground="#2e3440",
            heading_background="#3b4252",
            heading_foreground="#88c0d0",
            selected="#5e81ac",
            group_header_bg="#3b4252",
            group_header_fg="#88c0d0",
            log_debug="#a3be8c",
            log_info="#81a1c1",
            log_warning="#ebcb8b",
            log_error="#bf616a",
            log_notification="#b48ead",
            log_collapsed="#4c566a",
            button_bg="#5e81ac",
            button_fg="#eceff4",
            entry_bg="#3b4252",
            entry_fg="#d8dee9",
            # 新規追加
            text_area_bg="#3b4252",
            text_area_fg="#eceff4",
            input_field_bg="#434c5e",
            input_field_fg="#eceff4",
            status_bar_bg="#5e81ac",
            status_bar_fg="#eceff4",
            panel_border="#4c566a",
            hover_bg="#434c5e"
        )
        
        # デフォルトテーマを保存
        for theme in [dark_theme, light_theme, blue_theme, mono_theme, nordic_theme]:
            self.available_themes[theme.name] = theme
            self.save_theme(theme)
    
    def load_themes(self):
        """保存されたテーマを読み込み"""
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    theme = ColorScheme.from_dict(data)
                    self.available_themes[theme.name] = theme
            except Exception as e:
                print(f"テーマ読み込みエラー ({theme_file.name}): {e}")
    
    def save_theme(self, theme: ColorScheme):
        """テーマを保存"""
        try:
            theme_file = self.themes_dir / f"{theme.name}.json"
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"テーマ保存エラー: {e}")
            raise
    
    def delete_theme(self, theme_name: str) -> bool:
        """テーマを削除"""
        # システムテーマは削除不可
        if theme_name in ["ダークテーマ", "ライトテーマ", "ブルーテーマ", "モノクローム", "ノルディック"]:
            messagebox.showerror("エラー", "システムテーマは削除できません")
            return False
        
        try:
            theme_file = self.themes_dir / f"{theme_name}.json"
            if theme_file.exists():
                theme_file.unlink()
            
            if theme_name in self.available_themes:
                del self.available_themes[theme_name]
            
            return True
        except Exception as e:
            print(f"テーマ削除エラー: {e}")
            return False
    
    def apply_theme(self, theme: ColorScheme):
        """テーマを適用"""
        self.current_theme = theme
        self.save_last_used_theme(theme.name)
    
    def save_last_used_theme(self, theme_name: str):
        """最後に使用したテーマを保存"""
        try:
            config_file = Path("theme_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"last_theme": theme_name}, f)
        except Exception as e:
            print(f"設定保存エラー: {e}")
    
    def load_last_used_theme(self):
        """最後に使用したテーマを読み込み"""
        try:
            config_file = Path("theme_config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get("last_theme", "ダークテーマ")
                    
                    if theme_name in self.available_themes:
                        self.current_theme = self.available_themes[theme_name]
                    else:
                        self.current_theme = self.available_themes["ダークテーマ"]
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            self.current_theme = self.available_themes["ダークテーマ"]
    
    def get_theme_names(self) -> list:
        """テーマ名のリストを取得"""
        return list(self.available_themes.keys())
    
    def get_theme(self, name: str) -> Optional[ColorScheme]:
        """名前でテーマを取得"""
        return self.available_themes.get(name)
    
    def create_custom_theme(self, base_theme: ColorScheme, new_name: str) -> ColorScheme:
        """カスタムテーマを作成"""
        custom_theme = ColorScheme(
            name=new_name,
            description=f"{base_theme.name}をベースにしたカスタムテーマ",
            author="ユーザー",
            background=base_theme.background,
            foreground=base_theme.foreground,
            fieldbackground=base_theme.fieldbackground,
            heading_background=base_theme.heading_background,
            heading_foreground=base_theme.heading_foreground,
            selected=base_theme.selected,
            group_header_bg=base_theme.group_header_bg,
            group_header_fg=base_theme.group_header_fg,
            log_debug=base_theme.log_debug,
            log_info=base_theme.log_info,
            log_warning=base_theme.log_warning,
            log_error=base_theme.log_error,
            log_notification=base_theme.log_notification,
            log_collapsed=base_theme.log_collapsed,
            button_bg=base_theme.button_bg,
            button_fg=base_theme.button_fg,
            entry_bg=base_theme.entry_bg,
            entry_fg=base_theme.entry_fg
        )
        
        self.available_themes[new_name] = custom_theme
        self.save_theme(custom_theme)
        
        return custom_theme


class ThemeEditor:
    """テーマエディタダイアログ"""
    
    def __init__(self, parent, theme_manager: ThemeManager, current_theme: ColorScheme, on_apply):
        self.parent = parent
        self.theme_manager = theme_manager
        self.editing_theme = ColorScheme(**asdict(current_theme))  # コピーを作成
        self.on_apply = on_apply
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"テーマエディタ - {self.editing_theme.name}")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        
        # 中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 300
        y = (self.dialog.winfo_screenheight() // 2) - 350
        self.dialog.geometry(f"600x700+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """UIを構築"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本情報
        info_frame = ttk.LabelFrame(scrollable_frame, text="テーマ情報", padding="10")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="テーマ名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_frame, text=self.editing_theme.name).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="作成者:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_frame, text=self.editing_theme.author).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 色設定
        self.color_buttons = {}
        
        # 背景・UI要素
        ui_frame = ttk.LabelFrame(scrollable_frame, text="背景・UI要素", padding="10")
        ui_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self._add_color_row(ui_frame, 0, "背景色", "background")
        self._add_color_row(ui_frame, 1, "文字色", "foreground")
        self._add_color_row(ui_frame, 2, "入力欄背景", "fieldbackground")
        self._add_color_row(ui_frame, 3, "ヘッダー背景", "heading_background")
        self._add_color_row(ui_frame, 4, "ヘッダー文字", "heading_foreground")
        self._add_color_row(ui_frame, 5, "選択時の色", "selected")
        
        # ログレベルの色
        log_frame = ttk.LabelFrame(scrollable_frame, text="ログレベルの色", padding="10")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self._add_color_row(log_frame, 0, "Debug", "log_debug")
        self._add_color_row(log_frame, 1, "Info", "log_info")
        self._add_color_row(log_frame, 2, "Warning", "log_warning")
        self._add_color_row(log_frame, 3, "Error", "log_error")
        self._add_color_row(log_frame, 4, "通知", "log_notification")
        self._add_color_row(log_frame, 5, "折りたたみ", "log_collapsed")
        
        # その他
        other_frame = ttk.LabelFrame(scrollable_frame, text="その他の要素", padding="10")
        other_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self._add_color_row(other_frame, 0, "グループヘッダー背景", "group_header_bg")
        self._add_color_row(other_frame, 1, "グループヘッダー文字", "group_header_fg")
        self._add_color_row(other_frame, 2, "ボタン背景", "button_bg")
        self._add_color_row(other_frame, 3, "ボタン文字", "button_fg")
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="プレビュー", command=self.preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="リセット", command=self.reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="新規保存", command=self.save_as).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="適用", command=self.apply).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _add_color_row(self, parent, row, label, attr_name):
        """色選択行を追加"""
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        
        color = getattr(self.editing_theme, attr_name)
        
        # 色のプレビュー
        color_preview = tk.Label(parent, bg=color, width=10, relief=tk.SUNKEN)
        color_preview.grid(row=row, column=1, padx=5, pady=2)
        
        # 色選択ボタン
        def choose_color():
            new_color = colorchooser.askcolor(color=color, title=f"{label}の色を選択")[1]
            if new_color:
                setattr(self.editing_theme, attr_name, new_color)
                color_preview.config(bg=new_color)
        
        color_button = ttk.Button(parent, text="色を選択", command=choose_color)
        color_button.grid(row=row, column=2, padx=5, pady=2)
        
        self.color_buttons[attr_name] = (color_preview, color_button)
    
    def preview(self):
        """プレビュー（一時的に適用）"""
        self.on_apply(self.editing_theme)
        messagebox.showinfo("プレビュー", "テーマを一時的に適用しました\n閉じると元に戻ります")
    
    def reset(self):
        """デフォルトに戻す"""
        if messagebox.askyesno("確認", "デフォルトの色に戻しますか？"):
            original = self.theme_manager.get_theme(self.editing_theme.name)
            if original:
                self.editing_theme = ColorScheme(**asdict(original))
                self.dialog.destroy()
                self.__init__(self.parent, self.theme_manager, self.editing_theme, self.on_apply)
    
    def save_as(self):
        """新しい名前で保存"""
        from tkinter import simpledialog
        
        new_name = simpledialog.askstring(
            "新規保存",
            "新しいテーマ名を入力してください:",
            initialvalue=f"{self.editing_theme.name}_カスタム"
        )
        
        if new_name:
            if new_name in self.theme_manager.available_themes:
                if not messagebox.askyesno("確認", f"テーマ「{new_name}」は既に存在します。\n上書きしますか？"):
                    return
            
            self.editing_theme.name = new_name
            self.editing_theme.author = "ユーザー"
            self.theme_manager.save_theme(self.editing_theme)
            self.theme_manager.available_themes[new_name] = self.editing_theme
            messagebox.showinfo("成功", f"テーマ「{new_name}」を保存しました")
            self.dialog.destroy()
    
    def apply(self):
        """適用して閉じる"""
        self.on_apply(self.editing_theme)
        self.dialog.destroy()
