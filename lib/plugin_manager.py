"""
VRChat ログビューアー - プラグインシステム

プラグインの読み込み・管理・実行を行うモジュール
"""

import json
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext


@dataclass
class PluginInfo:
    """プラグイン情報"""
    id: str
    name: str
    version: str
    author: str
    description: str
    install_date: str
    enabled: bool = True
    file_path: str = ""
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'PluginInfo':
        """辞書から作成"""
        return PluginInfo(**data)


class Plugin:
    """プラグインの基底クラス"""
    
    def __init__(self):
        self.info = PluginInfo(
            id="base_plugin",
            name="Base Plugin",
            version="1.0.0",
            author="System",
            description="プラグインの基底クラス",
            install_date=datetime.now().isoformat()
        )
    
    def on_load(self, app_context):
        """
        プラグイン読み込み時に呼ばれる
        
        Args:
            app_context: アプリケーションのコンテキスト
                - root: メインウィンドウ
                - widgets: UIウィジェット辞書
                - theme_manager: テーママネージャー
                - plugin_manager: プラグインマネージャー
        """
        pass
    
    def on_unload(self):
        """プラグインアンロード時に呼ばれる"""
        pass
    
    def on_log_loaded(self, logs: list):
        """ログ読み込み時に呼ばれる"""
        pass
    
    def on_log_filtered(self, filtered_logs: list):
        """ログフィルタリング時に呼ばれる"""
        pass
    
    def get_menu_items(self) -> List[tuple]:
        """
        メニューに追加する項目を返す
        
        Returns:
            [(ラベル, コールバック関数), ...]
        """
        return []
    
    def get_context_menu_items(self, selected_logs: list) -> List[tuple]:
        """
        コンテキストメニューに追加する項目を返す
        
        Args:
            selected_logs: 選択されているログ
        
        Returns:
            [(ラベル, コールバック関数), ...]
        """
        return []


