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
        
        # UI設定変数
        self.collapse_long_lines = tk.BooleanVar(value=True)
        self.collapse_repeated_tags = tk.BooleanVar(value=True)
        self.auto_update_var = tk.BooleanVar(value=False)
        
        # グループ名管理
        self.group_names: Dict[str, str] = {}
        self.load_group_names()
        
        # UIウィジェット参照
        self.widgets = {}
        
        # UI構築
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # 初期ロード
        self.load_logs()
    
    # ==================== 初期化・設定 ====================
    
    def load_group_names(self) -> None:
        """保存されたグループ名を読み込み"""
        if GROUP_NAMES_FILE.exists():
            try:
                with open(GROUP_NAMES_FILE, 'r', encoding='utf-8') as f:
                    self.group_names = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"グループ名の読み込みエラー: {e}")
                self.group_names = {}
    
    def save_group_names(self) -> None:
        """グループ名を保存"""
        try:
            with open(GROUP_NAMES_FILE, 'w', encoding='utf-8') as f:
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
            'focus_search': lambda: self.widgets['search_entry'].focus_set(),
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
            'show_message_context_menu': self.show_message_context_menu
        }
    
    # ==================== イベントハンドラー ====================
    
    def on_log_double_click(self, event_or_idx, log_info=None) -> None:
        """ログ行のダブルクリックで展開/折りたたみ
        
        Args:
            event_or_idx: tk.Event (従来版) または int (仮想スクロール版のインデックス)
            log_info: LogInfo (仮想スクロール版のみ)
        """
        log_tree = self.widgets.get('log_tree')
        
        # 仮想スクロール版の場合
        if isinstance(event_or_idx, int):
            # 仮想スクロール版では特に何もしない（グループ展開は内部で処理される）
            return
        
        # 従来のTreeview版の場合
        if hasattr(log_tree, 'selection'):
            if not log_tree.selection():
                return
            
            item = log_tree.selection()[0]
            if log_tree.get_children(item):
                current_state = log_tree.item(item, "open")
                log_tree.item(item, open=not current_state)
    
    def show_log_context_menu(self, event, line_idx=None, log_info=None) -> None:
        """ログの右クリックメニューを表示
        
        Args:
            event: tk.Event
            line_idx: int (仮想スクロール版のインデックス、オプション)
            log_info: LogInfo (仮想スクロール版、オプション)
        """
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
        
        # 仮想スクロールビューアの場合
        if hasattr(log_tree, 'get_selected_logs'):
            all_logs = log_tree.get_selected_logs()
            if not all_logs:
                return
            
            copied_text = []
            for log in all_logs:
                log_line = f"{log.timestamp}\t{log.level}\t{log.content}"
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
            return
        
        # 従来のTreeviewの場合
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
        
        # 仮想スクロールの場合は何もしない（既に全選択相当）
        if hasattr(log_tree, 'get_selected_logs'):
            return "break"
        
        # 従来のTreeviewの場合
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
        """個別のログファイルを読み込み"""
        status_label = self.widgets['status_label']
        
        try:
            self.current_log_file = log_file
            
            if not append:
                status_label.config(
                    text=STATUS_MESSAGES['loading'].format(filename=log_file.name)
                )
                self.root.update()
            
            file_size = log_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # 大きなファイルの警告
            if file_size_mb > LARGE_FILE_THRESHOLD_MB and not append:
                response = messagebox.askyesno(
                    "大きなファイル",
                    ERROR_MESSAGES['large_file_warning'].format(size=file_size_mb)
                )
                if not response:
                    status_label.config(text=STATUS_MESSAGES['cancelled'])
                    return
            
            if not append:
                status_label.config(
                    text=STATUS_MESSAGES['reading'].format(size=file_size_mb)
                )
                self.root.update()
            
            # ファイル読み込み
            content = FileUtils.read_file_with_encoding(log_file)
            
            if not append:
                status_label.config(text=STATUS_MESSAGES['parsing'])
                self.root.update()
            
            lines = content.splitlines(keepends=True)
            self.last_file_size = file_size
            
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
        """ログフィルターを適用（仮想スクロール最適化版）"""
        log_tree = self.widgets['log_tree']
        search_var = self.widgets['search_var']
        stats_label = self.widgets['stats_label']
        
        search_text = search_var.get().lower()
        
        # 仮想スクロールビューアーかどうかチェック
        is_virtual = hasattr(log_tree, 'set_logs')
        
        # フィルター設定を辞書化
        show_filters = {
            'error': self.widgets['show_error'].get(),
            'warning': self.widgets['show_warning'].get(),
            'debug': self.widgets['show_debug'].get(),
            'info': self.widgets['show_info'].get()
        }
        
        filtered_logs = []
        filtered_count = 0
        
        # グループ化用の状態管理
        current_tag = None
        current_message_pattern = None
        tag_group_start = None
        tag_group = []
        tag_count = 0
        
        for idx, line in enumerate(self.current_logs):
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
                    # 前のグループを処理
                    if tag_count >= GROUP_COLLAPSE_THRESHOLD:
                        # グループヘッダーを作成
                        header = LogInfo(
                            timestamp="",
                            level="",
                            content=f"📁 [{current_tag or '同じメッセージ'}] {tag_count} 件のログ",
                            tags=["group_header"]
                        )
                        filtered_logs.append(header)
                        
                        if is_virtual and tag_group_start is not None:
                            # 仮想スクロールの場合はグループマーク
                            log_tree.mark_as_group(len(filtered_logs) - 1, len(filtered_logs) - 1 + len(tag_group))
                        
                        # グループの中身も追加（折りたたまれて表示される）
                        filtered_logs.extend(tag_group)
                    elif tag_group:
                        filtered_logs.extend(tag_group)
                    
                    # 新しいグループ開始
                    current_tag = line_tag
                    current_message_pattern = content_clean if not line_tag else None
                    tag_group = [log_info]
                    tag_count = 1
                    tag_group_start = len(filtered_logs)
            else:
                filtered_logs.append(log_info)
            
            filtered_count += 1
        
        # 最後のグループを処理
        if self.collapse_repeated_tags.get() and tag_count >= GROUP_COLLAPSE_THRESHOLD:
            header = LogInfo(
                timestamp="",
                level="",
                content=f"📁 [{current_tag or '同じメッセージ'}] {tag_count} 件のログ",
                tags=["group_header"]
            )
            filtered_logs.append(header)
            filtered_logs.extend(tag_group)
            
            if is_virtual and tag_group_start is not None:
                log_tree.mark_as_group(len(filtered_logs) - 1 - len(tag_group), len(filtered_logs) - 1)
        elif tag_group:
            filtered_logs.extend(tag_group)
        
        # ログを表示
        if is_virtual:
            # 仮想スクロール版: 一括設定（超高速）
            log_tree.set_logs(filtered_logs)
        else:
            # 従来版: Treeviewに挿入
            log_tree.delete(*log_tree.get_children())
            self._insert_log_items_to_treeview(log_tree, filtered_logs)
        
        stats_label.config(text=f"表示: {filtered_count} / {len(self.current_logs)} 行")
    
    def _insert_log_items_to_treeview(self, log_tree, items: List[LogInfo]) -> None:
        """ログアイテムをTreeviewに挿入（従来版フォールバック用）"""
        for item in items:
            log_tree.insert(
                "",
                "end",
                values=(item.timestamp, item.level, item.content),
                tags=item.tags
            )
    
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


def main():
    """メインエントリーポイント"""
    root = tk.Tk()
    app = VRChatLogViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
