"""デバイス認証ユーティリティ - MACアドレスベースの認証"""
from flask import request
import re
import logging

logger = logging.getLogger(__name__)


def get_client_mac_address():
    """
    クライアントのMACアドレスを取得
    
    注意: ブラウザから直接MACアドレスを取得することはできないため、
    以下のいずれかの方法で対応する必要があります：
    
    1. カスタムヘッダー方式（推奨）:
       クライアント側のJavaScriptやアプリから X-Device-MAC ヘッダーでMACアドレスを送信
       
    2. Cookie方式:
       初回登録時にMACアドレスをCookieに保存し、以降の認証で使用
       
    3. ネットワーク層での取得（制限あり）:
       サーバー側でARP/DHCP情報から取得（同一ネットワーク内のみ）
    
    Returns:
        str: MACアドレス (XX:XX:XX:XX:XX:XX形式) または None
    """
    # 方法1: カスタムヘッダーから取得
    mac_from_header = request.headers.get('X-Device-MAC')
    if mac_from_header:
        logger.info(f"MAC address from header: {mac_from_header}")
        return normalize_mac_address(mac_from_header)
    
    # 方法2: Cookieから取得
    mac_from_cookie = request.cookies.get('device_mac')
    if mac_from_cookie:
        logger.info(f"MAC address from cookie: {mac_from_cookie}")
        return normalize_mac_address(mac_from_cookie)
    
    # 方法3: フォームデータから取得（デバッグ/開発用）
    mac_from_form = request.form.get('device_mac') or request.args.get('device_mac')
    if mac_from_form:
        logger.info(f"MAC address from form/query: {mac_from_form}")
        return normalize_mac_address(mac_from_form)
    
    logger.warning("No MAC address found in request")
    return None


def normalize_mac_address(mac: str) -> str:
    """
    MACアドレスを正規化 (XX:XX:XX:XX:XX:XX形式)
    
    Args:
        mac: MACアドレス文字列（様々な形式に対応）
        
    Returns:
        str: 正規化されたMACアドレス
        
    Raises:
        ValueError: 不正なMACアドレス形式の場合
    """
    if not mac:
        raise ValueError("MAC address is required")
    
    # ハイフン、コロン、スペースを削除
    mac = mac.replace('-', '').replace(':', '').replace(' ', '').upper()
    
    # 12桁の16進数であることを確認
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address length: {mac}")
    
    # 有効な16進数文字のみか確認
    if not re.match(r'^[0-9A-F]{12}$', mac):
        raise ValueError(f"Invalid MAC address format: {mac}")
    
    # コロン区切りの形式に変換
    return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])


def validate_device_access(driver_id: int, mac_address: str = None) -> tuple:
    """
    デバイスアクセスを検証
    
    Args:
        driver_id: ドライバーID
        mac_address: MACアドレス（指定がない場合はリクエストから自動取得）
        
    Returns:
        tuple: (認証成功/失敗, メッセージ, デバイス情報)
    """
    from app.models import DriverDevice
    from app.database import db
    
    # MACアドレスを取得
    if not mac_address:
        mac_address = get_client_mac_address()
    
    if not mac_address:
        return False, "デバイス情報が取得できません", None
    
    try:
        # MACアドレスを正規化
        normalized_mac = normalize_mac_address(mac_address)
        
        # 登録済みデバイスか確認
        device = DriverDevice.query.filter_by(
            driver_id=driver_id,
            mac_address=normalized_mac,
            is_active=True
        ).first()
        
        if not device:
            logger.warning(f"Unregistered device attempt - Driver ID: {driver_id}, MAC: {normalized_mac}")
            return False, "このデバイスは登録されていません", None
        
        # 最終使用日時を更新
        device.update_last_used()
        db.session.commit()
        
        logger.info(f"Device authenticated - Driver ID: {driver_id}, Device: {device.device_name}, MAC: {normalized_mac}")
        return True, "認証成功", device
        
    except ValueError as e:
        logger.error(f"MAC address validation error: {e}")
        return False, f"MACアドレスが不正です: {str(e)}", None
    except Exception as e:
        logger.error(f"Device validation error: {e}")
        return False, "デバイス認証中にエラーが発生しました", None


def require_device_auth(driver_id: int):
    """
    デバイス認証デコレーター用のヘルパー関数
    
    Args:
        driver_id: ドライバーID
        
    Returns:
        bool: 認証成功時True
        
    Raises:
        PermissionError: 認証失敗時
    """
    success, message, device = validate_device_access(driver_id)
    if not success:
        raise PermissionError(message)
    return True


def get_device_mac_from_request_context():
    """
    現在のリクエストコンテキストからMACアドレスを取得
    複数の取得方法を試行
    """
    methods = [
        ('header', lambda: request.headers.get('X-Device-MAC')),
        ('cookie', lambda: request.cookies.get('device_mac')),
        ('form', lambda: request.form.get('device_mac')),
        ('query', lambda: request.args.get('device_mac')),
    ]
    
    for method_name, getter in methods:
        try:
            mac = getter()
            if mac:
                logger.debug(f"MAC address obtained from {method_name}: {mac}")
                return normalize_mac_address(mac)
        except Exception as e:
            logger.debug(f"Error getting MAC from {method_name}: {e}")
            continue
    
    return None
