#!/usr/bin/env python3
"""
ドライバーテストユーザー作成スクリプト
"""

import sys
import os
sys.path.insert(0, '/app')

def create_test_driver():
    """テスト用ドライバーを作成"""
    try:
        from app import create_app
        from app.models import Driver
        from app.database import db
        
        app = create_app()
        
        with app.app_context():
            # テストドライバーの情報
            test_drivers = [
                {'username': 'driver1', 'number': 1, 'password': 'driver123'},
                {'username': 'driver2', 'number': 2, 'password': 'driver123'},
                {'username': 'driver3', 'number': 3, 'password': 'driver123'},
            ]
            
            for driver_data in test_drivers:
                # 既存のドライバーをチェック
                existing = Driver.query.filter_by(username=driver_data['username']).first()
                
                if existing:
                    print(f"Driver {driver_data['username']} already exists, updating password...")
                    existing.set_password(driver_data['password'])
                    db.session.commit()
                    print(f"✅ Updated driver: {driver_data['username']}")
                else:
                    # 新しいドライバーを作成
                    driver = Driver()
                    driver.username = driver_data['username']
                    driver.number = driver_data['number']
                    driver.set_password(driver_data['password'])
                    
                    db.session.add(driver)
                    db.session.commit()
                    print(f"✅ Created driver: {driver_data['username']} (number: {driver_data['number']})")
            
            # 作成されたドライバーを確認
            all_drivers = Driver.query.all()
            print(f"\n📊 Total drivers in database: {len(all_drivers)}")
            for driver in all_drivers:
                print(f"  - {driver.username} (number: {driver.number}, active: {driver.is_active})")
                
    except Exception as e:
        print(f"Error creating test driver: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_test_driver()
