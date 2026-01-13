"""
SQLiteデータをPostgreSQLに移行するスクリプト
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

# SQLiteデータベースのパス
SQLITE_DB = 'instance/student.db'

# PostgreSQL接続情報
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_DB = os.getenv('POSTGRES_DB', 'mydb')
PG_USER = os.getenv('POSTGRES_USER', 'user')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')

def migrate_table(sqlite_cursor, pg_cursor, table_name):
    """特定のテーブルのデータを移行"""
    print(f"\n移行中: {table_name}")
    
    # SQLiteからデータを取得
    sqlite_cursor.execute(f'SELECT * FROM {table_name}')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  {table_name}: データなし")
        return
    
    # カラム名を取得
    columns = [description[0] for description in sqlite_cursor.description]
    
    # PostgreSQLにデータを挿入
    if table_name == 'Reservation':
        # Reservationテーブルは"で囲む必要がある
        insert_query = f'INSERT INTO "{table_name}" ({", ".join(columns)}) VALUES %s ON CONFLICT DO NOTHING'
    else:
        insert_query = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES %s ON CONFLICT DO NOTHING'
    
    try:
        execute_values(pg_cursor, insert_query, rows)
        print(f"  {table_name}: {len(rows)}件のレコードを移行しました")
    except Exception as e:
        print(f"  {table_name}: エラー - {e}")
        raise

def main():
    """メイン処理"""
    print("=== SQLiteからPostgreSQLへのデータ移行 ===")
    
    # SQLite接続
    if not os.path.exists(SQLITE_DB):
        print(f"エラー: SQLiteデータベース '{SQLITE_DB}' が見つかりません")
        return
    
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    # PostgreSQL接続
    try:
        pg_conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"PostgreSQL接続エラー: {e}")
        sqlite_conn.close()
        return
    
    # 移行するテーブルのリスト（依存関係順）
    tables = [
        'user',
        'semester',
        'bus',
        'seat',
        'Reservation',
        'cancel',
        'user_penalty',
        'last_semester_user',
        'semester_transition',
        'penalty_reservation',
        'test_model'
    ]
    
    try:
        for table in tables:
            # テーブルが存在するか確認
            sqlite_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if sqlite_cursor.fetchone():
                migrate_table(sqlite_cursor, pg_cursor, table)
            else:
                print(f"\n{table}: SQLiteに存在しません（スキップ）")
        
        # コミット
        pg_conn.commit()
        print("\n=== 移行完了 ===")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == '__main__':
    main()
