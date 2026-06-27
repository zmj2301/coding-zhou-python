# 标准化API接口
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.chess_engine import ChessEngine
from model.agent import ChessAI
from core.move import Move


class ChessAIApi:
    """中国象棋AI标准化API接口"""
    
    def __init__(self, difficulty=2, model_path=None, device='cpu'):
        """
        初始化AI接口
        
        Args:
            difficulty: 难度级别 (1-简单, 2-中等, 3-困难)
            model_path: 预训练模型路径
            device: 计算设备 ('cpu' 或 'cuda')
        """
        self.engine = ChessEngine()
        self.ai = ChessAI(difficulty=difficulty, model_path=model_path, device=device)
    
    def initialize(self, board_state=None):
        """
        初始化AI，重置棋盘状态
        
        Args:
            board_state: 可选，自定义初始棋盘状态
        """
        self.engine.reset()
        if board_state is not None:
            self.engine.board.board = board_state.copy()
        return True
    
    def get_best_move(self, board_state=None):
        """
        获取下一步最佳走法（同步）
        
        Args:
            board_state: 可选，指定的棋盘状态
        
        Returns:
            Move对象 或 字典格式的走法信息
        """
        if board_state is not None:
            original_state = self.engine.get_board_state()
            self.engine.board.board = board_state.copy()
        
        move = self.ai.get_best_move(self.engine.board)
        
        if board_state is not None:
            self.engine.board.board = original_state
        
        if move:
            return {
                'move': move,
                'from': (move.from_row, move.from_col),
                'to': (move.to_row, move.to_col),
                'ucci': move.to_ucci()
            }
        return None
    
    def set_difficulty(self, level):
        """
        设置AI难度级别
        
        Args:
            level: 难度级别 (1, 2, 3)
        
        Returns:
            bool: 是否成功
        """
        return self.ai.set_difficulty(level)
    
    def make_move(self, move):
        """
        执行一步走法
        
        Args:
            move: Move对象 或 UCCI格式字符串 或 坐标元组
        
        Returns:
            bool: 是否成功
        """
        if isinstance(move, str):
            move = Move.from_ucci(move)
        elif isinstance(move, tuple) and len(move) == 4:
            move = Move(*move)
        
        return self.engine.make_move(move)
    
    def get_legal_moves(self):
        """获取当前局面所有合法走法"""
        return self.engine.get_legal_moves()
    
    def get_board_state(self):
        """获取当前棋盘状态"""
        return self.engine.get_board_state()
    
    def evaluate_position(self):
        """评估当前局面"""
        return self.ai.evaluate_position(self.engine.board)
    
    def is_game_over(self):
        """判断游戏是否结束"""
        return self.engine.is_game_over()
    
    def is_in_check(self):
        """判断是否被将军"""
        return self.engine.is_in_check()
    
    def reset(self):
        """重置游戏"""
        self.engine.reset()
    
    def print_board(self):
        """打印棋盘"""
        self.engine.print_board()
