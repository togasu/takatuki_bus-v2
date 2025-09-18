from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging
import psycopg2
from psycopg2 import sql
import sys
import traceback

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

import logging
import sys
import traceback

# ログ設定
logger = logging.getLogger(__name__)

def create_app():
    try:
        logger.info("=== Admin Service App Creation Started ===")
        
        app = Flask(__name__)
        logger.info("Flask app instance created")

        # Flask設定
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'admin-secret-key-change-in-production-2024')
        logger.info("Flask secret key configured")

        # ログ設定
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, "access.log"),
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )
        logger.info("Logging configured")

        @app.before_request
        def log_request_info():
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            path = request.path
            logging.info(f"IP: {ip} - Path: /admin{path}")

        # DB設定
        app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
        app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
        app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
        app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
        app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")
        logger.info("Database configuration loaded")

        # データベース初期化
        logger.info("Initializing database...")
        from app.database import init_db
        init_db(app)
        logger.info("Database initialized")

        # マイグレーション実行
        logger.info("Performing migration...")
        with app.app_context():
            perform_migration(app)
        logger.info("Migration completed")

        # モデルをインポート（マイグレーションで必要）
        logger.info("Importing models...")
        from app import models
        logger.info("Models imported")

        # モデルに定義されたBlueprintを自動登録
        logger.info("Registering model blueprints...")
        models.register_model_blueprints(app)
        logger.info("Model blueprints registered")

        logger.info("Registering route blueprints...")
        from app import routes
        routes.register_blueprints(app)
        logger.info("Route blueprints registered")
        # エラーハンドラーを登録
        logger.info("Registering error handlers...")
        from app.utils.error_handlers import register_error_handlers
        register_error_handlers(app)
        logger.info("Error handlers registered")

        # デバッグ用：登録されているルートを表示
        def debug_routes():
            print("=== 登録されているルート ===")
            for rule in app.url_map.iter_rules():
                methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
                print(f"{rule.endpoint}: {rule.rule} [{', '.join(methods)}]")
                
                # login関連のルートを特に詳しく表示
                if 'login' in rule.rule.lower() or 'login' in rule.endpoint.lower():
                    print(f"  *** LOGIN ROUTE DETECTED ***")
                    print(f"  Endpoint: {rule.endpoint}")
                    print(f"  Rule: {rule.rule}")
                    print(f"  Methods: {rule.methods}")
                    print(f"  Defaults: {rule.defaults}")
            print("========================")
        
        # アプリケーション起動時にルートをデバッグ表示
        with app.app_context():
            debug_routes()

        logger.info("Initializing SocketIO...")
        socketio.init_app(app)
        logger.info("SocketIO initialized")
        
        logger.info("=== Admin Service App Creation Completed Successfully ===")
        return app
        
    except Exception as e:
        logger.error(f"=== Admin Service App Creation Failed ===")
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

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
            'users': {
                'id': 'integer',
                'username': 'character varying(80)',
                'email': 'character varying(120)',
                'password_hash': 'character varying(255)',
                'password_salt': 'character varying(255)',
                'role': 'character varying(20)',
                'is_active': 'boolean',
                'last_login': 'timestamp without time zone',
                'created_at': 'timestamp without time zone',
                'updated_at': 'timestamp without time zone'
            },
            'permissions': {
                'id': 'integer',
                'resource': 'character varying(100)',
                'action': 'character varying(50)',
                'role': 'character varying(20)',
                'is_allowed': 'boolean',
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
            
            result = cursor.fetchone()
            table_exists = result[0] if result else False
            
            if not table_exists:
                migration_needed = True
                migration_reasons.append(f"テーブル '{table_name}' が存在しません")
                logging.info(f"Admin service: Table '{table_name}' does not exist")
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
                    logging.info(f"Admin service: Column '{expected_col}' missing in table '{table_name}'")
                elif not _is_compatible_type(existing_columns[expected_col], expected_type):
                    migration_needed = True
                    migration_reasons.append(f"テーブル '{table_name}' のカラム '{expected_col}' の型が期待値と異なります (実際: {existing_columns[expected_col]}, 期待: {expected_type})")
                    logging.info(f"Admin service: Column '{expected_col}' in table '{table_name}' has wrong type: {existing_columns[expected_col]} (expected: {expected_type})")
        
        # マイグレーションが必要かどうかの判定
        if migration_needed:
            logging.info("Admin service: Migration needed. Reasons:")
            for reason in migration_reasons:
                logging.info(f"  - {reason}")
            
            # マイグレーション実行
            if os.path.exists('migrations/env.py'):
                logging.info("Admin service: Executing Flask-Migrate upgrade...")
                try:
                    # Flask-Migrateが利用可能かチェック
                    import importlib.util
                    spec = importlib.util.find_spec("flask_migrate")
                    if spec is not None:
                        from flask_migrate import upgrade
                        upgrade()
                        logging.info("Admin service: Migration completed successfully via Flask-Migrate")
                    else:
                        logging.warning("Admin service: Flask-Migrate not installed. Falling back to direct table creation...")
                        _create_tables_directly(app)
                except Exception as e:
                    logging.warning(f"Admin service: Flask-Migrate failed: {e}. Falling back to direct table creation...")
                    _create_tables_directly(app)
            else:
                logging.info("Admin service: No migration files found. Creating tables directly...")
                _create_tables_directly(app)
        else:
            logging.info("Admin service: Database schema is up to date. No migration needed.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logging.error(f"Admin service: Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Admin service: Migration error: {e}")
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
            # データベースの変更をコミット
            db.session.commit()
            logging.info("Admin service: Tables created successfully using SQLAlchemy")
            
            # 少し待機してからデフォルトデータを挿入
            import time
            time.sleep(1)
            
            # 初期権限データを挿入
            _insert_default_permissions()
            
    except Exception as e:
        logging.error(f"Admin service: Direct table creation failed: {e}")
        raise

def _insert_default_permissions():
    """デフォルトの権限データを挿入"""
    try:
        from app.database import db
        from app.models.permission import Permission
        
        # テーブルが存在することを確認
        try:
            # シンプルなクエリでテーブルの存在を確認
            Permission.query.first()
        except Exception as e:
            logging.warning(f"Admin service: Permissions table not ready yet: {e}")
            return
        
        # デフォルト権限の定義
        default_permissions = [
            # 管理者用権限
            ('admin_user', 'create', 'admin', True),
            ('admin_user', 'read', 'admin', True),
            ('admin_user', 'update', 'admin', True),
            ('admin_user', 'delete', 'admin', True),
            ('permission', 'create', 'admin', True),
            ('permission', 'read', 'admin', True),
            ('permission', 'update', 'admin', True),
            ('permission', 'delete', 'admin', True),
            ('system', 'manage', 'admin', True),
            
            # 一般ユーザー用権限
            ('admin_user', 'read', 'normal', True),
            ('permission', 'read', 'normal', True),
            
            # ゲスト用権限（制限あり）
            ('admin_user', 'read', 'guest', False),
            ('permission', 'read', 'guest', False),
        ]
        
        # 既存の権限をチェックして重複を避ける
        for resource, action, role, is_allowed in default_permissions:
            try:
                existing = Permission.query.filter_by(
                    resource=resource, 
                    action=action, 
                    role=role
                ).first()
                
                if not existing:
                    permission = Permission(
                        resource=resource,
                        action=action,
                        role=role,
                        is_allowed=is_allowed
                    )
                    db.session.add(permission)
            except Exception as e:
                logging.warning(f"Admin service: Failed to check/insert permission {resource}.{action}.{role}: {e}")
                continue
        
        try:
            db.session.commit()
            logging.info("Admin service: Default permissions inserted successfully")
        except Exception as e:
            logging.warning(f"Admin service: Failed to commit default permissions: {e}")
            db.session.rollback()
        
    except Exception as e:
        logging.warning(f"Admin service: Failed to insert default permissions: {e}")
        try:
            from app.database import db
            db.session.rollback()
        except:
            pass  # セッションが無効な場合は無視
