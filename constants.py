"""
VRChat ログビューアー - 定数定義

アプリケーション全体で使用する定数を定義
"""

from pathlib import Path
import os

# ==================== パス設定 ====================
DEFAULT_LOG_PATH_WINDOWS = Path(os.path.expanduser("~")) / "AppData" / "LocalLow" / "VRChat" / "VRChat"
GROUP_NAMES_FILE = Path("vrchat_group_names.json")

# ==================== 表示設定 ====================
LONG_LINE_THRESHOLD = 300  # 長い行を折りたたむ閾値（文字数）
GROUP_COLLAPSE_THRESHOLD = 3  # グループ化する最小行数

# ==================== パフォーマンス設定 ====================
BATCH_SIZE = 100  # バッチ処理のサイズ
AUTO_UPDATE_INTERVAL = 3000  # 自動更新間隔（ミリ秒）
LARGE_FILE_THRESHOLD_MB = 50  # 大容量ファイル警告の閾値（MB）

# ==================== エンコーディング設定 ====================
ENCODINGS = ['utf-8', 'utf-8-sig', 'cp932', 'shift-jis']

# ==================== UI設定 ====================
WINDOW_TITLE = "VRChat ログビューアー (改善版)"
WINDOW_GEOMETRY = "1400x800"

# ダークテーマの色設定
DARK_THEME = {
    'background': '#1e1e1e',
    'foreground': '#d4d4d4',
    'fieldbackground': '#1e1e1e',
    'heading_background': '#2d2d30',
    'heading_foreground': '#cccccc',
    'selected': '#094771',
    'group_header_bg': '#2d2d30',
    'group_header_fg': '#cccccc'
}

# ログレベルの色設定
LOG_COLORS = {
    'debug': '#6a9955',
    'info': '#4fc1ff',
    'warning': '#dcdcaa',
    'error': '#f48771',
    'notification': '#9cdcfe',
    'collapsed': '#858585'
}

# ==================== グループ名のデフォルト設定 ====================
DEFAULT_GROUP_NAMES = {
    'group_earthquake': '🔔 地震情報',
    'group_bar': '🍺 Bar/開店情報',
    'group_guild': '⚔️ ギルド/公会',
    'group_tourism': '🗺️ 観光部',
    'group_game': '🎮 ゲーム情報',
    'group_village': '🏘️ 村/開村情報'
}

# ==================== 正規表現パターン ====================
LOG_TIMESTAMP_PATTERN = r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+-\s+(.+)'
TAG_PATTERN = r'\[([\w\s]+)\]'
NOTIFICATION_PATTERN = (
    r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}).*?'
    r'Received Notification: <Notification[^>]*?'
    r'id: (not_[\w-]+)[^>]*?'
    r'created at: ([\d/]+ [\d:]+ \w+)[^>]*?'
    r'message: "(.+?)">'
)

# ==================== メッセージテンプレート ====================
ERROR_MESSAGES = {
    'folder_not_found': "指定されたログフォルダが存在しません:\n\n{path}\n\n正しいフォルダを選択してください。",
    'no_log_files': "指定されたフォルダにログファイルが見つかりません:\n\n{path}\n\nVRChatを起動してログを生成してください。",
    'large_file_warning': "ファイルサイズが {size:.1f}MB です。\n読み込みに時間がかかる可能性があります。\n続行しますか？",
    'read_error': "ファイルの読み込みに失敗しました:\n\n{filename}\n\nエラー: {error}",
    'export_error': "エクスポートに失敗しました:\n{error}",
    'folder_open_error': "フォルダを開けませんでした:\n{error}"
}

STATUS_MESSAGES = {
    'ready': '準備完了',
    'searching': '🔍 ログファイルを検索中...',
    'loading': '📂 読み込み中... {filename}',
    'reading': '📖 ファイルを読み込み中... ({size:.1f}MB)',
    'parsing': '🔄 行を解析中...',
    'extracting': '📨 グループメッセージを抽出中...',
    'displaying': '🎨 ログを表示中...',
    'completed': '✅ 読み込み完了: {filename} ({lines} 行, {messages} メッセージ)',
    'updated': '更新完了 ({time})',
    'no_folder': '❌ ログフォルダが見つかりません',
    'no_files': '⚠️ ログファイルが見つかりません',
    'error': '❌ エラー: {error}',
    'copied': '✅ {count} 行をコピーしました',
    'message_copied': '✅ メッセージをコピーしました',
    'detected': '✅ ログファイル {count} 個を検出',
    'cancelled': '読み込みをキャンセルしました',
    'binary_mode': '⚠️ バイナリモードで読み込み中...'
}

# ==================== キーボードショートカット ====================
SHORTCUTS = {
    'search': '<Control-f>',
    'reload': '<Control-r>',
    'reload_alt': '<F5>',
    'copy': '<Control-c>',
    'select_all': '<Control-a>',
    'clear_search': '<Escape>'
}

SHORTCUTS_HELP = """
キーボードショートカット:

Ctrl+F       検索にフォーカス
Ctrl+R / F5  再読み込み
Ctrl+C       選択したログをコピー
Ctrl+A       すべて選択
ESC          検索クリア

右クリック   コンテキストメニュー
ダブルクリック グループの展開/折りたたみ
"""

# ==================== バージョン情報 ====================
VERSION = "2.0"
ABOUT_TEXT = f"""
VRChat ログビューアー (改善版)
Version {VERSION}

主な機能:
• ログファイルの表示とフィルタリング
• グループメッセージの抽出と管理
• 自動更新機能
• キーボードショートカット対応
• コピー機能（読み取り専用）
• ダークテーマ対応

改善点:
✓ エラーハンドリングの強化
✓ パフォーマンスの最適化
✓ キーボードショートカット追加
✓ コピー機能追加（読み取り専用）
✓ コードの整理とリファクタリング
✓ 型ヒントの追加
✓ モジュール化による負荷分散
"""
