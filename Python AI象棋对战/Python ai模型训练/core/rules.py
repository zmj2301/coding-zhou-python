# 中国象棋规则校验与合法走法生成
from .board import Board
from .move import Move, Color


class Rules:
    """中国象棋规则类"""
    
    @staticmethod
    def get_legal_moves(board: Board):
        """获取当前局面所有合法走法"""
        legal_moves = []
        for row in range(10):
            for col in range(9):
                piece = board.get_piece(row, col)
                if piece == 0:
                    continue
                if board.is_my_piece(piece):
                    moves = Rules._get_piece_moves(board, row, col, piece)
                    legal_moves.extend(moves)
        
        # 过滤会导致被将军的走法
        legal_moves = [move for move in legal_moves 
                       if not Rules._move_leaves_king_in_check(board, move)]
        return legal_moves
    
    @staticmethod
    def _get_piece_moves(board, row, col, piece):
        """获取单个棋子的所有走法（不校验将军）"""
        moves = []
        piece_type = abs(piece)
        
        if piece_type == 1 or piece_type == 8:  # 将/帅
            moves = Rules._get_king_moves(board, row, col, piece)
        elif piece_type == 2 or piece_type == 9:  # 士
            moves = Rules._get_advisor_moves(board, row, col, piece)
        elif piece_type == 3 or piece_type == 10:  # 象/相
            moves = Rules._get_elephant_moves(board, row, col, piece)
        elif piece_type == 4 or piece_type == 11:  # 马
            moves = Rules._get_horse_moves(board, row, col, piece)
        elif piece_type == 5 or piece_type == 12:  # 车
            moves = Rules._get_chariot_moves(board, row, col, piece)
        elif piece_type == 6 or piece_type == 13:  # 炮
            moves = Rules._get_cannon_moves(board, row, col, piece)
        elif piece_type == 7 or piece_type == 14:  # 兵/卒
            moves = Rules._get_pawn_moves(board, row, col, piece)
        
        return moves
    
    @staticmethod
    def _get_king_moves(board, row, col, piece):
        moves = []
        is_red = board.is_red_piece(piece)
        # 将/帅只能在九宫格移动
        min_row, max_row = (7, 9) if is_red else (0, 2)
        min_col, max_col = 3, 5
        
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            if (min_row <= nr <= max_row and
                min_col <= nc <= max_col):
                target = board.get_piece(nr, nc)
                if target == 0 or board.is_enemy_piece(target):
                    moves.append(Move(row, col, nr, nc))
        return moves
    
    @staticmethod
    def _get_advisor_moves(board, row, col, piece):
        moves = []
        is_red = board.is_red_piece(piece)
        min_row, max_row = (7, 9) if is_red else (0, 2)
        min_col, max_col = 3, 5
        
        dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            if (min_row <= nr <= max_row and
                min_col <= nc <= max_col):
                target = board.get_piece(nr, nc)
                if target == 0 or board.is_enemy_piece(target):
                    moves.append(Move(row, col, nr, nc))
        return moves
    
    @staticmethod
    def _get_elephant_moves(board, row, col, piece):
        moves = []
        is_red = board.is_red_piece(piece)
        
        # 象不能过河
        if is_red:
            valid_rows = range(5, 10)
        else:
            valid_rows = range(0, 5)
        
        dirs = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        block_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for (dr, dc), (bdr, bdc) in zip(dirs, block_dirs):
            nr, nc = row + dr, col + dc
            if nr in valid_rows and 0 <= nc < 9:
                block = board.get_piece(row + bdr, col + bdc)
                if block == 0:
                    target = board.get_piece(nr, nc)
                    if target == 0 or board.is_enemy_piece(target):
                        moves.append(Move(row, col, nr, nc))
        return moves
    
    @staticmethod
    def _get_horse_moves(board, row, col, piece):
        moves = []
        dirs = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)]
        block_dirs = [(-1, 0), (-1, 0), (0, -1), (0, -1),
                       (0, 1), (0, 1), (1, 0), (1, 0)]
        
        for (dr, dc), (bdr, bdc) in zip(dirs, block_dirs):
            nr, nc = row + dr, col + dc
            if 0 <= nr < 10 and 0 <= nc < 9:
                block = board.get_piece(row + bdr, col + bdc)
                if block == 0:
                    target = board.get_piece(nr, nc)
                    if target == 0 or board.is_enemy_piece(target):
                        moves.append(Move(row, col, nr, nc))
        return moves
    
    @staticmethod
    def _get_chariot_moves(board, row, col, piece):
        moves = []
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            while 0 <= nr < 10 and 0 <= nc < 9:
                target = board.get_piece(nr, nc)
                if target == 0:
                    moves.append(Move(row, col, nr, nc))
                else:
                    if board.is_enemy_piece(target):
                        moves.append(Move(row, col, nr, nc))
                    break
                nr += dr
                nc += dc
        return moves
    
    @staticmethod
    def _get_cannon_moves(board, row, col, piece):
        moves = []
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            jumped = False
            while 0 <= nr < 10 and 0 <= nc < 9:
                target = board.get_piece(nr, nc)
                if target == 0:
                    if not jumped:
                        moves.append(Move(row, col, nr, nc))
                else:
                    if not jumped:
                        jumped = True
                    else:
                        if board.is_enemy_piece(target):
                            moves.append(Move(row, col, nr, nc))
                        break
                nr += dr
                nc += dc
        return moves
    
    @staticmethod
    def _get_pawn_moves(board, row, col, piece):
        moves = []
        is_red = board.is_red_piece(piece)
        
        if is_red:
            forward = -1
            river = 5
        else:
            forward = 1
            river = 4
        
        # 前进
        nr, nc = row + forward, col
        if 0 <= nr < 10:
            target = board.get_piece(nr, nc)
            if target == 0 or board.is_enemy_piece(target):
                moves.append(Move(row, col, nr, nc))
        
        # 过河后可以左右移动
        if (is_red and row <= river) or (not is_red and row >= river):
            for dc in [-1, 1]:
                nc = col + dc
                if 0 <= nc < 9:
                    target = board.get_piece(row, nc)
                    if target == 0 or board.is_enemy_piece(target):
                        moves.append(Move(row, col, row, nc))
        return moves
    
    @staticmethod
    def _move_leaves_king_in_check(board, move):
        """判断走法是否导致被将军"""
        board.make_move(move)
        in_check = Rules.is_in_check(board)
        board.undo_move()
        return in_check
    
    @staticmethod
    def is_in_check(board: Board):
        """判断当前局面是否被将军"""
        if board.current_player == Color.RED:
            king_r, king_c = board.red_king_pos
            enemy_pieces = [p for p in [-8, -9, -10, -11, -12, -13, -14]]
        else:
            king_r, king_c = board.black_king_pos
            enemy_pieces = [p for p in [1, 2, 3, 4, 5, 6, 7]]
        
        # 临时切换视角检查将军
        saved_player = board.current_player
        board.current_player = Color.BLACK if board.current_player == Color.RED else Color.RED
        
        for r in range(10):
            for c in range(9):
                p = board.get_piece(r, c)
                if p in enemy_pieces:
                    moves = Rules._get_piece_moves(board, r, c, p)
                    for move in moves:
                        if move.to_row == king_r and move.to_col == king_c:
                            board.current_player = saved_player
                            return True
        
        board.current_player = saved_player
        return False
    
    @staticmethod
    def is_game_over(board: Board):
        """判断游戏是否结束"""
        legal_moves = Rules.get_legal_moves(board)
        if not legal_moves:
            return True, "将死" if Rules.is_in_check(board) else "困毙"
        return False, ""
