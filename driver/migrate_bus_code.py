#!/usr/bin/env python3
"""
BusCodeテーブルを追加するマイグレーションスクリプト
"""

import os
import sys
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_bus_code_table():
    """bus_codesテーブルを作成"""
    try:
        logger.info("Importing app modules...")
        from app import create_app
        from app.database import db
        from app.models import BusCode
        
        logger.info("Creating Flask application...")
        app = create_app()
        
        with app.app_context():
            logger.info("Creating bus_codes table...")
            
            # テーブルが既に存在するか確認
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'bus_codes' in inspector.get_table_names():
                logger.info("bus_codes table already exists.")
                return
            
            # BusCodeテーブルを作成
            BusCode.__table__.create(db.engine, checkfirst=True)
            logger.info("bus_codes table created successfully.")
            
    except Exception as e:
        logger.error(f"Error creating bus_codes table: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    create_bus_code_table()