class PluginManager:
    """プラグイン管理クラス"""
    
    def __init__(self):
        # スクリプトと同じディレクトリにpluginsフォルダを作成
        script_dir = Path(__file__).parent
        self.plugins_dir = script_dir / "plugins"
        
        try:
            self.plugins_dir.mkdir(exist_ok=True)
        except PermissionError:
            # 権限がない場合はユーザーのホームディレクトリに作成
            import os
            home_dir = Path(os.path.expanduser("~"))
            self.plugins_dir = home_dir / ".vrchat_log_viewer" / "plugins"
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.plugin_infos: Dict[str, PluginInfo] = {}
        
        self.app_context = None
        
        # プラグイン設定ファイル（スクリプトと同じ場所）
        self.config_file = script_dir / "plugin_config.json"
        self.load_config()
        
        # サンプルプラグインを作成
        self._create_sample_plugins()
    
    def _create_sample_plugins(self):
        """サンプルプラグインを作成"""
        # ログ統計プラグイン
        sample1_path = self.plugins_dir / "log_statistics.py"
        if not sample1_path.exists():
            sample1_code = '''"""
ログ統計プラグイン

ログの統計情報を表示するサンプルプラグイン
"""

from plugin_manager import Plugin, PluginInfo
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class LogStatisticsPlugin(Plugin):
    """ログ統計プラグイン"""
    
    def __init__(self):
        super().__init__()
        self.info = PluginInfo(
            id="log_statistics",
            name="ログ統計",
            version="1.0.0",
            author="サンプル作者",
            description="ログの統計情報を表示します",
            install_date=datetime.now().isoformat()
        )
        self.current_logs = []
    
    def on_log_loaded(self, logs: list):
        """ログ読み込み時"""
        self.current_logs = logs
    
    def get_menu_items(self):
        """メニュー項目"""
        return [
            ("📊 ログ統計を表示", self.show_statistics)
        ]
    
    def show_statistics(self):
        """統計情報を表示"""
        if not self.current_logs:
            messagebox.showinfo("統計", "ログがありません")
            return
        
        total = len(self.current_logs)
        
        # ログレベルをカウント
        debug_count = sum(1 for log in self.current_logs if 'debug' in log.lower())
        info_count = sum(1 for log in self.current_logs if 'info' in log.lower())
        warning_count = sum(1 for log in self.current_logs if 'warning' in log.lower())
        error_count = sum(1 for log in self.current_logs if 'error' in log.lower() or 'exception' in log.lower())
        
        stats = f"""
ログ統計情報:

総行数: {total:,}
Debug: {debug_count:,} ({debug_count/total*100:.1f}%)
Info: {info_count:,} ({info_count/total*100:.1f}%)
Warning: {warning_count:,} ({warning_count/total*100:.1f}%)
Error: {error_count:,} ({error_count/total*100:.1f}%)
その他: {total - debug_count - info_count - warning_count - error_count:,}
"""
        
        messagebox.showinfo("ログ統計", stats)


# プラグインのインスタンスを作成
plugin_instance = LogStatisticsPlugin()
'''
            sample1_path.write_text(sample1_code, encoding='utf-8')
        
        # エクスポート拡張プラグイン
        sample2_path = self.plugins_dir / "export_extended.py"
        if not sample2_path.exists():
            sample2_code = '''"""
エクスポート拡張プラグイン

追加のエクスポート形式を提供するサンプルプラグイン
"""

from plugin_manager import Plugin, PluginInfo
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox


class ExportExtendedPlugin(Plugin):
    """エクスポート拡張プラグイン"""
    
    def __init__(self):
        super().__init__()
        self.info = PluginInfo(
            id="export_extended",
            name="エクスポート拡張",
            version="1.0.0",
            author="サンプル作者",
            description="HTML/Markdownエクスポート機能を追加",
            install_date=datetime.now().isoformat()
        )
        self.current_logs = []
    
    def on_log_loaded(self, logs: list):
        """ログ読み込み時"""
        self.current_logs = logs
    
    def get_menu_items(self):
        """メニュー項目"""
        return [
            ("📄 HTMLでエクスポート", self.export_html),
            ("📝 Markdownでエクスポート", self.export_markdown)
        ]
    
    def export_html(self):
        """HTML形式でエクスポート"""
        if not self.current_logs:
            messagebox.showinfo("エクスポート", "ログがありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="HTMLエクスポート",
            defaultextension=".html",
            filetypes=[("HTMLファイル", "*.html")]
        )
        
        if file_path:
            try:
                html = self._generate_html()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                messagebox.showinfo("成功", f"エクスポートしました:\\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポート失敗:\\n{e}")
    
    def export_markdown(self):
        """Markdown形式でエクスポート"""
        if not self.current_logs:
            messagebox.showinfo("エクスポート", "ログがありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Markdownエクスポート",
            defaultextension=".md",
            filetypes=[("Markdownファイル", "*.md")]
        )
        
        if file_path:
            try:
                md = self._generate_markdown()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md)
                messagebox.showinfo("成功", f"エクスポートしました:\\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポート失敗:\\n{e}")
    
    def _generate_html(self) -> str:
        """HTML生成"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VRChat ログ</title>
    <style>
        body { font-family: 'Consolas', monospace; background: #1e1e1e; color: #d4d4d4; }
        .log-line { padding: 2px 5px; border-bottom: 1px solid #333; }
        .debug { color: #6a9955; }
        .info { color: #4fc1ff; }
        .warning { color: #dcdcaa; }
        .error { color: #f48771; }
    </style>
</head>
<body>
    <h1>VRChat ログ</h1>
    <div class="logs">
"""
        
        for log in self.current_logs[:1000]:  # 最初の1000行のみ
            log_class = "log-line"
            if 'error' in log.lower():
                log_class += " error"
            elif 'warning' in log.lower():
                log_class += " warning"
            elif 'debug' in log.lower():
                log_class += " debug"
            elif 'info' in log.lower():
                log_class += " info"
            
            html += f'        <div class="{log_class}">{log.strip()}</div>\\n'
        
        html += """    </div>
</body>
</html>"""
        
        return html
    
    def _generate_markdown(self) -> str:
        """Markdown生成"""
        md = "# VRChat ログ\\n\\n"
        md += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
        md += "```\\n"
        
        for log in self.current_logs[:1000]:
            md += log
        
        md += "```\\n"
        
        return md


# プラグインのインスタンスを作成
plugin_instance = ExportExtendedPlugin()
'''
            sample2_path.write_text(sample2_code, encoding='utf-8')
    
    def load_config(self):
        """プラグイン設定を読み込み"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for plugin_id, plugin_data in data.items():
                        self.plugin_infos[plugin_id] = PluginInfo.from_dict(plugin_data)
            except Exception as e:
                print(f"プラグイン設定読み込みエラー: {e}")
    
    def save_config(self):
        """プラグイン設定を保存"""
        try:
            data = {
                plugin_id: info.to_dict()
                for plugin_id, info in self.plugin_infos.items()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"プラグイン設定保存エラー: {e}")
    
    def set_app_context(self, context):
        """アプリケーションコンテキストを設定"""
        self.app_context = context
    
    def discover_plugins(self):
        """プラグインを検索"""
        discovered = []
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                # プラグインを読み込み
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem,
                    plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_file.stem] = module
                spec.loader.exec_module(module)
                
                # plugin_instanceを取得
                if hasattr(module, 'plugin_instance'):
                    plugin = module.plugin_instance
                    plugin.info.file_path = str(plugin_file)
                    
                    # 設定に追加
                    if plugin.info.id not in self.plugin_infos:
                        self.plugin_infos[plugin.info.id] = plugin.info
                    
                    discovered.append(plugin)
            
            except Exception as e:
                print(f"プラグイン読み込みエラー ({plugin_file.name}): {e}")
        
        return discovered
    
    def load_all_plugins(self):
        """すべてのプラグインを読み込み"""
        plugins = self.discover_plugins()
        
        for plugin in plugins:
            if self.plugin_infos[plugin.info.id].enabled:
                try:
                    plugin.on_load(self.app_context)
                    self.loaded_plugins[plugin.info.id] = plugin
                    print(f"プラグイン読み込み: {plugin.info.name}")
                except Exception as e:
                    print(f"プラグイン初期化エラー ({plugin.info.name}): {e}")
        
        self.save_config()
    
    def unload_plugin(self, plugin_id: str):
        """プラグインをアンロード"""
        if plugin_id in self.loaded_plugins:
            try:
                self.loaded_plugins[plugin_id].on_unload()
                del self.loaded_plugins[plugin_id]
            except Exception as e:
                print(f"プラグインアンロードエラー: {e}")
    
    def enable_plugin(self, plugin_id: str):
        """プラグインを有効化"""
        if plugin_id in self.plugin_infos:
            self.plugin_infos[plugin_id].enabled = True
            self.save_config()
    
    def disable_plugin(self, plugin_id: str):
        """プラグインを無効化"""
        if plugin_id in self.plugin_infos:
            self.plugin_infos[plugin_id].enabled = False
            self.unload_plugin(plugin_id)
            self.save_config()
    
    def get_plugin_menu_items(self) -> List[tuple]:
        """すべてのプラグインのメニュー項目を取得"""
        items = []
        for plugin in self.loaded_plugins.values():
            try:
                plugin_items = plugin.get_menu_items()
                items.extend(plugin_items)
            except Exception as e:
                print(f"メニュー項目取得エラー ({plugin.info.name}): {e}")
        return items
    
    def notify_log_loaded(self, logs: list):
        """ログ読み込みを通知"""
        for plugin in self.loaded_plugins.values():
            try:
                plugin.on_log_loaded(logs)
            except Exception as e:
                print(f"プラグイン通知エラー ({plugin.info.name}): {e}")
    
    def notify_log_filtered(self, filtered_logs: list):
        """ログフィルタリングを通知"""
        for plugin in self.loaded_plugins.values():
            try:
                plugin.on_log_filtered(filtered_logs)
            except Exception as e:
                print(f"プラグイン通知エラー ({plugin.info.name}): {e}")


class PluginManagerDialog:
    """プラグイン管理ダイアログ"""
    
    def __init__(self, parent, plugin_manager: PluginManager):
        self.parent = parent
        self.plugin_manager = plugin_manager
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("プラグイン管理")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        
        # 中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 400
        y = (self.dialog.winfo_screenheight() // 2) - 300
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self.setup_ui()
        self.refresh_plugin_list()
    
    def setup_ui(self):
        """UIを構築"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ツールバー
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 更新", command=self.refresh_plugin_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕ プラグイン追加", command=self.add_plugin).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📁 プラグインフォルダを開く", command=self.open_plugin_folder).pack(side=tk.LEFT, padx=2)
        
        # プラグインリスト
        list_frame = ttk.LabelFrame(main_frame, text="インストール済みプラグイン", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("name", "version", "author", "status", "install_date")
        self.plugin_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )
        
        self.plugin_tree.heading("#0", text="ID")
        self.plugin_tree.heading("name", text="プラグイン名")
        self.plugin_tree.heading("version", text="バージョン")
        self.plugin_tree.heading("author", text="作成者")
        self.plugin_tree.heading("status", text="状態")
        self.plugin_tree.heading("install_date", text="インストール日")
        
        self.plugin_tree.column("#0", width=0, stretch=False)
        self.plugin_tree.column("name", width=200)
        self.plugin_tree.column("version", width=80)
        self.plugin_tree.column("author", width=120)
        self.plugin_tree.column("status", width=80)
        self.plugin_tree.column("install_date", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        
        self.plugin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.plugin_tree.bind("<<TreeviewSelect>>", self.on_plugin_select)
        
        # 詳細パネル
        detail_frame = ttk.LabelFrame(main_frame, text="プラグイン詳細", padding="10")
        detail_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.detail_text = scrolledtext.ScrolledText(
            detail_frame,
            wrap=tk.WORD,
            height=8,
            state=tk.DISABLED
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.enable_button = ttk.Button(button_frame, text="有効化", command=self.enable_plugin, state=tk.DISABLED)
        self.enable_button.pack(side=tk.LEFT, padx=2)
        
        self.disable_button = ttk.Button(button_frame, text="無効化", command=self.disable_plugin, state=tk.DISABLED)
        self.disable_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="削除", command=self.delete_plugin, state=tk.DISABLED).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="閉じる", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=2)
    
    def refresh_plugin_list(self):
        """プラグインリストを更新"""
        # クリア
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
        
        # プラグインを再検索
        self.plugin_manager.discover_plugins()
        
        # 追加
        for plugin_id, info in self.plugin_manager.plugin_infos.items():
            status = "✅ 有効" if info.enabled else "❌ 無効"
            install_date = info.install_date[:19] if len(info.install_date) > 19 else info.install_date
            
            self.plugin_tree.insert(
                "",
                "end",
                iid=plugin_id,
                values=(info.name, info.version, info.author, status, install_date)
            )
    
    def on_plugin_select(self, event):
        """プラグイン選択時"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
        
        plugin_id = selection[0]
        info = self.plugin_manager.plugin_infos.get(plugin_id)
        
        if info:
            # 詳細を表示
            detail = f"""
