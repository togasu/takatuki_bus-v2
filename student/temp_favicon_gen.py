from PIL import Image
import os

print("favicon生成を開始します...")

# icon.pngから各サイズのfaviconを生成
original = Image.open('app/static/images/icon.png')
print(f'元画像サイズ: {original.size}')

# RGBAモードに変換
original = original.convert('RGBA')

# 16x16 favicon
resized_16 = original.resize((16, 16), Image.Resampling.LANCZOS)
resized_16.save('app/static/images/favicon-16x16.png', 'PNG', optimize=True)
print("16x16 favicon作成完了")

# 32x32 favicon  
resized_32 = original.resize((32, 32), Image.Resampling.LANCZOS)
resized_32.save('app/static/images/favicon-32x32.png', 'PNG', optimize=True)
print("32x32 favicon作成完了")

# Apple touch icon
resized_180 = original.resize((180, 180), Image.Resampling.LANCZOS)
resized_180.save('app/static/images/apple-touch-icon.png', 'PNG', optimize=True)
print("Apple touch icon作成完了")

# .ico形式のfavicon
ico_images = []
for size in [(16, 16), (32, 32), (48, 48)]:
    resized = original.resize(size, Image.Resampling.LANCZOS)
    # 白背景と合成
    background = Image.new('RGB', size, (255, 255, 255))
    if resized.mode == 'RGBA':
        background.paste(resized, mask=resized.split()[-1])
    ico_images.append(background)

# .icoファイルを保存
ico_images[0].save('app/static/images/favicon.ico', format='ICO', 
                   sizes=[(16, 16), (32, 32), (48, 48)])
print("favicon.ico作成完了")

print("すべてのfavicon生成が完了しました!")