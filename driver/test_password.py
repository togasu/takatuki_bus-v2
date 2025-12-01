#!/usr/bin/env python3
"""パスワード検証テスト"""

from app import create_app
from app.models import Driver
from app.database import db

app = create_app()

with app.app_context():
    d = Driver.query.filter_by(username='driver1').first()
    if d:
        print(f'Username: {d.username}')
        print(f'Number: {d.number}')
        print(f'Password hash exists: {d.password is not None}')
        print(f'Password hash type: {type(d.password)}')
        print(f'Salt exists: {d.salt is not None}')
        print(f'Salt type: {type(d.salt)}')
        print(f'Verify "driver123": {d.verify_password("driver123")}')
        print(f'Verify "wrong": {d.verify_password("wrong")}')
        
        # デバッグ情報
        print(f'\nDebug info:')
        print(f'Password (first 20 chars): {str(d.password)[:20]}...')
        print(f'Salt (first 20 chars): {str(d.salt)[:20]}...')
    else:
        print('driver1 not found!')
