"""
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
                messagebox.showinfo("成功", f"エクスポートしました:\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポート失敗:\n{e}")
    
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
                messagebox.showinfo("成功", f"エクスポートしました:\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポート失敗:\n{e}")
    
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
            
            html += f'        <div class="{log_class}">{log.strip()}</div>\n'
        
        html += """    </div>
</body>
</html>"""
        
        return html
    
    def _generate_markdown(self) -> str:
        """Markdown生成"""
        md = "# VRChat ログ\n\n"
        md += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "```\n"
        
        for log in self.current_logs[:1000]:
            md += log
        
        md += "```\n"
        
        return md


# プラグインのインスタンスを作成
plugin_instance = ExportExtendedPlugin()
