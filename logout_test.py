from flask import Flask, render_template_string, url_for

app = Flask(__name__)

# シンプルなログアウトページのテンプレート
LOGOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ログアウト - 管理システム</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .logout-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            padding: 40px;
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        
        .logout-icon {
            font-size: 64px;
            color: #ffc107;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }
        
        .logout-message {
            color: #666;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .success-badge {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            cursor: pointer;
            font-size: 14px;
            background: #007bff;
            color: white;
            margin: 10px;
        }
        
        .btn:hover {
            background: #0056b3;
            transform: translateY(-2px);
        }
        
        .timestamp {
            font-size: 12px;
            color: #adb5bd;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="logout-container">
        <div class="logout-icon">🌟</div>
        
        <h1>お疲れさまでした</h1>
        
        <div class="success-badge">
            正常にログアウトしました
        </div>
        
        <p class="logout-message">
            {{ username }}さん、今日もお疲れさまでした。<br>
            管理システムからログアウトしました。<br>
            セキュリティのため、セッション情報はすべて削除されました。
        </p>
        
        <a href="/" class="btn">
            ログインページに戻る
        </a>
        
        <div class="timestamp">
            ログアウト時刻: {{ logout_time }}
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return """
    <h1>管理システム - テスト用</h1>
    <p>ログアウト機能のテストページです。</p>
    <a href="/logout">ログアウト</a>
    """

@app.route("/logout")
def logout():
    """ログアウトページ（テスト用）"""
    from datetime import datetime
    
    # テスト用のユーザー名と時刻
    username = "テストユーザー"
    logout_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    
    return render_template_string(LOGOUT_TEMPLATE, 
                                username=username, 
                                logout_time=logout_time)

if __name__ == "__main__":
    print("ログアウトページテストサーバーを起動しています...")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    app.run(debug=True, host="0.0.0.0", port=5000)