"""
VRChat ログビューアー - データモデル

ログ情報、通知データなどのデータクラスを定義
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LogInfo:
    """ログ情報のデータクラス"""
    timestamp: str
    level: str
    content: str
    full_content: Optional[str] = None
    is_collapsed: bool = False
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.tags is None:
            self.tags = []


@dataclass
class NotificationData:
    """通知データのデータクラス"""
    id: str
    date: str
    created_at: str
    message: str
    group_id: str
    raw_line: str
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'date': self.date,
            'created_at': self.created_at,
            'message': self.message,
            'group_id': self.group_id
        }


@dataclass
class GroupInfo:
    """グループ情報のデータクラス"""
    id: str
    name: str
    messages: List[NotificationData] = field(default_factory=list)
    
    def message_count(self) -> int:
        """メッセージ数を取得"""
        return len(self.messages)
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'message_count': self.message_count()
        }
