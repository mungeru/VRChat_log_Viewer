# lib/ フォルダ - モジュール構成

このフォルダには VRChat ログビューアーのすべてのモジュールが含まれています。

## 📁 ファイル一覧

### メインアプリケーション
- **vrchat_log_viewer.py** - メインアプリケーションクラス（VRChatLogViewer）

### UI関連
- **ui_builder.py** - UI構築ヘルパー
- **virtual_treeview.py** - 仮想レンダリング対応Treeview（高速化）
- **theme_manager.py** - テーマ管理システム
- **progress_dialog.py** - 読み込み進捗ダイアログ

### データ処理
- **async_loader.py** - 非同期ファイル読み込み
- **utils.py** - ユーティリティ関数（ファイル操作、パース処理など）
- **models.py** - データモデル（LogInfo, NotificationData, GroupInfo）

### 設定・定数
- **constants.py** - 定数定義（パス、色設定、パターンなど）

### 拡張機能
- **plugin_manager.py** - プラグインシステム

---

## 🚫 注意事項

**このフォルダ内のファイルを直接編集しないでください**

- すべてのファイルはアプリケーションの起動に必要です
- ファイルを削除したり移動したりしないでください
- カスタマイズはプラグインシステムを使用してください

---

## 📚 各モジュールの役割

### vrchat_log_viewer.py
メインアプリケーションクラス。すべての機能を統括。

### virtual_treeview.py（v2.1の新機能）
10万行のログを0.1秒で表示する仮想レンダリング機能。
見えている範囲だけを描画することで超高速化を実現。

### async_loader.py
大きなファイルを別スレッドで読み込み、UIをフリーズさせない。

### utils.py
共通処理をまとめたユーティリティ：
- FileUtils: ファイル読み込み
- LogParser: ログ解析
- NotificationParser: 通知抽出
- GroupUtils: グループ管理
- ExportUtils: エクスポート処理

### models.py
データクラス定義：
- LogInfo: ログ行のデータ
- NotificationData: 通知データ
- GroupInfo: グループ情報

### constants.py
アプリケーション全体で使用する定数。

### ui_builder.py
UI構築のヘルパー関数。メニュー、ツールバー、パネルなどを構築。

### theme_manager.py
テーマシステム。5種類のプリセットテーマとカスタマイズ機能。

### plugin_manager.py
プラグインシステム。機能を拡張するための仕組み。

### progress_dialog.py
ファイル読み込み時に表示される進捗ダイアログ。

---

**VRChat ログビューアー v2.1**  
すべてのファイルが正しく配置されていれば、自動的に連携して動作します。