プラグインID: {info.id}
プラグイン名: {info.name}
バージョン: {info.version}
作成者: {info.author}
状態: {'有効' if info.enabled else '無効'}
インストール日: {info.install_date}

説明:
{info.description}

ファイルパス:
{info.file_path}
"""
            
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, detail)
            self.detail_text.config(state=tk.DISABLED)
            
            # ボタンの状態を更新
            if info.enabled:
                self.enable_button.config(state=tk.DISABLED)
                self.disable_button.config(state=tk.NORMAL)
            else:
                self.enable_button.config(state=tk.NORMAL)
                self.disable_button.config(state=tk.DISABLED)
    
    def add_plugin(self):
        """プラグインを追加"""
        file_path = filedialog.askopenfilename(
            title="プラグインファイルを選択",
            filetypes=[("Pythonファイル", "*.py"), ("すべてのファイル", "*.*")]
        )
        
        if file_path:
            try:
                import shutil
                dest = self.plugin_manager.plugins_dir / Path(file_path).name
                shutil.copy(file_path, dest)
                messagebox.showinfo("成功", f"プラグインを追加しました:\n{dest.name}")
                self.refresh_plugin_list()
            except Exception as e:
                messagebox.showerror("エラー", f"プラグイン追加に失敗しました:\n{e}")
    
    def open_plugin_folder(self):
        """プラグインフォルダを開く"""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', str(self.plugin_manager.plugins_dir)])
            elif system == "Darwin":
                subprocess.run(['open', str(self.plugin_manager.plugins_dir)])
            else:
                subprocess.run(['xdg-open', str(self.plugin_manager.plugins_dir)])
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダを開けませんでした:\n{e}")
    
    def enable_plugin(self):
        """選択したプラグインを有効化"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
        
        plugin_id = selection[0]
        self.plugin_manager.enable_plugin(plugin_id)
        messagebox.showinfo("成功", "プラグインを有効化しました\n次回起動時に読み込まれます")
        self.refresh_plugin_list()
    
    def disable_plugin(self):
        """選択したプラグインを無効化"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
        
        plugin_id = selection[0]
        self.plugin_manager.disable_plugin(plugin_id)
        messagebox.showinfo("成功", "プラグインを無効化しました")
        self.refresh_plugin_list()
    
    def delete_plugin(self):
        """選択したプラグインを削除"""
        selection = self.plugin_tree.selection()
        if not selection:
            return
        
        plugin_id = selection[0]
        info = self.plugin_manager.plugin_infos.get(plugin_id)
        
        if not info:
            return
        
        if messagebox.askyesno("確認", f"プラグイン「{info.name}」を削除しますか?"):
            try:
                # ファイルを削除
                if info.file_path:
                    Path(info.file_path).unlink()
                
                # 設定から削除
                self.plugin_manager.unload_plugin(plugin_id)
                del self.plugin_manager.plugin_infos[plugin_id]
                self.plugin_manager.save_config()
                
                messagebox.showinfo("成功", "プラグインを削除しました")
                self.refresh_plugin_list()
            except Exception as e:
                messagebox.showerror("エラー", f"削除に失敗しました:\n{e}")
