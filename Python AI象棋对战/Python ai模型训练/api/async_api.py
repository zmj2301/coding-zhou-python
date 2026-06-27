# 异步API支持
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import threading
from functools import wraps
from api.chess_ai_api import ChessAIApi


class AsyncChessAIApi:
    """异步中国象棋AI API接口"""
    
    def __init__(self, difficulty=2, model_path=None, device='cpu'):
        self.sync_api = ChessAIApi(difficulty, model_path, device)
        self._loop = None
        self._thread = None
    
    def initialize(self, board_state=None):
        """初始化"""
        return self.sync_api.initialize(board_state)
    
    async def get_best_move_async(self, board_state=None):
        """异步获取最佳走法"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.sync_api.get_best_move(board_state)
        )
    
    def set_difficulty(self, level):
        return self.sync_api.set_difficulty(level)
    
    def make_move(self, move):
        return self.sync_api.make_move(move)
    
    def get_legal_moves(self):
        return self.sync_api.get_legal_moves()
    
    def get_board_state(self):
        return self.sync_api.get_board_state()
    
    def is_game_over(self):
        return self.sync_api.is_game_over()
    
    def is_in_check(self):
        return self.sync_api.is_in_check()
    
    def reset(self):
        self.sync_api.reset()
