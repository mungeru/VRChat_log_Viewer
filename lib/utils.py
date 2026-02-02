"""
VRChat ログビューアー - ユーティリティ関数

ファイル操作、パース処理、グループ判定などの共通処理
"""

import re
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from models import LogInfo, NotificationData
from constants import (
    ENCODINGS,
    LOG_TIMESTAMP_PATTERN,
    NOTIFICATION_PATTERN,
    DEFAULT_GROUP_NAMES,
    LONG_LINE_THRESHOLD
)


class FileUtils:
    """ファイル操作に関するユーティリティ"""
    
    @staticmethod
    def read_file_with_encoding(file_path: Path, progress_callback=None) -> str:
        """複数のエンコーディングで試行してファイルを読み込む"""
        last_error = None
        
        # ファイルサイズを確認
        file_size = file_path.stat().st_size
        
        # UTF-8などの一般的なエンコーディングで試行
        for encoding in ENCODINGS:
            try:
                # 大きなファイル（>5MB）の場合はチャンク読み込み
                if file_size > 5 * 1024 * 1024 and progress_callback:
                    content_parts = []
                    chunk_size = 1024 * 1024  # 1MB chunks
                    
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            content_parts.append(chunk)
                            if progress_callback:
                                progress_callback()
                    
                    return ''.join(content_parts)
                else:
                    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                        return f.read()
            except Exception as e:
                last_error = e
                continue
        
        # 最終手段：バイナリモードで読み込み
        try:
            with open(file_path, 'rb') as f:
                binary_content = f.read()
            return binary_content.decode('utf-8', errors='replace')
        except Exception as e:
            raise IOError(
                f"ファイルの読み込みに失敗しました:\n\n{file_path.name}\n\n"
                f"エラー: {e}\n前回のエラー: {last_error}"
            )
    
    @staticmethod
    def get_sorted_log_files(log_path: Path) -> List[Path]:
        """ログファイルをソートして取得"""
        return sorted(
            [f for f in log_path.glob("output_log_*.txt")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )


class LogParser:
    """ログパース処理に関するユーティリティ"""
    
    @staticmethod
    def parse_log_line(line: str, collapse_long_lines: bool = True) -> LogInfo:
        """ログ行を解析"""
        timestamp_match = re.match(LOG_TIMESTAMP_PATTERN, line)
        
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            level = timestamp_match.group(2)
            content = timestamp_match.group(3).strip()
        else:
            timestamp = ""
            level = ""
            content = line.strip()
        
        # ログレベルに応じたタグ
        tags = LogParser._determine_tags(line)
        
        # 長い行の折りたたみ
        if collapse_long_lines and len(content) > LONG_LINE_THRESHOLD:
            collapsed_content = content[:LONG_LINE_THRESHOLD] + "... [クリックで展開]"
            is_collapsed = True
            full_content = content
        else:
            collapsed_content = content
            is_collapsed = False
            full_content = None
        
        return LogInfo(
            timestamp=timestamp,
            level=level,
            content=collapsed_content,
            full_content=full_content,
            is_collapsed=is_collapsed,
            tags=tags
        )
    
    @staticmethod
    def _determine_tags(line: str) -> List[str]:
        """ログ行からタグを判定"""
        tags = []
        line_lower = line.lower()
        
        if 'Received Notification' in line:
            tags.append('notification')
        elif 'error' in line_lower or 'exception' in line_lower:
            tags.append('error')
        elif 'warning' in line_lower:
            tags.append('warning')
        elif 'debug' in line_lower:
            tags.append('debug')
        elif 'info' in line_lower:
            tags.append('info')
        
        return tags
    
    @staticmethod
    def should_show_log(line: str, show_filters: dict) -> bool:
        """ログレベルフィルターに基づいて表示するか判定"""
        line_lower = line.lower()
        
        if not show_filters.get('error', True) and ('error' in line_lower or 'exception' in line_lower):
            return False
        if not show_filters.get('warning', True) and 'warning' in line_lower:
            return False
        if not show_filters.get('debug', True) and 'debug' in line_lower:
            return False
        if not show_filters.get('info', True) and 'info' in line_lower:
            return False
        
        return True


class NotificationParser:
    """通知メッセージのパース処理に関するユーティリティ"""
    
    @staticmethod
    def parse_notifications(content: str) -> List[NotificationData]:
        """通知メッセージを解析して抽出"""
        notifications = []
        
        matches = re.findall(NOTIFICATION_PATTERN, content, re.DOTALL)
        
        if not matches:
            print("グループメッセージが見つかりませんでした")
            return notifications
        
        success_count = 0
        error_count = 0
        
        for date_str, notif_id, created_at, message in matches:
            try:
                # エスケープ文字を処理
                message = NotificationParser._unescape_message(message)
                
                if not message or message.strip() == "":
                    continue
                
                group_id = GroupUtils.get_group_id_from_message(message)
                
                notif_data = NotificationData(
                    id=notif_id,
                    date=date_str,
                    created_at=created_at,
                    message=message,
                    group_id=group_id,
                    raw_line=f"{date_str} - {notif_id}"
                )
                
                notifications.append(notif_data)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"通知の解析エラー ({notif_id}): {e}")
                continue
        
        if success_count > 0:
            print(f"グループメッセージ抽出完了: {success_count} 件成功, {error_count} 件失敗")
        
        return notifications
    
    @staticmethod
    def _unescape_message(message: str) -> str:
        """メッセージのエスケープ文字を処理"""
        message = message.replace('\\n', '\n')
        message = message.replace('\\t', '\t')
        message = message.replace('\\r', '')
        message = message.replace('\\"', '"')
        return message


