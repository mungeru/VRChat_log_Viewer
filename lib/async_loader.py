"""
VRChat ログビューアー - 非同期ローダー

大きなファイルを別スレッドで読み込み、UIを固まらせない
"""

import threading
import queue
from pathlib import Path
from typing import Callable, Optional, List
from models import NotificationData
from utils import FileUtils, NotificationParser


class AsyncLogLoader:
    """非同期ログ読み込みクラス"""
    
    def __init__(self):
        self.current_thread: Optional[threading.Thread] = None
        self.cancel_flag = threading.Event()
        self.progress_queue = queue.Queue()
    
    def cancel(self):
        """読み込みをキャンセル"""
        self.cancel_flag.set()
    
    def is_loading(self) -> bool:
        """読み込み中かどうか"""
        return self.current_thread is not None and self.current_thread.is_alive()
    
    def load_file_async(
        self,
        file_path: Path,
        on_progress: Callable[[str, int], None],
        on_complete: Callable[[List[str], List[NotificationData]], None],
        on_error: Callable[[Exception], None]
    ):
        """
        ファイルを非同期で読み込み
        
        Args:
            file_path: 読み込むファイルのパス
            on_progress: 進捗コールバック(message, percentage)
            on_complete: 完了コールバック(lines, notifications)
            on_error: エラーコールバック(exception)
        """
        if self.is_loading():
            return
        
        self.cancel_flag.clear()
        
        def _load_worker():
            try:
                # ステップ1: ファイルサイズ取得
                file_size = file_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                
                if self.cancel_flag.is_set():
                    return
                
                on_progress(f"📂 ファイルを開いています... ({file_size_mb:.1f}MB)", 5)
                
                # ステップ2: ファイル内容を読み込み
                on_progress(f"📖 ファイルを読み込み中... ({file_size_mb:.1f}MB)", 10)
                
                if self.cancel_flag.is_set():
                    return
                
                # チャンク読み込み時の進捗コールバック
                read_progress = [10]  # 開始進捗
                
                def on_chunk_read():
                    """チャンク読み込み時の進捗更新"""
                    if self.cancel_flag.is_set():
                        return
                    read_progress[0] += 2
                    if read_progress[0] <= 25:
                        on_progress(f"📖 読み込み中... {read_progress[0]}%", read_progress[0])
                
                content = FileUtils.read_file_with_encoding(file_path, on_chunk_read)
                
                if self.cancel_flag.is_set():
                    return
                
                on_progress("📝 読み込み完了", 30)
                
                # ステップ3: 行に分割
                on_progress("🔄 行を解析中...", 40)
                
                if self.cancel_flag.is_set():
                    return
                
                lines = content.splitlines(keepends=True)
                total_lines = len(lines)
                
                on_progress(f"✅ {total_lines:,} 行を検出", 60)
                
                if self.cancel_flag.is_set():
                    return
                
                # ステップ4: 通知を解析
                on_progress(f"📨 グループメッセージを抽出中...", 70)
                
                if self.cancel_flag.is_set():
                    return
                
                notifications = NotificationParser.parse_notifications(content)
                
                if self.cancel_flag.is_set():
                    return
                
                on_progress(f"🎉 {len(notifications)} 件のメッセージを検出", 90)
                
                on_progress("✅ 読み込み完了", 100)
                
                # 完了コールバック（メインスレッドで実行）
                on_complete(lines, notifications)
                
            except Exception as e:
                if not self.cancel_flag.is_set():
                    on_error(e)
        
        # 別スレッドで実行
        self.current_thread = threading.Thread(target=_load_worker, daemon=True)
        self.current_thread.start()
