#!/usr/bin/env python3
"""
Student Service Migration Initialization Script
マイグレーション用のファイルを初期化
"""

import os
import sys
import time
from flask import Flask
from flask_migrate import Migrate, init, migrate as flask_migrate, upgrade

def init_migration():
    """マイグレーション環境を初期化"""
    
    # アプリケーションファクトリーを使用
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    
    # アプリケーション作成
    app = create_app()
    
    with app.app_context():
        # 全てのモデルがインポートされていることを確認
        from app import models
        print(f"Loaded models: {models.__all__}")
        
        # データベース接続確認
        from app.database import db
        try:
            # 簡単な接続テスト - データベースに接続できるかテスト
            db.create_all()
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
        
        # migrations フォルダが存在しない場合は初期化
        if not os.path.exists('migrations'):
            print("Initializing migration repository...")
            init()
            print("Migration repository initialized. Waiting for files to be created...")
            time.sleep(3)  # ファイル作成を待機
            
            # env.pyを正しい内容で上書き
            print("Configuring env.py...")
            env_py_path = 'migrations/env.py'
            env_py_content = """from __future__ import with_statement
import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option(
    'sqlalchemy.url',
    str(current_app.extensions['migrate'].db.get_engine().url).replace(
        '%', '%%'))
target_metadata = current_app.extensions['migrate'].db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    \\\"\\\"\\\"Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    \\\"\\\"\\\"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    \\\"\\\"\\\"Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    \\\"\\\"\\\"

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    connectable = current_app.extensions['migrate'].db.get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
            with open(env_py_path, 'w', encoding='utf-8') as f:
                f.write(env_py_content)
            print("env.py configured successfully")
        
        # env.pyファイルが存在することを確認してからマイグレーション作成
        if os.path.exists('migrations/env.py'):
            print("Creating initial migration...")
            flask_migrate(message='Initial migration for student service')
            print("Applying migrations to database...")
            upgrade()
            print("Migration completed successfully!")
        else:
            print("Warning: Migration repository not properly initialized. Skipping migration creation.")
            return False
        
        print("Student service migration initialization completed!")
        return True

if __name__ == "__main__":
    success = init_migration()
    if success:
        print("Migration initialization completed successfully")
    else:
        print("Migration initialization failed, but continuing...")
    # Always exit with success to allow the server to start
    sys.exit(0)
