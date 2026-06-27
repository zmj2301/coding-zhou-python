# 棋谱数据爬取模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import requests
from core.move import Move


class ChessDataScraper:
    """中国象棋棋谱数据爬取器"""
    
    def __init__(self, data_dir='data/raw'):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 演示用棋谱
        self.demo_games = [
            # 演示对局1
            [
                'h2e2', 'h9g9', 'g0e2', 'h7h5', 'c0c2', 'c9c5',
                'b0c2', 'b9c9', 'f0e1', 'd9e9', 'd0d4', 'h5e5',
                'c2e3', 'e9f9', 'e3g4', 'c5c3', 'b2c2', 'g9e9'
            ],
            # 演示对局2
            [
                'c2c5', 'b8c8', 'h0g2', 'h8h9', 'b0c2', 'b9a7',
                'e3e4', 'c8c4', 'e1e2', 'd9e9', 'a0a3', 'a9a4'
            ]
        ]
    
    def scrape_from_web(self, url=None):
        """
        从网络爬取棋谱（演示版本）
        实际项目中需要实现真实爬取逻辑
        """
        print("使用演示棋谱数据")
        return self.demo_games
    
    def parse_ucci_moves(self, ucci_list):
        """解析UCCI格式的走法"""
        moves = []
        for ucci_str in ucci_list:
            try:
                move = Move.from_ucci(ucci_str)
                moves.append(move)
            except Exception as e:
                print(f"解析失败: {ucci_str}, 错误: {e}")
        return moves
    
    def save_games(self, games, filename='games.txt'):
        """保存对局"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for game in games:
                f.write(' '.join(game) + '\n')
        print(f"对局已保存: {filepath}")
    
    def load_games(self, filename='games.txt'):
        """加载对局"""
        filepath = os.path.join(self.data_dir, filename)
        games = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    moves = line.strip().split()
                    if moves:
                        games.append(moves)
        return games