class GroupUtils:
    """グループ管理に関するユーティリティ"""
    
    @staticmethod
    def get_group_id_from_message(message: str) -> str:
        """メッセージ内容からグループIDを判定"""
        if '震度' in message or '地震' in message:
            return 'group_earthquake'
        elif '开店' in message or '開店' in message or 'Bar' in message or 'NBB' in message:
            return 'group_bar'
        elif '公会' in message or 'ギルド' in message:
            return 'group_guild'
        elif '观光' in message or '観光' in message:
            return 'group_tourism'
        elif '职业' in message or 'Achievement' in message:
            return 'group_game'
        elif '村' in message and ('開' in message or '开' in message):
            return 'group_village'
        else:
            # その他のメッセージは先頭20文字のハッシュでグループ化
            prefix = message[:20] if len(message) > 20 else message
            group_hash = hashlib.md5(prefix.encode()).hexdigest()[:8]
            return f'group_other_{group_hash}'
    
    @staticmethod
    def get_default_group_name(group_id: str) -> str:
        """デフォルトのグループ名を取得"""
        return DEFAULT_GROUP_NAMES.get(group_id, f'📌 その他 ({group_id[-8:]})')
    
    @staticmethod
    def organize_notifications_by_group(
        notifications: List[NotificationData],
        group_names: dict
    ) -> dict:
        """通知をグループごとに整理"""
        groups = {}
        
        for notif in notifications:
            group_id = notif.group_id
            
            if group_id not in groups:
                groups[group_id] = {
                    'id': group_id,
                    'name': group_names.get(
                        group_id,
                        GroupUtils.get_default_group_name(group_id)
                    ),
                    'messages': []
                }
            
            groups[group_id]['messages'].append(notif)
        
        return groups


class ExportUtils:
    """エクスポート処理に関するユーティリティ"""
    
    @staticmethod
    def export_to_json(groups: dict, messages: List[NotificationData]) -> dict:
        """JSON形式でエクスポート用のデータを作成"""
        return {
            'groups': {
                gid: {
                    'name': ginfo['name'],
                    'message_count': len(ginfo['messages'])
                } for gid, ginfo in groups.items()
            },
            'messages': [m.to_dict() for m in messages]
        }
    
    @staticmethod
    def export_to_text(groups: dict, messages: List[NotificationData]) -> str:
        """テキスト形式でエクスポート用のデータを作成"""
        lines = []
        
        for group_id, group_info in sorted(
            groups.items(),
            key=lambda x: len(x[1]['messages']),
            reverse=True
        ):
            group_messages = [m for m in messages if m.group_id == group_id]
            if group_messages:
                lines.append(f"\n{'='*70}")
                lines.append(f"グループ: {group_info['name']} ({len(group_messages)} 件)")
                lines.append(f"{'='*70}\n")
                
                for notif in sorted(group_messages, key=lambda x: x.date):
                    lines.append(f"受信日時: {notif.date}")
                    lines.append(f"作成日時: {notif.created_at}")
                    lines.append(f"メッセージ:\n{notif.message}")
                    lines.append(f"{'-'*70}\n")
        
        return '\n'.join(lines)
