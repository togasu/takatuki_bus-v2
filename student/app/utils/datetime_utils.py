from datetime import datetime

def process_datetime_input(datetime_str):
    """時間の処理"""
    try:
        parts = datetime_str.split(' ')
        date_parts = parts[0].split('/')
        month = int(date_parts[0])
        day = int(date_parts[1])
        time_str = parts[1]

        current_year = datetime.now().year
        current_month = datetime.now().month

        if current_month > 9 and month <= 9:
            current_year += 1

        bus_time_object = datetime(current_year, month, day, int(time_str.split(':')[0]), int(time_str.split(':')[1]))
        return bus_time_object
    except (ValueError, IndexError):
        raise ValueError("日時の入力形式が無効です。")

def string_to_datetime(value):
    """文字列を日時に変換"""
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

def datetime_format(value, format='%Y-%m-%d %H:%M:%S'):
    """日時をフォーマット"""
    return value.strftime(format)
