"""数据清洗、去重与对比分析模块"""
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from scraper.base import Product


class DataAnalyzer:
    """数据分析器"""
    
    @staticmethod
    def deduplicate(products: List[Product]) -> List[Product]:
        """基于商品名称相似度去重"""
        seen = set()
        result = []
        for p in products:
            # 简单去重：取名称前20字符的哈希
            key = (p.platform, p.name[:20], round(p.price, -1))
            if key not in seen:
                seen.add(key)
                result.append(p)
        return result
    
    @staticmethod
    def sort_by_price(products: List[Product], ascending: bool = True) -> List[Product]:
        """按价格排序"""
        return sorted(products, key=lambda x: x.price, reverse=not ascending)
    
    @staticmethod
    def filter_by_platform(products: List[Product], platform: str) -> List[Product]:
        """按平台过滤"""
        return [p for p in products if p.platform == platform]
    
    @staticmethod
    def price_range(products: List[Product]) -> Dict[str, float]:
        """价格区间统计"""
        if not products:
            return {"min": 0, "max": 0, "avg": 0, "median": 0}
        prices = [p.price for p in products]
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        median = sorted_prices[n // 2] if n % 2 else (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": round(sum(prices) / n, 2),
            "median": round(median, 2),
        }
    
    @staticmethod
    def platform_stats(products: List[Product]) -> Dict[str, Dict[str, Any]]:
        """各平台统计"""
        stats = defaultdict(lambda: {"count": 0, "avg_price": 0, "min_price": float('inf'), "max_price": 0, "total_sales": 0})
        for p in products:
            s = stats[p.platform]
            s["count"] += 1
            s["avg_price"] = (s["avg_price"] * (s["count"] - 1) + p.price) / s["count"]
            s["min_price"] = min(s["min_price"], p.price)
            s["max_price"] = max(s["max_price"], p.price)
            s["total_sales"] += p.sales
        for s in stats.values():
            s["avg_price"] = round(s["avg_price"], 2)
            if s["min_price"] == float('inf'):
                s["min_price"] = 0
        return dict(stats)
    
    @staticmethod
    def recommend(products: List[Product], top_n: int = 5) -> List[Dict[str, Any]]:
        """性价比推荐 - 综合评分算法
        
        评分公式: score = 0.4 * price_score + 0.3 * sales_score + 0.2 * shop_score + 0.1 * discount_score
        """
        if not products:
            return []
        
        prices = [p.price for p in products]
        max_sales = max(p.sales for p in products)
        
        scored = []
        for p in products:
            # 价格得分 (价格越低分越高)
            price_score = 1 - (p.price - min(prices)) / (max(prices) - min(prices) + 1)
            # 销量得分
            sales_score = p.sales / (max_sales + 1)
            # 店铺评分得分
            shop_score = p.shop_score / 5.0
            # 折扣得分
            discount_score = 0
            if p.original_price > 0:
                discount_score = max(0, 1 - p.price / p.original_price)
            
            total_score = round(
                0.4 * price_score + 0.3 * sales_score + 0.2 * shop_score + 0.1 * discount_score,
                4
            )
            
            scored.append({
                "product": p,
                "score": total_score,
                "score_detail": {
                    "price": round(price_score, 3),
                    "sales": round(sales_score, 3),
                    "shop": round(shop_score, 3),
                    "discount": round(discount_score, 3),
                }
            })
        
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_n]
    
    @staticmethod
    def price_distribution(products: List[Product], bins: int = 10) -> Dict[str, Any]:
        """价格分布 - 用于图表"""
        if not products:
            return {"labels": [], "counts": []}
        
        prices = [p.price for p in products]
        min_p, max_p = min(prices), max(prices)
        step = (max_p - min_p) / bins if max_p > min_p else 1
        
        labels = []
        counts = []
        for i in range(bins):
            low = min_p + i * step
            high = low + step
            if bins <= 5:
                label = f"{low:.0f}-{high:.0f}"
            else:
                label = f"{low:.0f}"
            labels.append(label)
            counts.append(sum(1 for p in prices if low <= p < high))
        
        # 最后一个bin包含右端点
        if prices and counts:
            counts[-1] += sum(1 for p in prices if p == max_p) - (1 if max_p in [min_p + i * step + (max_p - min_p) / bins for i in range(bins - 1)] else 0)
        
        return {"labels": labels, "counts": counts}
    
    @staticmethod
    def platform_price_comparison(products: List[Product]) -> Dict[str, Any]:
        """各平台价格对比数据 - 用于图表"""
        stats = DataAnalyzer.platform_stats(products)
        return {
            "platforms": list(stats.keys()),
            "avg_prices": [round(stats[p]["avg_price"], 2) for p in stats],
            "min_prices": [round(stats[p]["min_price"], 2) for p in stats],
            "max_prices": [round(stats[p]["max_price"], 2) for p in stats],
        }
    
    @staticmethod
    def export_data(products: List[Product]) -> List[Dict[str, Any]]:
        """导出为可序列化的字典列表"""
        return [p.to_dict() for p in products]
