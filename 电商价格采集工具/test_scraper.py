"""测试爬虫功能"""
import sys
import os

# 确保项目目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_jd_scraper():
    """测试京东爬虫"""
    print("=" * 50)
    print("测试京东爬虫")
    print("=" * 50)
    
    try:
        from scraper.jd_scraper import JDScraper
        
        scraper = JDScraper(max_pages=1)
        products = scraper.search("手机")
        
        print(f"\n采集到 {len(products)} 个商品")
        
        if products:
            print("\n前5个商品:")
            for i, p in enumerate(products[:5]):
                print(f"\n{i+1}. {p.name}")
                print(f"   价格: {p.price} 元")
                print(f"   链接: {p.url}")
                print(f"   店铺: {p.shop_name}")
                print(f"   平台: {p.platform}")
        else:
            print("未采集到商品数据")
            
        return len(products) > 0
        
    except Exception as e:
        print(f"京东爬虫测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import():
    """测试导入"""
    print("=" * 50)
    print("测试模块导入")
    print("=" * 50)
    
    try:
        import requests
        print("✓ requests 已安装")
    except ImportError:
        print("✗ requests 未安装，请运行: pip install requests")
        return False
        
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4 已安装")
    except ImportError:
        print("✗ beautifulsoup4 未安装，请运行: pip install beautifulsoup4")
        return False
        
    try:
        import lxml
        print("✓ lxml 已安装")
    except ImportError:
        print("✗ lxml 未安装，请运行: pip install lxml")
        return False
        
    return True


if __name__ == "__main__":
    print("\n电商价格采集工具 - 爬虫功能测试\n")
    
    # 测试导入
    if not test_import():
        print("\n请先安装依赖: pip install requests beautifulsoup4 lxml")
        sys.exit(1)
    
    # 测试京东爬虫
    success = test_jd_scraper()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ 测试成功！爬虫可以正常工作")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ 测试失败，请检查网络连接或爬虫配置")
        print("=" * 50)