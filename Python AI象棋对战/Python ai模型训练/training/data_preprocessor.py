# 数据预处理模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import numpy as np
from core.board import Board
from model.dcnn_model import encode_board


class DataPreprocessor:
    """数据预处理类"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def process_game_record(self, moves, result):
        """
        处理对局记录，生成训练样本
        
        Args:
            moves: 走法序列
            result: 对局结果 (1红胜, -1黑胜, 0和棋)
        
        Returns:
            list: 训练样本列表
        """
        samples = []
        board = Board()
        
        for move in moves:
            # 保存当前局面
            state = board.to_numpy()
            encoded = encode_board(state)
            samples.append({
                'state': encoded,
                'result': result
            })
            
            # 执行走法
            board.make_move(move)
        
        return samples
    
    def save_dataset(self, samples, filename='dataset.pkl'):
        """保存数据集"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(samples, f)
        print(f"数据集已保存: {filepath}, 样本数: {len(samples)}")
    
    def load_dataset(self, filename='dataset.pkl'):
        """加载数据集"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def create_dummy_dataset(self, num_games=10):
        """
        创建演示数据集（用于测试）
        """
        import random
        from ..core.rules import Rules
        
        all_samples = []
        
        for _ in range(num_games):
            board = Board()
            game_moves = []
            game_result = 0
            move_count = 0
            
            while True:
                game_over, result = Rules.is_game_over(board)
                if game_over or move_count > 100:
                    if move_count > 20:
                        if result == "将死":
                            game_result = -1 if board.current_player == Board.RED else 1
                        else:
                            game_result = 0
                    break
                
                legal_moves = Rules.get_legal_moves(board)
                if not legal_moves:
                    break
                
                move = random.choice(legal_moves)
                game_moves.append(move)
                board.make_move(move)
                move_count += 1
            
            if move_count > 10:
                samples = self.process_game_record(game_moves, game_result)
                all_samples.extend(samples)
        
        self.save_dataset(all_samples, 'dummy_dataset.pkl')
        return all_samples
