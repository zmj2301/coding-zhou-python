import os
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 60)
    print("图片转PDF工具")
    print("=" * 60)
    
    try:
        from PIL import Image
        print("✓ Pillow 已加载")
    except ImportError:
        print("错误: 请先安装 Pillow: pip install Pillow")
        return
    
    input_dir = r"E:\桌面\P19-29"
    output_dir = os.path.join(input_dir, "output")
    
    print(f"\n输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ 已创建输出目录")
    
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    image_files = []
    
    for file in sorted(os.listdir(input_dir)):
        file_path = os.path.join(input_dir, file)
        if os.path.isfile(file_path):
            ext = Path(file_path).suffix.lower()
            if ext in supported_formats:
                image_files.append(file_path)
    
    if not image_files:
        print("未找到支持的图片文件")
        return
    
    print(f"\n找到 {len(image_files)} 张图片:")
    for f in image_files:
        print(f"  - {Path(f).name}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_pdf = os.path.join(output_dir, f'P19-29_{timestamp}.pdf')
    
    print(f"\n正在生成 PDF...")
    
    images = []
    success_count = 0
    
    for idx, img_path in enumerate(image_files):
        img_name = Path(img_path).name
        print(f"正在处理: {img_name} ({idx+1}/{len(image_files)})")
        
        try:
            img = Image.open(img_path)
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
            success_count += 1
            
        except Exception as e:
            print(f"  警告: 无法加载 {img_name}: {e}")
    
    if images:
        first_img = images[0]
        other_imgs = images[1:] if len(images) > 1 else []
        
        first_img.save(
            output_pdf,
            save_all=True,
            append_images=other_imgs
        )
        
        print("\n" + "=" * 60)
        print(f"✓ PDF 生成成功！")
        print(f"✓ 成功处理了 {success_count} 张图片")
        print(f"输出文件: {output_pdf}")
        print("=" * 60)
        
        return output_pdf
    else:
        print("\n错误: 没有成功加载任何图片")
        return None

if __name__ == '__main__':
    result = main()
    if result:
        print(f"\n转换完成！文件保存在: {result}")
    else:
        print("\n转换失败")
