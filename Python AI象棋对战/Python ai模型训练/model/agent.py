# AI智能体集成
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from core.board import Board
from core.rules import Rules
from core.move import Move, Color
from model.dcnn_model import ChessDCNN, predict_board_score
from model.mcts import MCTS


class ChessAI:
    """中国象棋AI智能体"""
    
    def __init__(self, difficulty=2, model_path=None, device='cpu'):
        """
        初始化AI
        difficulty: 1-简单, 2-中等, 3-困难
        """
        self.difficulty = difficulty
        self.device = device
        
        # 根据难度设置参数
        self._set_difficulty_params()
        
        # 加载模型
        self.model = None
        if model_path:
            self._load_model(model_path)
        
        # 初始化MCTS
        self.mcts = MCTS(
            model=self.model,
            simulation_limit=self.sim_limit,
            time_limit=self.time_limit
        )
    
    def _set_difficulty_params(self):
        """根据难度设置参数"""
        if self.difficulty == 1:  # 简单
            self.sim_limit = 200
            self.time_limit = 0.5
        elif self.difficulty == 2:  # 中等
            self.sim_limit = 800
            self.time_limit = 1.5
        else:  # 困难
            self.sim_limit = 2000
            self.time_limit = 3.0
    
    def _load_model(self, model_path):
        """加载预训练模型"""
        try:
            self.model = ChessDCNN()
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            print(f"模型加载成功: {model_path}")
        except Exception as e:
            print(f"模型加载失败，使用基础MCTS: {e}")
            self.model = None
    
    def set_difficulty(self, level):
        """设置难度级别"""
        if 1 <= level <= 3:
            self.difficulty = level
            self._set_difficulty_params()
            self.mcts.simulation_limit = self.sim_limit
            self.mcts.time_limit = self.time_limit
            return True
        return False
    
    def get_best_move(self, board_state):
        """
        获取下一步最佳走法
        board_state: 棋盘状态(numpy array或Board对象)
        """
        if isinstance(board_state, np.ndarray):
            board = Board()
            board.board = board_state.copy()
            # 简单判断当前玩家
            board.current_player = Color.RED
        else:
            board = board_state
        
        return self.mcts.search(board)
    
    def evaluate_position(self, board_state):
        """评估当前局面"""
        if self.model:
            return predict_board_score(self.model, 
                                      board_state if isinstance(board_state, np.ndarray) 
                                      else board_state.to_numpy(),
                                      self.device)
        else:
            return self._simple_evaluate(board_state)
    
    def _simple_evaluate(self, board):
        """简单子力评估"""
        values = {
            1: 1000, 2: 10, 3: 10, 4: 40, 5: 90, 6: 45, 7: 10,
            -8: -1000, -9: -10, -10: -10, -11: -40, -12: -90, 
            -13: -45, -14: -10
        }
        score = 0
        if isinstance(board, np.ndarray):
            state = board
        else:
            state = board.board
        
        for r in range(10):
            for c in range(9):
                p = state[r][c]
                if p != 0:
                    score += values.get(p, 0)
        return score / 1000.0


import numpy as np  # 补充导入
