"""
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
