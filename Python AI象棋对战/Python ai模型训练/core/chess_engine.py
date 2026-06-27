# 中国象棋游戏引擎
from .board import Board
from .rules import Rules
from .move import Move, Color


class ChessEngine:
    """中国象棋游戏引擎"""
    
    def __init__(self):
        self.board = Board()
    
    def reset(self):
        """重置游戏"""
        self.board.reset()
    
    def make_move(self, move: Move) -> bool:
        """执行一步走法"""
        return self.board.make_move(move)
    
    def get_legal_moves(self):
        """获取当前所有合法走法"""
        return Rules.get_legal_moves(self.board)
    
    def is_in_check(self):
        """判断是否被将军"""
        return Rules.is_in_check(self.board)
    
    def is_game_over(self):
        """判断游戏是否结束"""
        return Rules.is_game_over(self.board)
    
    def get_current_player(self):
        return self.board.current_player
    
    def print_board(self):
        return self.board.print_board()
    
    def get_board_state(self):
        return self.board.to_numpy()
