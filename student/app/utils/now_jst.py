from datetime import datetime, timezone, timedelta

# JST (Japan Standard Time) timezone
JST = timezone(timedelta(hours=9))

def now_jst():
    """現在のJST時刻を取得"""
    return datetime.now(JST)
