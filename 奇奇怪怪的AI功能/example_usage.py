from handwriting_to_pdf import HandwritingToPDF

def example_basic():
    print("基础使用示例")
    print("="*50)
    
    input_directory = "./images"
    
    converter = HandwritingToPDF(input_directory)
    converter.process_images()

def example_custom_options():
    print("\n自定义选项示例")
    print("="*50)
    
    input_directory = "./images"
    output_directory = "./my_output"
    
    converter = HandwritingToPDF(input_directory, output_directory)
    converter.process_images(
        page_size='Letter',
        font_size=14,
        margin=100
    )

if __name__ == '__main__':
    print("手写文字识别与PDF转换工具 - 使用示例")
    print("="*50)
    
    import os
    
    if not os.path.exists('./images'):
        os.makedirs('./images')
        print("\n已创建 'images' 文件夹，请将手写图片放入该文件夹后运行示例。")
    
    print("\n选择运行示例:")
    print("1. 基础使用")
    print("2. 自定义选项")
    
    choice = input("\n请输入选项 (1/2): ").strip()
    
    if choice == '1':
        example_basic()
    elif choice == '2':
        example_custom_options()
    else:
        print("无效选项！")
