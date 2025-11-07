"""
ドライバーシステムのメインエントリーポイント

このファイルはリファクタリング後のドライバーシステムのエントリーポイントです。
従来の巨大なmain.pyから機能を分離し、以下の構造で整理されています：

- models/: データベースモデル
- routes/: ルーティング関数
- services/: ビジネスロジック
- utils/: ユーティリティ関数
- driver_initializer.py: アプリケーション初期化

互換性のため、元のdriver()関数は保持されています。
"""

from app.driver_initializer import create_driver_app, driver

# 互換性のための関数エクスポート
__all__ = ['driver', 'create_driver_app']

# 直接実行時の処理
if __name__ == '__main__':
    app = create_driver_app()
    app.run(debug=True, port=8080)