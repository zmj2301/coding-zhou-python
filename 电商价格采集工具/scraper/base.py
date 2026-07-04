"""采集器基类模块"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Product:
    """商品数据模型"""
    name: str                          # 商品名称
    price: float                       # 当前价格
    original_price: float = 0.0       # 原价
    sales: int = 0                     # 月销量
    shop_name: str = ""                # 店铺名称
    shop_score: float = 0.0            # 店铺评分 (0-5)
    platform: str = ""                 # 平台名称
    url: str = ""                      # 商品链接
    image_url: str = ""                # 商品图片
    comments: str = ""                 # 评论数文本 (如 "10万+")
    tags: List[str] = field(default_factory=list)  # 标签
    collected_at: str = ""              # 采集时间
    
    def to_dict(self):
        return {
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "sales": self.sales,
            "shop_name": self.shop_name,
            "shop_score": self.shop_score,
            "platform": self.platform,
            "url": self.url,
            "image_url": self.image_url,
            "comments": self.comments,
            "tags": self.tags,
            "collected_at": self.collected_at,
        }


class BaseScraper(ABC):
    """采集器基类"""
    
    platform_name: str = ""
    
    def __init__(self, max_pages: int = 3):
        self.max_pages = max_pages
    
    @abstractmethod
    def search(self, keyword: str) -> List[Product]:
        """搜索商品"""
        pass
    
    @staticmethod
    def _now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
