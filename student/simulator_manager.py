#!/usr/bin/env python3
"""
予約シミュレーター管理スクリプト (Linux専用)

Dockerコンテナ内でバックグラウンドでシミュレーターを起動・停止する
"""

import os
import sys
import time
import subprocess
import signal

SIMULATOR_SCRIPT = "auto_reservation_simulator.py"
PID_FILE = "/tmp/reservation_simulator.pid"
LOG_FILE = "/app/logs/reservation_simulator.log"

def log(message):
    """ログ出力"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🎛️  Manager: {message}")

def is_simulator_running():
    """シミュレーターが実行中かチェック"""
    if not os.path.exists(PID_FILE):
        return False
        
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
            
        # /proc/<pid>の存在確認 (Linux)
        return os.path.exists(f"/proc/{pid}")
    except (ValueError, FileNotFoundError):
        return False

def start_simulator():
    """シミュレーター開始"""
    if is_simulator_running():
        log("⚠️  シミュレーターは既に実行中です")
        return False
        
    try:
        # ログディレクトリを作成
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # シミュレーターをバックグラウンドで開始
        with open(LOG_FILE, 'w') as log_file:
            env = os.environ.copy()
            env['SIMULATOR_CYCLE_SECONDS'] = '120'  # デバッグ用: 2分サイクル
            
            process = subprocess.Popen(
                [sys.executable, SIMULATOR_SCRIPT],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env
            )
            
        # PIDを保存
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
            
        log(f"🚀 シミュレーター開始 (PID: {process.pid})")
        log(f"📝 ログファイル: {LOG_FILE}")
        log(f"⚡ デバッグモード: 2分サイクル")
        return True
        
    except Exception as e:
        log(f"❌ シミュレーター開始エラー: {e}")
        return False

def stop_simulator():
    """シミュレーター停止"""
    if not is_simulator_running():
        log("ℹ️  シミュレーターは実行されていません")
        return False
        
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
            
        # プロセスを停止
        os.kill(pid, signal.SIGTERM)
        
        # 停止を待機
        for _ in range(10):
            if not is_simulator_running():
                break
            time.sleep(1)
        else:
            # 強制停止
            try:
                os.kill(pid, signal.SIGTERM)
                log("⚡ 強制停止しました")
            except:
                pass
                
        # PIDファイルを削除
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            
        log(f"🛑 シミュレーター停止 (PID: {pid})")
        return True
        
    except Exception as e:
        log(f"❌ シミュレーター停止エラー: {e}")
        return False

def get_status():
    """シミュレーターの状態を取得"""
    if is_simulator_running():
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        log(f"✅ シミュレーター実行中 (PID: {pid})")
        
        # ログファイルの最後の数行を表示
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-5:] if len(lines) >= 5 else lines
                    log("📋 最近のログ:")
                    for line in recent_lines:
                        print(f"   {line.strip()}")
            except:
                pass
    else:
        log("❌ シミュレーターは停止中です")

def show_help():
    """ヘルプ表示"""
    print("""
予約シミュレーター管理ツール

使用方法:
    python simulator_manager.py start   - シミュレーター開始
    python simulator_manager.py stop    - シミュレーター停止  
    python simulator_manager.py status  - 状態確認
    python simulator_manager.py restart - 再起動
    python simulator_manager.py help    - このヘルプを表示

機能:
    - 2分ごとに1-3件の予約を自動作成
    - 予約の80%が5分後に乗車済みに変更
    - 20%の確率でランダムキャンセル
    - 統計データのリアルタイム更新テスト
    
ログ: {LOG_FILE}
""")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_help()
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "start":
        start_simulator()
    elif command == "stop":
        stop_simulator()
    elif command == "status":
        get_status()
    elif command == "restart":
        log("🔄 シミュレーター再起動中...")
        stop_simulator()
        time.sleep(2)
        start_simulator()
    elif command == "help":
        show_help()
    else:
        log(f"❌ 不明なコマンド: {command}")
        show_help()
        sys.exit(1)