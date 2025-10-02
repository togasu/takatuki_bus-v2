#!/usr/bin/env python3
"""
Favicon generator for Sojo Bus Admin system
バス管理システム用のfaviconファイルを生成します
"""

from PIL import Image, ImageDraw
import os

def create_favicon():
    """バスアイコンのfaviconを作成"""
    
    # 32x32のベースサイズで作成
    size = 32
    img = Image.new('RGBA', (size, size), (13, 110, 253, 255))  # Bootstrap primary blue
    draw = ImageDraw.Draw(img)
    
    # バス本体 (白色の長方形)
    bus_width = 20
    bus_height = 12
    bus_x = (size - bus_width) // 2
    bus_y = 10
    draw.rounded_rectangle(
        [bus_x, bus_y, bus_x + bus_width, bus_y + bus_height],
        radius=2,
        fill=(255, 255, 255, 255)
    )
    
    # 窓 (3つの青い長方形)
    window_width = 4
    window_height = 3
    window_y = bus_y + 2
    
    # 左の窓
    draw.rectangle(
        [bus_x + 2, window_y, bus_x + 2 + window_width, window_y + window_height],
        fill=(13, 110, 253, 255)
    )
    
    # 中央の窓
    draw.rectangle(
        [bus_x + 8, window_y, bus_x + 8 + window_width, window_y + window_height],
        fill=(13, 110, 253, 255)
    )
    
    # 右の窓
    draw.rectangle(
        [bus_x + 14, window_y, bus_x + 14 + window_width, window_y + window_height],
        fill=(13, 110, 253, 255)
    )
    
    # タイヤ (2つの白い円)
    tire_radius = 2
    tire_y = bus_y + bus_height + 2
    
    # 左のタイヤ
    left_tire_x = bus_x + 4
    draw.ellipse(
        [left_tire_x - tire_radius, tire_y - tire_radius, 
         left_tire_x + tire_radius, tire_y + tire_radius],
        fill=(255, 255, 255, 255)
    )
    # タイヤの中心
    draw.ellipse(
        [left_tire_x - 1, tire_y - 1, left_tire_x + 1, tire_y + 1],
        fill=(13, 110, 253, 255)
    )
    
    # 右のタイヤ
    right_tire_x = bus_x + 16
    draw.ellipse(
        [right_tire_x - tire_radius, tire_y - tire_radius,
         right_tire_x + tire_radius, tire_y + tire_radius],
        fill=(255, 255, 255, 255)
    )
    # タイヤの中心
    draw.ellipse(
        [right_tire_x - 1, tire_y - 1, right_tire_x + 1, tire_y + 1],
        fill=(13, 110, 253, 255)
    )
    
    # ドア
    door_width = 2
    door_height = 5
    door_x = bus_x + 9
    door_y = bus_y + bus_height - door_height
    draw.rectangle(
        [door_x, door_y, door_x + door_width, door_y + door_height],
        fill=(13, 110, 253, 255)
    )
    
    return img

def main():
    """メイン処理"""
    # staticディレクトリのパス
    static_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'images')
    os.makedirs(static_dir, exist_ok=True)
    
    # ベース画像を作成
    base_img = create_favicon()
    
    # 各サイズのfaviconを生成
    sizes = {
        'favicon.ico': 16,
        'favicon-16x16.png': 16,
        'favicon-32x32.png': 32,
        'apple-touch-icon.png': 180
    }
    
    for filename, size in sizes.items():
        # サイズを調整
        if size != 32:
            resized_img = base_img.resize((size, size), Image.Resampling.LANCZOS)
        else:
            resized_img = base_img
        
        # ファイルパス
        filepath = os.path.join(static_dir, filename)
        
        # ICOファイルの場合は特別な処理
        if filename.endswith('.ico'):
            resized_img.save(filepath, format='ICO', sizes=[(16, 16)])
        else:
            resized_img.save(filepath, format='PNG')
        
        print(f"Created: {filepath}")
    
    print("Favicon generation completed!")

if __name__ == "__main__":
    main()