#!/usr/bin/env python
"""バスデータを確認するスクリプト"""
import sys
sys.path.insert(0, '/app')

from app import create_app
from app.database import db
from app.models import Bus
from datetime import datetime

app = create_app()

with app.app_context():
    # 1号車の今後のバスを確認
    buses = Bus.query.filter(
        Bus.busid == 1, 
        Bus.departure_time > datetime.now()
    ).order_by(Bus.departure_time).limit(5).all()
    
    print(f'Found {len(buses)} buses for busid=1')
    for b in buses:
        print(f'  Bus ID: {b.id}, Departure: {b.departure_time}, Seats: {b.seats}, UD: {b.ud}')
    
    # 全てのバスの数を確認
    all_buses = Bus.query.all()
    print(f'\nTotal buses in database: {len(all_buses)}')
    
    # 今後のバス（全号車）
    future_buses = Bus.query.filter(
        Bus.departure_time > datetime.now()
    ).order_by(Bus.departure_time).limit(10).all()
    print(f'\nFuture buses (all numbers): {len(future_buses)}')
    for b in future_buses:
        print(f'  Bus {b.busid}, Departure: {b.departure_time}')
