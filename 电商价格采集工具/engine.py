"""采集引擎 - 协调多平台采集与数据分析"""
import time
from typing import List, Dict, Any, Optional
from scraper.base import Product, BaseScraper
from scraper.jd_scraper import JDScraper
from scraper.taobao_scraper import TaobaoScraper
from scraper.pdd_scraper import PDDScraper
from analyzer import DataAnalyzer

# Selenium 爬虫（无需实名认证，获取真实数据）
try:
    from scraper.selenium_scraper import SeleniumJDScraper, SeleniumTaobaoScraper, SeleniumPDDScraper
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class CollectorEngine:
    """采集引擎 - 核心协调器
    
    支持三种采集模式：
    - "requests": 使用 requests 爬虫（快速但可能被反爬）
    - "selenium": 使用 Selenium 爬虫（无需认证，获取真实数据）
    - "api": 使用开放平台API（需要实名认证）
    """
    
    def __init__(self, platforms: Optional[List[str]] = None, max_pages: int = 3, mode: str = "requests"):
        self.max_pages = max_pages
        self.mode = mode
        self._scrapers: Dict[str, BaseScraper] = {}
        self._init_scrapers(platforms or ["京东", "淘宝", "拼多多"])
        self._analyzer = DataAnalyzer()
    
    def _init_scrapers(self, platform_names: List[str]):
        """初始化采集器"""
        
        # 根据模式选择爬虫
        if self.mode == "selenium" and SELENIUM_AVAILABLE:
            scraper_map = {
                "京东": SeleniumJDScraper,
                "淘宝": SeleniumTaobaoScraper,
                "拼多多": SeleniumPDDScraper,
            }
            print("[引擎] 使用 Selenium 爬虫（无需认证，获取真实数据）")
        else:
            scraper_map = {
                "京东": JDScraper,
                "淘宝": TaobaoScraper,
                "拼多多": PDDScraper,
            }
            if self.mode == "selenium":
                print("[引擎] Selenium 未安装，使用 requests 爬虫")
            else:
                print("[引擎] 使用 requests 爬虫")
        
        for name in platform_names:
            if name in scraper_map:
                self._scrapers[name] = scraper_map[name](max_pages=self.max_pages)
    
    def collect(self, keyword: str) -> Dict[str, Any]:
        """执行采集并返回完整结果
        
        Returns:
            {
                "keyword": str,
                "total": int,
                "products": List[dict],     # 去重排序后
                "all_products": List[dict],  # 原始数据
                "recommendations": List[dict],
                "price_range": dict,
                "platform_stats": dict,
                "price_distribution": dict,
                "platform_comparison": dict,
                "time_elapsed": float,
            }
        """
        start_time = time.time()
        all_products: List[Product] = []
        platform_details = {}
        
        for name, scraper in self._scrapers.items():
            try:
                products = scraper.search(keyword)
                all_products.extend(products)
                platform_details[name] = {
                    "collected": len(products),
                    "status": "success",
                }
            except Exception as e:
                platform_details[name] = {
                    "collected": 0,
                    "status": f"error: {str(e)}",
                }
        
        # 数据清洗
        cleaned = self._analyzer.deduplicate(all_products)
        sorted_products = self._analyzer.sort_by_price(cleaned, ascending=True)
        
        # 分析
        recommendations = self._analyzer.recommend(sorted_products, top_n=5)
        price_range = self._analyzer.price_range(sorted_products)
        platform_stats = self._analyzer.platform_stats(sorted_products)
        price_dist = self._analyzer.price_distribution(sorted_products, bins=10)
        platform_comp = self._analyzer.platform_price_comparison(sorted_products)
        
        elapsed = round(time.time() - start_time, 2)
        
        return {
            "keyword": keyword,
            "total": len(sorted_products),
            "platform_details": platform_details,
            "products": self._analyzer.export_data(sorted_products),
            "all_products": self._analyzer.export_data(all_products),
            "recommendations": [
                {
                    "rank": i + 1,
                    "score": r["score"],
                    "score_detail": r["score_detail"],
                    **r["product"].to_dict(),
                }
                for i, r in enumerate(recommendations)
            ],
            "price_range": price_range,
            "platform_stats": platform_stats,
            "price_distribution": price_dist,
            "platform_comparison": platform_comp,
            "time_elapsed": elapsed,
        }
    
    @staticmethod
    def run(keyword: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """快速运行采集的静态方法"""
        engine = CollectorEngine(platforms=platforms)
        return engine.collect(keyword)
