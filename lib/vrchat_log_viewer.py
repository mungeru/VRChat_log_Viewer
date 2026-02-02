"""
VRChat ログビューアー (モジュール化版)

メインアプリケーションクラス
各機能を別モジュールから読み込んで使用
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from pathlib import Path
from datetime import datetime
import json
import subprocess
import platform
import re
from typing import List, Dict, Optional

# 自作モジュールのインポート
from constants import (
    DEFAULT_LOG_PATH_WINDOWS,
    GROUP_NAMES_FILE,
    WINDOW_TITLE,
    WINDOW_GEOMETRY,
    AUTO_UPDATE_INTERVAL,
    LARGE_FILE_THRESHOLD_MB,
    BATCH_SIZE,
    GROUP_COLLAPSE_THRESHOLD,
    RESIZE_DEBOUNCE_DELAY,
    SHORTCUTS,
    ERROR_MESSAGES,
    STATUS_MESSAGES
)
from models import LogInfo, NotificationData, GroupInfo
from utils import (
    FileUtils,
    LogParser,
    NotificationParser,
    GroupUtils,
    ExportUtils
)
from ui_builder import UIBuilder, DialogUtils
from async_loader import AsyncLogLoader
from progress_dialog import ProgressDialog
from theme_manager import ThemeManager, ThemeEditor, ColorScheme
from plugin_manager import PluginManager, PluginManagerDialog


class VRChatLogViewer:
    """VRChat ログビューアーのメインクラス"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        
        # 状態管理
        self.log_path = DEFAULT_LOG_PATH_WINDOWS
        self.current_logs: List[str] = []
        self.notifications: List[NotificationData] = []
        self.groups: Dict[str, dict] = {}
        self.current_displayed_messages: List[NotificationData] = []
        
        # 設定
        self.auto_update = False
        self.last_file_size = 0
        self.current_log_file: Optional[Path] = None
        
        # デバウンス用
        self.resize_timer: Optional[str] = None
        self.pending_resize = False
        
        # UI設定変数
        self.collapse_long_lines = tk.BooleanVar(value=True)
        self.collapse_repeated_tags = tk.BooleanVar(value=True)
        self.auto_update_var = tk.BooleanVar(value=False)
        
        # グループ名管理
        self.group_names: Dict[str, str] = {}
        self.load_group_names()
        
        # 非同期ローダー
        self.async_loader = AsyncLogLoader()
        self.progress_dialog: Optional[ProgressDialog] = None
        
        # UIウィジェット参照
        self.widgets = {}
        
        # テーママネージャー
        self.theme_manager = ThemeManager()
        
        # プラグインマネージャー
        self.plugin_manager = PluginManager()
        
        # UI構築
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # テーマを適用
        self.apply_current_theme()
        
        # プラグインを初期化
        self.initialize_plugins()
        
        # 初期ロード
        self.load_logs()
    
    # ==================== 初期化・設定 ====================
    
    def load_group_names(self) -> None:
        """保存されたグループ名を読み込み"""
        # スクリプトと同じディレクトリに保存
        script_dir = Path(__file__).parent
        group_names_file = script_dir / "vrchat_group_names.json"
        self.group_names_file = group_names_file
        
        if group_names_file.exists():
            try:
                with open(group_names_file, 'r', encoding='utf-8') as f:
                    self.group_names = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"グループ名の読み込みエラー: {e}")
                self.group_names = {}
    
    def save_group_names(self) -> None:
        """グループ名を保存"""
        try:
            with open(self.group_names_file, 'w', encoding='utf-8') as f:
                json.dump(self.group_names, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"グループ名の保存エラー: {e}")
            messagebox.showerror("保存エラー", f"グループ名の保存に失敗しました:\n{e}")
    
    def setup_keyboard_shortcuts(self) -> None:
        """キーボードショートカットを設定"""
        self.root.bind(SHORTCUTS['search'], lambda e: self.widgets['search_entry'].focus_set())
        self.root.bind(SHORTCUTS['reload'], lambda e: self.load_logs())
        self.root.bind(SHORTCUTS['reload_alt'], lambda e: self.load_logs())
        self.root.bind(SHORTCUTS['copy'], self.copy_selected_logs)
        self.widgets['log_tree'].bind(SHORTCUTS['select_all'], self.select_all_logs)
        self.root.bind(SHORTCUTS['clear_search'], lambda e: self.widgets['search_var'].set(''))
        
        # ウィンドウリサイズイベント（デバウンス付き）
        self.root.bind('<Configure>', self.on_window_resize)
    
    def setup_ui(self) -> None:
        """UIを構築"""
        # コールバック辞書を作成
        callbacks = self._create_callbacks()
        
        # メニューバー
        UIBuilder.setup_menubar(self.root, callbacks)
        
        # トップフレーム
        top_widgets = UIBuilder.setup_top_frame(self.root, str(self.log_path), callbacks)
        self.widgets.update(top_widgets)
        
        # メインパネル
        main_paned = tk.ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左パネル - ログ表示
        left_frame = tk.ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=3)
        
        # フィルターフレーム
        filter_widgets = UIBuilder.setup_filter_frame(left_frame, callbacks)
        self.widgets.update(filter_widgets)
        
        # 統計情報
        stats_frame = tk.ttk.LabelFrame(left_frame, text="統計", padding="5")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        stats_label = tk.ttk.Label(stats_frame, text="ログ: 0行")
        stats_label.pack(side=tk.LEFT, padx=10)
        self.widgets['stats_label'] = stats_label
        
        # ログツリー
        log_tree = UIBuilder.setup_log_tree(left_frame, callbacks)
        self.widgets['log_tree'] = log_tree
        
        # 右パネル - グループメッセージ
        right_frame = tk.ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        message_widgets = UIBuilder.setup_message_panel(right_frame, callbacks)
        self.widgets.update(message_widgets)
        
        # ステータスバー
        status_label = UIBuilder.setup_statusbar(self.root)
        self.widgets['status_label'] = status_label
    
    def _create_callbacks(self) -> Dict:
        """コールバック辞書を作成"""
        return {
            'select_folder': self.select_log_folder,
            'reload': self.load_logs,
            'open_folder': self.open_log_folder,
            'auto_update_var': self.auto_update_var,
            'toggle_auto_update': self.toggle_auto_update,
            'collapse_long_lines': self.collapse_long_lines,
            'collapse_repeated_tags': self.collapse_repeated_tags,
            'apply_filter': self.apply_filter,
            'copy': self.copy_selected_logs,
            'select_all': self.select_all_logs,
            'focus_search': lambda: self.widgets.get('search_entry', tk.Entry()).focus_set() if 'search_entry' in self.widgets else None,
            'show_shortcuts': DialogUtils.show_shortcuts,
            'show_about': DialogUtils.show_about,
            'on_file_selected': self.on_file_selected,
            'on_search_changed': self.apply_filter,
            'on_log_double_click': self.on_log_double_click,
            'show_log_context_menu': self.show_log_context_menu,
            'refresh_messages': self.refresh_messages,
            'edit_group_name': self.edit_group_name,
            'export_messages': self.export_messages,
            'on_group_selected': self.on_group_selected,
            'filter_messages': self.filter_messages,
            'on_message_select': self.on_message_select,
            'show_message_context_menu': self.show_message_context_menu,
            # テーマ関連
            'select_theme': self.select_theme,
            'customize_theme': self.customize_theme,
            'export_theme': self.export_theme,
            'import_theme': self.import_theme,
            # プラグイン関連
            'manage_plugins': self.manage_plugins,
            'get_plugin_menu_items': self.get_plugin_menu_items,
        }
    
    # ==================== イベントハンドラー ====================
    
    def on_window_resize(self, event: tk.Event) -> None:
        """ウィンドウリサイズイベント（デバウンス処理）"""
        # ウィンドウ自体のリサイズイベントのみ処理
        if event.widget != self.root:
            return
        
        # 既存のタイマーをキャンセル
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        
        # 新しいタイマーを設定
        self.resize_timer = self.root.after(
            RESIZE_DEBOUNCE_DELAY,
            self.handle_resize_complete
        )
    
    def handle_resize_complete(self) -> None:
        """リサイズ完了時の処理"""
        self.resize_timer = None
        # 必要に応じてUIの再描画などを行う
        # 現在の実装では特に追加処理は不要だが、
        # 将来的にカスタムレイアウト調整などを追加できる
        self.root.update_idletasks()
    
    def on_log_double_click(self, event: tk.Event) -> None:
        """ログ行のダブルクリックで展開/折りたたみ"""
        log_tree = self.widgets['log_tree']
        if not log_tree.selection():
            return
        
        item = log_tree.selection()[0]
        if log_tree.get_children(item):
            current_state = log_tree.item(item, "open")
            log_tree.item(item, open=not current_state)
    
    def show_log_context_menu(self, event: tk.Event) -> None:
        """ログの右クリックメニューを表示"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="コピー", command=self.copy_selected_logs)
        menu.add_command(label="すべて選択", command=self.select_all_logs)
        menu.add_separator()
        menu.add_command(label="詳細を表示", command=self.show_log_details)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def show_message_context_menu(self, event: tk.Event) -> None:
        """メッセージ詳細の右クリックメニューを表示"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="コピー", command=self.copy_message_detail)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def copy_selected_logs(self, event: Optional[tk.Event] = None) -> None:
        """選択されたログをクリップボードにコピー"""
        log_tree = self.widgets['log_tree']
        selected_items = log_tree.selection()
        
        if not selected_items:
            return
        
        copied_text = []
        for item in selected_items:
            values = log_tree.item(item, "values")
            if values:
                log_line = f"{values[0]}\t{values[1]}\t{values[2]}"
                copied_text.append(log_line)
        
        if copied_text:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(copied_text))
            self.widgets['status_label'].config(
                text=STATUS_MESSAGES['copied'].format(count=len(copied_text))
            )
            self.root.after(2000, lambda: self.widgets['status_label'].config(
                text=STATUS_MESSAGES['ready']
            ))
    
    def copy_message_detail(self) -> None:
        """メッセージ詳細をクリップボードにコピー"""
        msg_detail = self.widgets['msg_detail']
        try:
            msg_detail.config(state=tk.NORMAL)
            text = msg_detail.get(1.0, tk.END).strip()
            msg_detail.config(state=tk.DISABLED)
            
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.widgets['status_label'].config(text=STATUS_MESSAGES['message_copied'])
                self.root.after(2000, lambda: self.widgets['status_label'].config(
                    text=STATUS_MESSAGES['ready']
                ))
        except Exception as e:
            print(f"コピーエラー: {e}")
    
    def select_all_logs(self, event: Optional[tk.Event] = None) -> None:
        """すべてのログを選択"""
        log_tree = self.widgets['log_tree']
        all_items = log_tree.get_children()
        log_tree.selection_set(all_items)
        return "break"
    
    def show_log_details(self) -> None:
        """選択されたログの詳細を表示"""
        log_tree = self.widgets['log_tree']
        selected_items = log_tree.selection()
        
        if not selected_items:
            return
        
        details = []
        for item in selected_items:
            values = log_tree.item(item, "values")
            if values:
                details.append(f"時刻: {values[0]}\nレベル: {values[1]}\n内容: {values[2]}\n")
        
        if details:
            messagebox.showinfo("ログ詳細", "\n".join(details))
    
    def on_file_selected(self, event: tk.Event) -> None:
        """ファイルコンボボックスで選択された時"""
        file_combo = self.widgets['file_combo']
        selection = file_combo.current()
        if selection >= 0:
            log_files = FileUtils.get_sorted_log_files(self.log_path)
            if selection < len(log_files):
                self.load_log_file(log_files[selection])
    
    def on_group_selected(self, event: tk.Event) -> None:
        """グループが選択された時"""
        self.update_message_list()
    
    def on_message_select(self, event: tk.Event) -> None:
        """メッセージが選択された時"""
        msg_tree = self.widgets['msg_tree']
        msg_detail = self.widgets['msg_detail']
        
        selection = msg_tree.selection()
        if selection and hasattr(self, 'current_displayed_messages'):
            try:
                item_id = int(selection[0])
                if 0 <= item_id < len(self.current_displayed_messages):
                    notif = self.current_displayed_messages[item_id]
                    
                    msg_detail.config(state=tk.NORMAL)
                    msg_detail.delete(1.0, tk.END)
                    
                    detail_text = f"受信日時: {notif.date}\n"
                    detail_text += f"作成日時: {notif.created_at}\n"
                    detail_text += f"グループ: {self.groups[notif.group_id]['name']}\n"
                    detail_text += f"ID: {notif.id}\n"
                    detail_text += f"\nメッセージ:\n{notif.message}"
                    
                    msg_detail.insert(1.0, detail_text)
                    msg_detail.config(state=tk.DISABLED)
            except (ValueError, IndexError, KeyError) as e:
                print(f"メッセージ選択エラー: {e}")
    
    # ==================== ファイル操作 ====================
    
    def open_log_folder(self) -> None:
        """エクスプローラーでログフォルダを開く"""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', str(self.log_path)])
            elif system == "Darwin":
                subprocess.run(['open', str(self.log_path)])
            else:
                subprocess.run(['xdg-open', str(self.log_path)])
        except Exception as e:
            messagebox.showerror(
                "エラー",
                ERROR_MESSAGES['folder_open_error'].format(error=e)
            )
    
    def select_log_folder(self) -> None:
        """ログフォルダを選択"""
        folder = filedialog.askdirectory(
            title="VRChatログフォルダを選択",
            initialdir=str(self.log_path)
        )
        if folder:
            self.log_path = Path(folder)
            self.widgets['path_label'].config(text=str(self.log_path))
            self.load_logs()
    
    def load_logs(self) -> None:
        """ログファイルのリストを読み込み"""
        status_label = self.widgets['status_label']
        
        try:
            if not self.log_path.exists():
                messagebox.showerror(
                    "ログフォルダが見つかりません",
                    ERROR_MESSAGES['folder_not_found'].format(path=self.log_path)
                )
                status_label.config(text=STATUS_MESSAGES['no_folder'])
                return
            
            status_label.config(text=STATUS_MESSAGES['searching'])
            self.root.update()
            
            log_files = FileUtils.get_sorted_log_files(self.log_path)
            
            if not log_files:
                messagebox.showwarning(
                    "ログファイルが見つかりません",
                    ERROR_MESSAGES['no_log_files'].format(path=self.log_path)
                )
                status_label.config(text=STATUS_MESSAGES['no_files'])
                return
            
            file_list = []
            for log_file in log_files:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                file_list.append(f"{log_file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            
            self.widgets['file_combo']['values'] = file_list
            self.widgets['file_combo'].current(0)
            
            self.load_log_file(log_files[0])
            
            status_label.config(
                text=STATUS_MESSAGES['detected'].format(count=len(log_files))
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror(
                "ログ読み込みエラー",
                f"ログファイルの読み込み中にエラーが発生しました:\n\n{e}\n\n"
                f"詳細:\n{error_details[:300]}"
            )
            status_label.config(text=STATUS_MESSAGES['error'].format(error=str(e)[:50]))
            print(f"エラー詳細:\n{error_details}")
    
    def load_log_file(self, log_file: Path, append: bool = False) -> None:
        """個別のログファイルを読み込み（非同期対応）"""
        status_label = self.widgets['status_label']
        
        # すでに読み込み中の場合はキャンセル
        if self.async_loader.is_loading():
            self.async_loader.cancel()
            if self.progress_dialog:
                self.progress_dialog.close()
        
        try:
            self.current_log_file = log_file
            file_size = log_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # 小さいファイル（1MB未満）は同期読み込み
            if file_size_mb < 1.0 and not append:
                self._load_log_file_sync(log_file, append)
                return
            
            # 大きなファイルの場合は非同期読み込み
            if not append:
                # プログレスダイアログを表示
                self.progress_dialog = ProgressDialog(
                    self.root,
                    f"ログ読み込み中... ({file_size_mb:.1f}MB)"
                )
                self.progress_dialog.set_on_cancel(self.async_loader.cancel)
                
                def on_progress(message: str, percentage: int):
                    """進捗コールバック（メインスレッドで実行）"""
                    self.root.after(0, lambda: self._update_progress(message, percentage))
                
                def on_complete(lines: List[str], notifications: List[NotificationData]):
                    """完了コールバック（メインスレッドで実行）"""
                    self.root.after(0, lambda: self._on_load_complete(
                        log_file, lines, notifications, append
                    ))
                
                def on_error(error: Exception):
                    """エラーコールバック（メインスレッドで実行）"""
                    self.root.after(0, lambda: self._on_load_error(error))
                
                # 非同期読み込み開始
                self.async_loader.load_file_async(
                    log_file,
                    on_progress,
                    on_complete,
                    on_error
                )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror(
                "予期しないエラー",
                f"ファイルの読み込み中に予期しないエラーが発生しました:\n\n{e}\n\n"
                f"詳細:\n{error_details[:500]}"
            )
            status_label.config(text=STATUS_MESSAGES['error'].format(error=str(e)[:50]))
            print(f"エラー詳細:\n{error_details}")
    
    def _load_log_file_sync(self, log_file: Path, append: bool = False) -> None:
        """ログファイルを同期的に読み込み（小さいファイル用）"""
        status_label = self.widgets['status_label']
        
        try:
            if not append:
                status_label.config(
                    text=STATUS_MESSAGES['loading'].format(filename=log_file.name)
                )
                self.root.update()
            
            # ファイル読み込み
            content = FileUtils.read_file_with_encoding(log_file)
            
            if not append:
                status_label.config(text=STATUS_MESSAGES['parsing'])
                self.root.update()
            
            lines = content.splitlines(keepends=True)
            self.last_file_size = log_file.stat().st_size
            
            if not append:
                self.current_logs = lines
            else:
                new_lines = lines[len(self.current_logs):]
                self.current_logs.extend(new_lines)
            
            if not append:
                status_label.config(text=STATUS_MESSAGES['extracting'])
                self.root.update()
            
            # 通知の解析
            new_content = content if not append else '\n'.join(lines[len(self.current_logs):])
            new_notifications = NotificationParser.parse_notifications(new_content)
            
            if not append:
                self.notifications = new_notifications
            else:
                self.notifications.extend(new_notifications)
            
            # グループ整理
            self.groups = GroupUtils.organize_notifications_by_group(
                self.notifications,
                self.group_names
            )
            
            if not append:
                status_label.config(text=STATUS_MESSAGES['displaying'])
                self.root.update()
                self.apply_filter()
            
            self.update_group_list()
            if not append:
                self.update_message_list()
            
            msg_count = len(self.notifications)
            status_label.config(
                text=STATUS_MESSAGES['completed'].format(
                    filename=log_file.name,
                    lines=len(self.current_logs),
                    messages=msg_count
                )
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror(
                "予期しないエラー",
                f"ファイルの読み込み中に予期しないエラーが発生しました:\n\n{e}\n\n"
                f"詳細:\n{error_details[:500]}"
            )
            status_label.config(text=STATUS_MESSAGES['error'].format(error=str(e)[:50]))
            print(f"エラー詳細:\n{error_details}")
    
    def _update_progress(self, message: str, percentage: int):
        """プログレス更新（メインスレッドで実行）"""
        if self.progress_dialog and not self.progress_dialog.cancelled:
            try:
                self.progress_dialog.set_progress(message, percentage)
                self.root.update_idletasks()  # UIを強制更新
                self.root.update()  # イベントを処理
            except:
                pass  # ダイアログが閉じられた場合
    
    def _on_load_complete(
        self,
        log_file: Path,
        lines: List[str],
        notifications: List[NotificationData],
        append: bool
    ):
        """読み込み完了時の処理"""
        status_label = self.widgets['status_label']
        
        # プログレスダイアログを閉じる
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # データを設定
        self.last_file_size = log_file.stat().st_size
        
        if not append:
            self.current_logs = lines
            self.notifications = notifications
        else:
            new_lines = lines[len(self.current_logs):]
            self.current_logs.extend(new_lines)
            self.notifications.extend(notifications)
        
        # グループ整理
        self.groups = GroupUtils.organize_notifications_by_group(
            self.notifications,
            self.group_names
        )
        
        # UI更新
        status_label.config(text=STATUS_MESSAGES['displaying'])
        self.root.update()
        
        if not append:
            self.apply_filter()
        
        self.update_group_list()
        if not append:
            self.update_message_list()
        
        # 完了メッセージ
        msg_count = len(self.notifications)
        status_label.config(
            text=STATUS_MESSAGES['completed'].format(
                filename=log_file.name,
                lines=len(self.current_logs),
                messages=msg_count
            )
        )
    
    def _on_load_error(self, error: Exception):
        """読み込みエラー時の処理"""
        status_label = self.widgets['status_label']
        
        # プログレスダイアログを閉じる
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        import traceback
        error_details = traceback.format_exc()
        messagebox.showerror(
            "読み込みエラー",
            f"ファイルの読み込み中にエラーが発生しました:\n\n{error}\n\n"
            f"詳細:\n{error_details[:300]}"
        )
        status_label.config(text=STATUS_MESSAGES['error'].format(error=str(error)[:50]))
        print(f"エラー詳細:\n{error_details}")
    
    # ==================== 自動更新 ====================
    
    def toggle_auto_update(self) -> None:
        """自動更新のオン/オフ切り替え"""
        update_indicator = self.widgets['update_indicator']
        
        if self.auto_update_var.get():
            self.auto_update = True
            update_indicator.config(foreground="green")
            self.check_for_updates()
        else:
            self.auto_update = False
            update_indicator.config(foreground="gray")
    
    def check_for_updates(self) -> None:
        """ファイルの更新をチェック"""
        if not self.auto_update:
            return
        
        update_indicator = self.widgets['update_indicator']
        status_label = self.widgets['status_label']
        
        try:
            if self.current_log_file and self.current_log_file.exists():
                current_size = self.current_log_file.stat().st_size
                
                if current_size != self.last_file_size:
                    update_indicator.config(text="●", foreground="orange")
                    self.root.update()
                    
                    self.load_log_file(self.current_log_file, append=True)
                    
                    update_indicator.config(text="●", foreground="green")
                    status_label.config(
                        text=STATUS_MESSAGES['updated'].format(
                            time=datetime.now().strftime('%H:%M:%S')
                        )
                    )
        except Exception as e:
            print(f"自動更新エラー: {e}")
        
        if self.auto_update:
            self.root.after(AUTO_UPDATE_INTERVAL, self.check_for_updates)
    
    # ==================== グループメッセージ管理 ====================
    
    def update_group_list(self) -> None:
        """グループリストを更新"""
        group_combo = self.widgets['group_combo']
        group_list = ["すべてのグループ"]
        
        sorted_groups = sorted(
            self.groups.items(),
            key=lambda x: len(x[1]['messages']),
            reverse=True
        )
        
        for group_id, group_info in sorted_groups:
            msg_count = len(group_info['messages'])
            group_list.append(f"{group_info['name']} ({msg_count})")
        
        current_selection = group_combo.get()
        group_combo['values'] = group_list
        
        if current_selection in group_list:
            group_combo.set(current_selection)
        else:
            group_combo.current(0)
    
    def refresh_messages(self) -> None:
        """メッセージを再読み込み"""
        if self.current_log_file:
            self.load_log_file(self.current_log_file)
            messagebox.showinfo("更新", "メッセージを更新しました")
    
    def edit_group_name(self) -> None:
        """グループ名を編集"""
        group_combo = self.widgets['group_combo']
        selection = group_combo.get()
        
        if selection == "すべてのグループ" or not selection:
            messagebox.showinfo("情報", "編集するグループを選択してください")
            return
        
        group_index = group_combo.current() - 1
        if group_index < 0 or group_index >= len(self.groups):
            return
        
        group_id = list(self.groups.keys())[group_index]
        current_name = self.groups[group_id]['name']
        
        new_name = simpledialog.askstring(
            "グループ名編集",
            f"グループ名を入力してください:\n(現在: {current_name})",
            initialvalue=current_name
        )
        
        if new_name and new_name != current_name:
            self.group_names[group_id] = new_name
            self.groups[group_id]['name'] = new_name
            self.save_group_names()
            self.update_group_list()
            messagebox.showinfo("成功", "グループ名を更新しました")
    
    def update_message_list(self) -> None:
        """メッセージリストを更新"""
        msg_tree = self.widgets['msg_tree']
        msg_stats_label = self.widgets['msg_stats_label']
        group_combo = self.widgets['group_combo']
        
        # ツリーをクリア
        for item in msg_tree.get_children():
            msg_tree.delete(item)
        
        selected_group = group_combo.get()
        
        # 表示するメッセージを選択
        if selected_group == "すべてのグループ" or not selected_group:
            messages = self.notifications
        else:
            group_index = group_combo.current() - 1
            if 0 <= group_index < len(self.groups):
                group_id = list(self.groups.keys())[group_index]
                messages = self.groups[group_id]['messages']
            else:
                messages = []
        
        # 日付でソート
        sorted_messages = sorted(messages, key=lambda x: x.date, reverse=True)
        
        # ツリーに追加
        for i, notif in enumerate(sorted_messages):
            preview = notif.message[:50].replace('\n', ' ')
            if len(notif.message) > 50:
                preview += "..."
            
            msg_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(notif.date, preview)
            )
        
        msg_stats_label.config(text=f"メッセージ: {len(sorted_messages)} 件")
        self.current_displayed_messages = sorted_messages
    
    def filter_messages(self, *args) -> None:
        """メッセージを検索フィルタリング"""
        msg_search_var = self.widgets['msg_search_var']
        msg_tree = self.widgets['msg_tree']
        msg_stats_label = self.widgets['msg_stats_label']
        group_combo = self.widgets['group_combo']
        
        search_text = msg_search_var.get().lower()
        
        if not search_text:
            self.update_message_list()
            return
        
        # ツリーをクリア
        for item in msg_tree.get_children():
            msg_tree.delete(item)
        
        selected_group = group_combo.get()
        
        # 表示するメッセージを選択
        if selected_group == "すべてのグループ" or not selected_group:
            messages = self.notifications
        else:
            group_index = group_combo.current() - 1
            if 0 <= group_index < len(self.groups):
                group_id = list(self.groups.keys())[group_index]
                messages = self.groups[group_id]['messages']
            else:
                messages = []
        
        # フィルタリング
        filtered_messages = [
            notif for notif in messages
            if search_text in notif.message.lower()
        ]
        
        # ツリーに追加
        for i, notif in enumerate(filtered_messages):
            preview = notif.message[:50].replace('\n', ' ')
            if len(notif.message) > 50:
                preview += "..."
            
            msg_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(notif.date, preview)
            )
        
        msg_stats_label.config(
            text=f"メッセージ: {len(filtered_messages)} / {len(messages)} 件"
        )
        self.current_displayed_messages = filtered_messages
    
    def export_messages(self) -> None:
        """メッセージをエクスポート"""
        if not self.notifications:
            messagebox.showinfo("情報", "エクスポートするメッセージがありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="メッセージをエクスポート",
            defaultextension=".txt",
            filetypes=[
                ("テキストファイル", "*.txt"),
                ("JSONファイル", "*.json"),
                ("すべてのファイル", "*.*")
            ]
        )
        
        if file_path:
            try:
                group_combo = self.widgets['group_combo']
                selected_group = group_combo.get()
                
                # エクスポートするメッセージを選択
                if selected_group == "すべてのグループ" or not selected_group:
                    messages = self.notifications
                else:
                    group_index = group_combo.current() - 1
                    if 0 <= group_index < len(self.groups):
                        group_id = list(self.groups.keys())[group_index]
                        messages = self.groups[group_id]['messages']
                    else:
                        messages = []
                
                # エクスポート
                if file_path.endswith('.json'):
                    export_data = ExportUtils.export_to_json(self.groups, messages)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    text_data = ExportUtils.export_to_text(self.groups, messages)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_data)
                
                messagebox.showinfo("成功", f"メッセージをエクスポートしました:\n{file_path}")
            except Exception as e:
                messagebox.showerror(
                    "エラー",
                    ERROR_MESSAGES['export_error'].format(error=e)
                )
    
    # ==================== ログフィルタリング ====================
    
    def apply_filter(self, *args) -> None:
        """ログフィルターを適用（最適化版）"""
        log_tree = self.widgets['log_tree']
        search_var = self.widgets['search_var']
        stats_label = self.widgets['stats_label']
        
        search_text = search_var.get().lower()
        
        # Treeviewをクリア
        for item in log_tree.get_children():
            log_tree.delete(item)
        
        # フィルター設定を辞書化
        show_filters = {
            'error': self.widgets['show_error'].get(),
            'warning': self.widgets['show_warning'].get(),
            'debug': self.widgets['show_debug'].get(),
            'info': self.widgets['show_info'].get()
        }
        
        filtered_count = 0
        items_to_insert = []
        
        # グループ化用の状態管理
        current_tag = None
        current_message_pattern = None
        tag_group = []
        tag_count = 0
        
        for line in self.current_logs:
            # 検索フィルター
            if search_text and search_text not in line.lower():
                continue
            
            # ログレベルフィルター
            if not LogParser.should_show_log(line, show_filters):
                continue
            
            # ログ情報を解析
            log_info = LogParser.parse_log_line(line, self.collapse_long_lines.get())
            
            # 連続タグ・メッセージのグループ化
            if self.collapse_repeated_tags.get():
                tag_match = re.search(r'\[([\w\s]+)\]', line)
                line_tag = tag_match.group(1) if tag_match else None
                
                # メッセージパターンを抽出
                content_clean = re.sub(r'\d+', 'N', log_info.content[:100])
                
                # 同じグループか判定
                is_same_group = False
                if line_tag and line_tag == current_tag:
                    is_same_group = True
                elif not line_tag and current_message_pattern and content_clean == current_message_pattern:
                    is_same_group = True
                
                if is_same_group:
                    tag_group.append(log_info)
                    tag_count += 1
                    continue
                else:
                    # 前のグループを挿入
                    if tag_count >= GROUP_COLLAPSE_THRESHOLD:
                        self._insert_grouped_logs(tag_group, current_tag or "同じメッセージ")
                    elif tag_group:
                        items_to_insert.extend(tag_group)
                    
                    # 新しいグループ開始
                    current_tag = line_tag
                    current_message_pattern = content_clean if not line_tag else None
                    tag_group = [log_info]
                    tag_count = 1
            else:
                items_to_insert.append(log_info)
            
            filtered_count += 1
            
            # バッチ挿入
            if len(items_to_insert) >= BATCH_SIZE:
                self._insert_log_items(items_to_insert)
                items_to_insert = []
        
        # 最後のグループを処理
        if self.collapse_repeated_tags.get() and tag_count >= GROUP_COLLAPSE_THRESHOLD:
            self._insert_grouped_logs(tag_group, current_tag or "同じメッセージ")
        elif tag_group:
            items_to_insert.extend(tag_group)
        
        # 残りを挿入
        if items_to_insert:
            self._insert_log_items(items_to_insert)
        
        stats_label.config(text=f"表示: {filtered_count} / {len(self.current_logs)} 行")
    
    def _insert_log_items(self, items: List[LogInfo]) -> None:
        """複数のログアイテムを一度に挿入"""
        log_tree = self.widgets['log_tree']
        for item in items:
            log_tree.insert(
                "",
                "end",
                values=(item.timestamp, item.level, item.content),
                tags=item.tags
            )
    
    def _insert_grouped_logs(self, group: List[LogInfo], tag_name: str) -> None:
        """グループ化されたログを挿入"""
        log_tree = self.widgets['log_tree']
        
        # グループヘッダー
        parent = log_tree.insert(
            "",
            "end",
            values=("", f"[{tag_name}]", f"📁 {len(group)} 件のログ（クリックで展開）"),
            tags=["group_header"],
            open=False
        )
        
        # 子要素として各ログを追加
        for item in group:
            log_tree.insert(
                parent,
                "end",
                values=(item.timestamp, item.level, item.content),
                tags=item.tags
            )
    
    # ==================== テーマ管理 ====================
    
    def apply_current_theme(self, theme=None):
        """現在のテーマを適用"""
        try:
            # 引数でテーマが渡された場合はそれを使用、なければ現在のテーマを使用
            if theme is None:
                theme = self.theme_manager.current_theme
            else:
                # テーマエディタから渡された場合、テーママネージャーにも反映
                self.theme_manager.current_theme = theme
            
            # ルートウィンドウの背景色を設定
            self.root.configure(bg=theme.background)
            
            # ttkスタイルを完全に設定
            from tkinter import ttk
            style = ttk.Style()
            
            # すべてのttkウィジェットの背景色を設定
            style.configure(".", background=theme.background, foreground=theme.foreground)
            style.configure("TFrame", background=theme.background)
            style.configure("TLabel", background=theme.background, foreground=theme.foreground)
            style.configure("TLabelframe", background=theme.background, foreground=theme.foreground, bordercolor=theme.panel_border)
            style.configure("TLabelframe.Label", background=theme.background, foreground=theme.foreground)
            style.configure("TButton", background=theme.button_bg, foreground=theme.button_fg)
            style.map("TButton", background=[('active', theme.hover_bg), ('pressed', theme.selected)])
            style.configure("TEntry", fieldbackground=theme.input_field_bg, foreground=theme.input_field_fg, insertbackground=theme.input_field_fg)
            style.configure("TCombobox", fieldbackground=theme.input_field_bg, foreground=theme.input_field_fg, selectbackground=theme.selected)
            
            # ステータスバー用のスタイル
            style.configure("Status.TLabel", background=theme.status_bar_bg, foreground=theme.status_bar_fg, padding=5)
            
            # 統計表示用のスタイル（強調）
            style.configure("Stats.TLabel", background=theme.heading_background, foreground=theme.heading_foreground, padding=5, font=("", 9, "bold"))
            
            # Treeviewのスタイル
            style.configure(
                "Dark.Treeview",
                background=theme.background,
                foreground=theme.foreground,
                fieldbackground=theme.fieldbackground,
                borderwidth=0
            )
            style.configure(
                "Dark.Treeview.Heading",
                background=theme.heading_background,
                foreground=theme.heading_foreground,
                borderwidth=1
            )
            style.map(
                'Dark.Treeview',
                background=[('selected', theme.selected)],
                foreground=[('selected', theme.foreground)]
            )
            
            # PanedWindowのスタイル
            style.configure("TPanedwindow", background=theme.background)
            style.configure("Sash", sashthickness=5, background=theme.heading_background)
            
            # ログツリーのタグを更新
            log_tree = self.widgets.get('log_tree')
            if log_tree:
                log_tree.tag_configure("debug", foreground=theme.log_debug)
                log_tree.tag_configure("info", foreground=theme.log_info)
                log_tree.tag_configure("warning", foreground=theme.log_warning)
                log_tree.tag_configure("error", foreground=theme.log_error)
                log_tree.tag_configure("notification", foreground=theme.log_notification)
                log_tree.tag_configure("collapsed", foreground=theme.log_collapsed)
                log_tree.tag_configure(
                    "group_header",
                    background=theme.group_header_bg,
                    foreground=theme.group_header_fg,
                    font=("Consolas", 9, "bold")
                )
            
            # すべてのウィジェットの色を更新
            self._update_all_widgets(theme)
                
        except Exception as e:
            print(f"テーマ適用エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_all_widgets(self, theme):
        """すべてのウィジェットを再帰的に更新"""
        def update_widget(widget):
            try:
                widget_class = widget.winfo_class()
                widget_name = str(widget)
                
                # 特定のウィジェットに専用色を適用
                # メッセージ詳細エリア
                if 'msg_detail' in widget_name or widget_class == 'Text':
                    try:
                        widget.configure(
                            bg=theme.text_area_bg, 
                            fg=theme.text_area_fg, 
                            insertbackground=theme.text_area_fg,
                            selectbackground=theme.selected, 
                            selectforeground=theme.text_area_fg
                        )
                    except:
                        pass
                # 入力欄・検索欄
                elif widget_class == 'Entry' or 'search' in widget_name or 'entry' in widget_name.lower():
                    widget.configure(
                        bg=theme.input_field_bg, 
                        fg=theme.input_field_fg, 
                        insertbackground=theme.input_field_fg, 
                        selectbackground=theme.selected, 
                        selectforeground=theme.input_field_fg
                    )
                # ステータスバー
                elif 'status' in widget_name.lower() and widget_class == 'TLabel':
                    try:
                        # ttkラベルはスタイルで設定
                        pass
                    except:
                        pass
                # 標準ウィジェット
                elif widget_class == 'Frame':
                    widget.configure(bg=theme.background)
                elif widget_class == 'Label':
                    # ステータスラベルは特別扱い
                    if 'status' in widget_name.lower():
                        widget.configure(bg=theme.status_bar_bg, fg=theme.status_bar_fg)
                    else:
                        widget.configure(bg=theme.background, fg=theme.foreground)
                elif widget_class == 'Labelframe':
                    widget.configure(bg=theme.background, fg=theme.foreground)
                elif widget_class == 'Button':
                    widget.configure(
                        bg=theme.button_bg, 
                        fg=theme.button_fg, 
                        activebackground=theme.hover_bg, 
                        activeforeground=theme.button_fg
                    )
                elif widget_class == 'Listbox':
                    widget.configure(
                        bg=theme.background, 
                        fg=theme.foreground, 
                        selectbackground=theme.selected, 
                        selectforeground=theme.foreground
                    )
                elif widget_class == 'Canvas':
                    widget.configure(bg=theme.background)
                
                # 子ウィジェットを再帰的に更新
                for child in widget.winfo_children():
                    update_widget(child)
            except Exception as e:
                # エラーが出ても続行
                pass
        
        # ルートから開始
        update_widget(self.root)
    
    def _update_widget_colors(self, widget, theme):
        """ウィジェットの色を再帰的に更新（互換性のため残す）"""
        # 新しいメソッドに委譲
        self._update_all_widgets(theme)
    
    def select_theme(self):
        """テーマ選択ダイアログ"""
        from tkinter import ttk
        
        dialog = tk.Toplevel(self.root)
        dialog.title("テーマを選択")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        
        # 中央に配置
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 300
        dialog.geometry(f"500x600+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="テーマを選択してください:", font=("", 11, "bold")).pack(pady=(0, 10))
        
        # テーマリスト
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        theme_listbox = tk.Listbox(list_frame, font=("", 10), height=8)
        theme_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=theme_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        theme_listbox.configure(yscrollcommand=scrollbar.set)
        
        # テーマを追加
        theme_names = self.theme_manager.get_theme_names()
        for name in theme_names:
            theme_listbox.insert(tk.END, name)
        
        # 現在のテーマを選択
        try:
            current_index = theme_names.index(self.theme_manager.current_theme.name)
            theme_listbox.selection_set(current_index)
            theme_listbox.see(current_index)
        except:
            theme_listbox.selection_set(0)
        
        # プレビューフレーム
        preview_frame = ttk.LabelFrame(main_frame, text="プレビュー", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 情報表示
        info_text = tk.Text(preview_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, font=("", 9))
        info_text.pack(fill=tk.X, pady=(0, 5))
        
        # カラープレビュー
        color_preview_frame = ttk.Frame(preview_frame)
        color_preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # プレビュー用のラベル
        preview_labels = {}
        for i, (label_text, key) in enumerate([
            ("背景", "background"),
            ("文字", "foreground"),
            ("Debug", "log_debug"),
            ("Info", "log_info"),
            ("Warning", "log_warning"),
            ("Error", "log_error")
        ]):
            row = i // 2
            col = i % 2
            
            label = tk.Label(color_preview_frame, text=label_text, width=15, height=2, relief=tk.RAISED)
            label.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            preview_labels[key] = label
        
        color_preview_frame.grid_columnconfigure(0, weight=1)
        color_preview_frame.grid_columnconfigure(1, weight=1)
        
        def update_preview(event=None):
            selection = theme_listbox.curselection()
            if selection:
                theme_name = theme_listbox.get(selection[0])
                theme = self.theme_manager.get_theme(theme_name)
                if theme:
                    # 情報を表示
                    info = f"{theme.name}\n作成者: {theme.author}\n\n{theme.description}"
                    info_text.config(state=tk.NORMAL)
                    info_text.delete(1.0, tk.END)
                    info_text.insert(1.0, info)
                    info_text.config(state=tk.DISABLED, bg=theme.background, fg=theme.foreground)
                    
                    # カラープレビューを更新
                    preview_labels["background"].config(bg=theme.background, fg=theme.foreground)
                    preview_labels["foreground"].config(bg=theme.foreground, fg=theme.background)
                    preview_labels["log_debug"].config(bg=theme.background, fg=theme.log_debug)
                    preview_labels["log_info"].config(bg=theme.background, fg=theme.log_info)
                    preview_labels["log_warning"].config(bg=theme.background, fg=theme.log_warning)
                    preview_labels["log_error"].config(bg=theme.background, fg=theme.log_error)
        
        theme_listbox.bind("<<ListboxSelect>>", update_preview)
        update_preview()
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_theme():
            selection = theme_listbox.curselection()
            if selection:
                theme_name = theme_listbox.get(selection[0])
                theme = self.theme_manager.get_theme(theme_name)
                if theme:
                    self.theme_manager.apply_theme(theme)
                    self.apply_current_theme()
                    messagebox.showinfo("成功", f"テーマ「{theme_name}」を適用しました")
                    dialog.destroy()
        
        ttk.Button(button_frame, text="適用", command=apply_theme).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="キャンセル", command=dialog.destroy).pack(side=tk.RIGHT, padx=2)
    
    def customize_theme(self):
        """テーマカスタマイズダイアログ"""
        try:
            ThemeEditor(self.root, self.theme_manager, self.theme_manager.current_theme, self.apply_current_theme)
        except Exception as e:
            messagebox.showerror("エラー", f"テーマエディタを開けませんでした:\n{e}")
    
    def export_theme(self):
        """テーマをエクスポート"""
        file_path = filedialog.asksaveasfilename(
            title="テーマをエクスポート",
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.theme_manager.current_theme.to_dict(), f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"テーマをエクスポートしました:\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{e}")
    
    def import_theme(self):
        """テーマをインポート"""
        file_path = filedialog.askopenfilename(
            title="テーマをインポート",
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                theme = ColorScheme.from_dict(data)
                
                # 同名のテーマがあれば確認
                if theme.name in self.theme_manager.available_themes:
                    if not messagebox.askyesno("確認", f"テーマ「{theme.name}」は既に存在します。\n上書きしますか？"):
                        return
                
                self.theme_manager.available_themes[theme.name] = theme
                self.theme_manager.save_theme(theme)
                
                messagebox.showinfo("成功", f"テーマ「{theme.name}」をインポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"インポートに失敗しました:\n{e}")
    
    # ==================== プラグイン管理 ====================
    
    def initialize_plugins(self):
        """プラグインを初期化"""
        try:
            # アプリケーションコンテキストを設定
            context = {
                'root': self.root,
                'widgets': self.widgets,
                'theme_manager': self.theme_manager,
                'plugin_manager': self.plugin_manager,
                'app': self
            }
            
            self.plugin_manager.set_app_context(context)
            
            # プラグインを読み込み
            self.plugin_manager.load_all_plugins()
        except Exception as e:
            print(f"プラグイン初期化エラー: {e}")
    
    def manage_plugins(self):
        """プラグイン管理ダイアログ"""
        try:
            PluginManagerDialog(self.root, self.plugin_manager)
        except Exception as e:
            messagebox.showerror("エラー", f"プラグイン管理画面を開けませんでした:\n{e}")
    
    def get_plugin_menu_items(self):
        """プラグインメニュー項目を取得"""
        try:
            return self.plugin_manager.get_plugin_menu_items()
        except Exception as e:
            print(f"プラグインメニュー取得エラー: {e}")
            return []

