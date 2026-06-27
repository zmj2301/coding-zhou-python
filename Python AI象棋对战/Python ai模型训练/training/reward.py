# 奖励函数设计
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.board import Board
from core.rules import Rules
from core.move import Color


class RewardFunction:
    """中国象棋奖励函数"""
    
    # 子力价值
    PIECE_VALUES = {
        1: 1000, 2: 10, 3: 10, 4: 40, 5: 90, 6: 45, 7: 10,
        -8: -1000, -9: -10, -10: -10, -11: -40, -12: -90, 
        -13: -45, -14: -10
    }
    
    # 位置权重矩阵（红方视角）
    POSITION_WEIGHTS = {
        7: np.array([  # 兵/卒位置权重
            [0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0],
            [1,1,1,2,2,2,1,1,1],
            [1,2,3,4,5,4,3,2,1],
            [2,3,4,6,7,6,4,3,2],
            [3,4,5,7,8,7,5,4,3],
            [0,0,0,0,0,0,0,0,0]
        ])
    }
    
    @staticmethod
    def compute_reward(board: Board, previous_board=None):
        """
        计算当前局面的奖励
        
        Args:
            board: 当前棋盘
            previous_board: 上一步棋盘（用于计算变化奖励）
        
        Returns:
            float: 奖励值
        """
        reward = 0.0
        
        # 1. 胜负奖励
        game_over, result = Rules.is_game_over(board)
        if game_over:
            if result == "将死":
                if Rules.is_in_check(board):
                    if board.current_player == Color.RED:
                        return -1.0  # 红方被将死
                    else:
                        return 1.0  # 黑方被将死
                else:
                    if board.current_player == Color.RED:
                        return 1.0
                    else:
                        return -1.0
            else:
                return 0.0
        
        # 2. 子力价值奖励
        material_reward = RewardFunction._material_value(board)
        reward += material_reward * 0.6
        
        # 3. 位置优势奖励
        position_reward = RewardFunction._position_advantage(board)
        reward += position_reward * 0.2
        
        # 4. 威胁/将军奖励
        threat_reward = RewardFunction._threat_reward(board)
        reward += threat_reward * 0.2
        
        # 5. 走法变化奖励（如果有前一局面）
        if previous_board is not None:
            change_reward = RewardFunction._move_change_reward(board, previous_board)
            reward += change_reward * 0.1
        
        return np.clip(reward, -1.0, 1.0)
    
    @staticmethod
    def _material_value(board: Board):
        """子力价值评估"""
        total = 0
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p != 0:
                    total += RewardFunction.PIECE_VALUES.get(p, 0)
        return total / 2000.0  # 归一化
    
    @staticmethod
    def _position_advantage(board: Board):
        """位置优势评估"""
        score = 0
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p == 7:  # 红兵
                    score += RewardFunction.POSITION_WEIGHTS[7][r][c]
                elif p == -14:  # 黑卒
                    score -= RewardFunction.POSITION_WEIGHTS[7][9 - r][c]
        return score / 50.0  # 归一化
    
    @staticmethod
    def _threat_reward(board: Board):
        """威胁/将军奖励"""
        if Rules.is_in_check(board):
            if board.current_player == Color.RED:
                return -0.3  # 红方被将军
            else:
                return 0.3  # 黑方被将军
        return 0.0
    
    @staticmethod
    def _move_change_reward(board: Board, previous_board: Board):
        """走法变化奖励（鼓励吃子和积极进攻）"""
        captured = 0
        for r in range(10):
            for c in range(9):
                prev = previous_board.board[r][c]
                curr = board.board[r][c]
                if prev != 0 and curr == 0:
                    captured += RewardFunction.PIECE_VALUES.get(prev, 0)
                elif prev == 0 and curr != 0:
                    pass
        
        return abs(captured) / 100.0
