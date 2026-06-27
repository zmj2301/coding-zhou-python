# 棋盘表示与操作
import numpy as np
from .move import Move, PieceType, Color


class Board:
    """中国象棋棋盘类 - 10×9网格"""
    
    # 棋子编码
    # 红方：0空，1帅，2仕，3相，4馬，5車，6炮，7兵
    # 黑方：-1空，-8将，-9士，-10象，-11馬，-12車，-13炮，-14卒
    
    # 初始棋盘布局
    INITIAL_BOARD = [
        [-12, -11, -10, -9, -8, -9, -10, -11, -12],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, -13, 0, 0, 0, 0, 0, -13, 0],
        [-14, 0, -14, 0, -14, 0, -14, 0, -14],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [7, 0, 7, 0, 7, 0, 7, 0, 7],
        [0, 6, 0, 0, 0, 0, 0, 6, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [5, 4, 3, 2, 1, 2, 3, 4, 5]
    ]
    
    def __init__(self):
        self.board = np.array(self.INITIAL_BOARD, dtype=np.int8)
        self.current_player = Color.RED  # 红方先行
        self.move_history = []
        self.red_king_pos = (9, 4)
        self.black_king_pos = (0, 4)
    
    def copy(self):
        """深拷贝棋盘"""
        new_board = Board()
        new_board.board = self.board.copy()
        new_board.current_player = self.current_player
        new_board.move_history = self.move_history.copy()
        new_board.red_king_pos = self.red_king_pos
        new_board.black_king_pos = self.black_king_pos
        return new_board
    
    def reset(self):
        """重置棋盘"""
        self.board = np.array(self.INITIAL_BOARD, dtype=np.int8)
        self.current_player = Color.RED
        self.move_history = []
        self.red_king_pos = (9, 4)
        self.black_king_pos = (0, 4)
    
    def get_piece(self, row, col):
        """获取棋盘上某个位置的棋子"""
        if 0 <= row < 10 and 0 <= col < 9:
            return self.board[row][col]
        return 0
    
    def set_piece(self, row, col, piece):
        """设置棋盘上某个位置的棋子"""
        self.board[row][col] = piece
        if piece == 1:
            self.red_king_pos = (row, col)
        elif piece == -8:
            self.black_king_pos = (row, col)
    
    def is_red_piece(self, piece):
        return piece > 0
    
    def is_black_piece(self, piece):
        return piece < 0
    
    def is_my_piece(self, piece):
        if self.current_player == Color.RED:
            return self.is_red_piece(piece)
        else:
            return self.is_black_piece(piece)
    
    def is_enemy_piece(self, piece):
        if self.current_player == Color.RED:
            return self.is_black_piece(piece)
        else:
            return self.is_red_piece(piece)
    
    def make_move(self, move):
        """执行走法，返回是否成功"""
        piece = self.get_piece(move.from_row, move.from_col)
        if piece == 0:
            return False
        if not self.is_my_piece(piece):
            return False
        
        # 记录移动以便撤销
        captured = self.get_piece(move.to_row, move.to_col)
        self.move_history.append((move, piece, captured, 
                                  self.red_king_pos, self.black_king_pos))
        
        # 执行移动
        self.set_piece(move.to_row, move.to_col, piece)
        self.set_piece(move.from_row, move.from_col, 0)
        
        # 交换回合
        self.current_player = Color.BLACK if self.current_player == Color.RED else Color.RED
        
        return True
    
    def undo_move(self):
        """撤销上一步走法"""
        if not self.move_history:
            return
        move, piece, captured, red_kp, black_kp = self.move_history.pop()
        self.set_piece(move.from_row, move.from_col, piece)
        self.set_piece(move.to_row, move.to_col, captured)
        self.red_king_pos = red_kp
        self.black_king_pos = black_kp
        self.current_player = Color.BLACK if self.current_player == Color.RED else Color.RED
    
    def to_numpy(self):
        """转换为numpy数组用于神经网络输入"""
        return self.board.copy()
    
    def print_board(self):
        """打印棋盘（调试用）"""
        piece_chars = {
            0: '   ',
            1: '帥 ', 2: '仕 ', 3: '相 ', 4: '馬 ', 5: '車 ', 6: '炮 ', 7: '兵 ',
            -8: '將 ', -9: '士 ', -10: '象 ', -11: '馬 ', -12: '車 ', -13: '炮 ', -14: '卒 '
        }
        print("   a  b  c  d  e  f  g  h  i")
        for i in range(10):
            print(f"{9-i:2d} ", end="")
            for j in range(9):
                p = self.board[i][j]
                print(piece_chars.get(p, ' ? '), end="")
            print()
