#!/usr/bin/env python3
"""
Favicon生成スクリプト
icon.pngから複数サイズのfaviconを生成します
"""

from PIL import Image
import os

def generate_favicons():
    """icon.pngから複数サイズのfaviconを生成"""
    
    # 入力画像パス
    input_path = os.path.join("app", "static", "images", "icon.png")
    
    # 出力ディレクトリ
    output_dir = os.path.join("app", "static", "images")
    
    # ファイルの存在確認
    if not os.path.exists(input_path):
        print(f"Error: {input_path} が見つかりません")
        return False
    
    try:
        # 元画像を開く
        with Image.open(input_path) as img:
            # RGBAモードに変換（透明度サポート）
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            print(f"元画像サイズ: {img.size}")
            
            # 生成するfaviconサイズ
            sizes = [
                (16, 16, "favicon-16x16.png"),
                (32, 32, "favicon-32x32.png"),
                (180, 180, "apple-touch-icon.png")
            ]
            
            for width, height, filename in sizes:
                # 画像をリサイズ
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # 出力パス
                output_path = os.path.join(output_dir, filename)
                
                # 保存
                resized.save(output_path, "PNG", optimize=True)
                print(f"生成完了: {output_path} ({width}x{height})")
            
            # favicon.icoも生成（複数サイズを含む）
            ico_path = os.path.join(output_dir, "favicon.ico")
            
            # ICO用のサイズ（16x16, 32x32）
            ico_images = []
            for size in [16, 32]:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                ico_images.append(resized)
            
            # ICOファイルとして保存
            ico_images[0].save(ico_path, format='ICO', sizes=[(16, 16), (32, 32)])
            print(f"生成完了: {ico_path}")
            
            print("\nfavicon生成が完了しました！")
            return True
            
    except Exception as e:
        print(f"Error: favicon生成中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    print("=== Favicon生成スクリプト ===")
    print("icon.pngから複数サイズのfaviconを生成します...\n")
    
    success = generate_favicons()
    
    if success:
        print("\n✅ 全てのfaviconが正常に生成されました")
        print("\n生成されたファイル:")
        print("- favicon-16x16.png")
        print("- favicon-32x32.png")
        print("- apple-touch-icon.png")
        print("- favicon.ico")
    else:
        print("\n❌ favicon生成に失敗しました")