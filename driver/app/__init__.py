from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging
import psycopg2
from psycopg2 import sql

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    app = Flask(__name__)

    # ログ設定
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "access.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )

    @app.before_request
    def log_request_info():
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        path = request.path
        logging.info(f"IP: {ip} - Path: /driver{path}")

    # DB設定
    app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
    app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
    app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
    app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
    app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")

    # データベース初期化
    from app.database import init_db
    init_db(app)

    # マイグレーション実行
    with app.app_context():
        perform_migration(app)

    # モデルをインポート（マイグレーションで必要）
    from app import models

    # モデルに定義されたBlueprintを自動登録
    models.register_model_blueprints(app)

    from app import routes
    routes.register_blueprints(app)

    # エラーハンドラーを登録
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    socketio.init_app(app)
    return app

def perform_migration(app):
    """スマートマイグレーションを実行：テーブル構造の変更を検出して自動対応"""
    try:
        # データベース接続テスト
        conn = psycopg2.connect(
            host=app.config["POSTGRES_HOST"],
            database=app.config["POSTGRES_DB"],
            user=app.config["POSTGRES_USER"],
            password=app.config["POSTGRES_PASSWORD"]
        )
        cursor = conn.cursor()
        
        # 必要なテーブルとその期待される構造を定義
        expected_tables = {
            'drivers': {
                'id': 'integer',
                'driver_id': 'character varying(20)',
                'name': 'character varying(100)',
                'license_number': 'character varying(50)',
                'phone': 'character varying(20)',
                'email': 'character varying(120)',
                'is_active': 'boolean',
                'created_at': 'timestamp without time zone',
                'updated_at': 'timestamp without time zone'
            }
        }
        
        migration_needed = False
        migration_reasons = []
        
        # 各テーブルの存在と構造をチェック
        for table_name, expected_columns in expected_tables.items():
            # テーブルの存在確認
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                migration_needed = True
                migration_reasons.append(f"テーブル '{table_name}' が存在しません")
                logging.info(f"Driver service: Table '{table_name}' does not exist")
                continue
            
            # テーブルが存在する場合、カラム構造をチェック
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            existing_columns = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 期待されるカラムが存在するかチェック
            for expected_col, expected_type in expected_columns.items():
                if expected_col not in existing_columns:
                    migration_needed = True
                    migration_reasons.append(f"テーブル '{table_name}' にカラム '{expected_col}' が存在しません")
                    logging.info(f"Driver service: Column '{expected_col}' missing in table '{table_name}'")
                elif not _is_compatible_type(existing_columns[expected_col], expected_type):
                    migration_needed = True
                    migration_reasons.append(f"テーブル '{table_name}' のカラム '{expected_col}' の型が期待値と異なります")
                    logging.info(f"Driver service: Column '{expected_col}' in table '{table_name}' has wrong type")
        
        # マイグレーションが必要かどうかの判定
        if migration_needed:
            logging.info("Driver service: Migration needed. Reasons:")
            for reason in migration_reasons:
                logging.info(f"  - {reason}")
            
            # マイグレーション実行
            if os.path.exists('migrations/env.py'):
                logging.info("Driver service: Executing Flask-Migrate upgrade...")
                try:
                    from flask_migrate import upgrade
                    upgrade()
                    logging.info("Driver service: Migration completed successfully via Flask-Migrate")
                except Exception as e:
                    logging.warning(f"Driver service: Flask-Migrate failed: {e}. Falling back to direct table creation...")
                    _create_tables_directly(app)
            else:
                logging.info("Driver service: No migration files found. Creating tables directly...")
                _create_tables_directly(app)
        else:
            logging.info("Driver service: Database schema is up to date. No migration needed.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logging.error(f"Driver service: Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Driver service: Migration error: {e}")
        raise

def _is_compatible_type(actual_type, expected_type):
    """データ型の互換性をチェック"""
    # PostgreSQLの型エイリアスを正規化
    type_aliases = {
        'varchar': 'character varying',
        'int4': 'integer',
        'int': 'integer',
        'bool': 'boolean',
        'timestamp': 'timestamp without time zone',
        'timestamptz': 'timestamp with time zone'
    }
    
    # 実際の型を正規化
    normalized_actual = actual_type.lower()
    for alias, canonical in type_aliases.items():
        if normalized_actual.startswith(alias):
            normalized_actual = normalized_actual.replace(alias, canonical)
            break
    
    # 期待される型を正規化
    normalized_expected = expected_type.lower()
    for alias, canonical in type_aliases.items():
        if normalized_expected.startswith(alias):
            normalized_expected = normalized_expected.replace(alias, canonical)
            break
    
    # 文字列型の長さは無視して比較
    if 'character varying' in normalized_actual and 'character varying' in normalized_expected:
        return True
    
    return normalized_actual == normalized_expected

def _create_tables_directly(app):
    """SQLAlchemyを使用してテーブルを直接作成"""
    try:
        from app.database import db
        with app.app_context():
            db.create_all()
            logging.info("Driver service: Tables created successfully using SQLAlchemy")
            
    except Exception as e:
        logging.error(f"Driver service: Direct table creation failed: {e}")
        raise
