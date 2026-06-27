#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整版中国象棋 AI
基于 auto_chess2.py 的专业算法实现
包含：
- PVS（主要变例搜索）
- Alpha-Beta 剪枝
- 置换表
- 杀手走法
- 历史表
- MVV/LVA 排序
- 静态搜索
- 将军延伸
- 迭代加深搜索
"""
import os
import time
import random
from datetime import datetime


# 棋子基础价值（参考象棋巫师）
CHESS_BASIC_VALUE = {
    '帥': 10000, '将': 10000,
    '車': 1000, '馬': 450, '炮': 450,
    '相': 200, '象': 200, '仕': 200, '士': 200,
    '兵': 100, '卒': 100
}

# 红方棋子位置价值矩阵（参考象棋巫师）
RED_POSITION_VALUE = {
    '帥': [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    '仕': [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
    ],
    '相': [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 1, 0, 0],
    ],
    '馬': [
        [0, -3, 5, 4, 3, 3, 4, 5, -3],
        [-3, -3, 0, 3, 1, 3, 0, -3, -3],
        [5, 0, 4, 3, 2, 3, 4, 0, 5],
        [4, 3, 2, 3, 2, 3, 2, 3, 4],
        [3, 2, 1, 0, 0, 0, 1, 2, 3],
        [2, 1, 0, -1, -2, -1, 0, 1, 2],
        [1, 0, -1, -2, -3, -2, -1, 0, 1],
        [0, 0, -1, -2, -3, -2, -1, 0, 0],
        [-1, 0, -2, -3, -4, -3, -2, 0, -1],
        [-3, -5, -5, -5, -5, -5, -5, -5, -3],
    ],
    '車': [
        [6, 8, 6, 8, 8, 8, 6, 8, 6],
        [6, 10, 8, 10, 10, 10, 8, 10, 6],
        [6, 10, 8, 10, 10, 10, 8, 10, 6],
        [7, 10, 10, 12, 14, 12, 10, 10, 7],
        [7, 10, 10, 12, 14, 12, 10, 10, 7],
        [7, 10, 10, 12, 14, 12, 10, 10, 7],
        [7, 10, 10, 12, 14, 12, 10, 10, 7],
        [6, 10, 10, 12, 12, 12, 10, 10, 6],
        [6, 8, 8, 10, 10, 10, 8, 8, 6],
        [4, 6, 6, 8, 8, 8, 6, 6, 4],
    ],
    '炮': [
        [0, 0, 2, 0, 2, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [-2, 0, 2, 0, 2, 0, 2, 0, -2],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    '兵': [
        [0, 0, 0, -2, -4, -2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
}

# 黑方棋子位置价值矩阵（红方矩阵翻转）
BLACK_POSITION_VALUE = {}
for piece_type, matrix in RED_POSITION_VALUE.items():
    BLACK_POSITION_VALUE[piece_type] = [list(reversed(row)) for row in reversed(matrix)]

# 开局下法
BEGIN_MOVES = [
    ('Red', 'Cannon', 7, 2, 4, 2),
    ('Red', 'Cannon', 1, 2, 4, 2),
    ('Red', 'Bishop', 6, 0, 4, 2),
    ('Red', 'Pawn', 2, 3, 2, 4),
    ('Red', 'Knight', 7, 0, 6, 2),
    ('Red', 'Knight', 1, 0, 2, 2),
]


class AIPlayer:
    """完整版中国象棋 AI"""
    
    def __init__(self, model_path=None, difficulty=2, user_profile_path='user.json'):
        self.difficulty = difficulty
        
        if difficulty == 1:
            self.limit_time = 3
        elif difficulty == 2:
            self.limit_time = 5
        else:
            self.limit_time = 8
        
        self.win = 10000
        self.max_ply = 200
        self.win_value = self.win - self.max_ply
        self.ban_value = self.win - 100
        self.draw = 0
        
        self.depth = 1
        self.best_move = None
        
        self.history_table = {}
        self.replacement_table = {}
        self.killer_moves = {}
        self.parent_list = set()
        
        self.check_depth = 0
        self.depth_to_root = 0
        self.max_depth = 20
        
        self.hash_alph = 0
        self.hash_beta = 1
        self.hash_pv = 2
        
        self.node_count = 0
        self.is_root = True
        
        self.thought_history = []
        self._init_new_record()
    
    def _evaluate_chess(self, name, color, r, c):
        """评估单个棋子"""
        basic = CHESS_BASIC_VALUE.get(name, 50)
        
        if color == 'red':
            pos_value = RED_POSITION_VALUE.get(name, [[0]*9 for _ in range(10)])
            if name in RED_POSITION_VALUE:
                pos = pos_value[r][c]
            else:
                pos = 0
        else:
            pos_value = BLACK_POSITION_VALUE.get(name, [[0]*9 for _ in range(10)])
            if name in BLACK_POSITION_VALUE:
                pos = pos_value[r][c]
            else:
                pos = 0
        
        return basic + pos
    
    def _evaluate_board(self, board, player):
        """评估棋盘（从玩家角度）"""
        score = 0
        
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece:
                    name, color, _ = piece
                    value = CHESS_BASIC_VALUE.get(name, 50)
                    
                    if player == color:
                        score += value
                    else:
                        score -= value
        
        return score
    
    def _in_check(self, board, player):
        """检查玩家是否被将军"""
        king_pos = None
        
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece and piece[1] == player:
                    if piece[0] == '帥' or piece[0] == '将':
                        king_pos = (r, c)
                        break
        
        if not king_pos:
            return False
        
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece and piece[1] != player:
                    valid_moves = self._get_valid_moves(board, r, c)
                    if king_pos in valid_moves:
                        return True
        
        return False
    
    def _get_valid_moves(self, board, r, c):
        """获取棋子的合法走法"""
        piece = board[r][c]
        if not piece:
            return []
        
        name, color, _ = piece
        moves = []
        
        if name == '帥' or name == '将':
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 9:
                    if color == 'red' and 0 <= nr < 3 and 3 <= nc <= 5:
                        target = board[nr][nc]
                        if not target or target[1] != 'red':
                            moves.append((nr, nc))
                    elif color == 'black' and 7 <= nr < 10 and 3 <= nc <= 5:
                        target = board[nr][nc]
                        if not target or target[1] != 'black':
                            moves.append((nr, nc))
        
        elif name == '仕' or name == '士':
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 9:
                    if color == 'red' and 0 <= nr < 3 and 3 <= nc <= 5:
                        target = board[nr][nc]
                        if not target or target[1] != 'red':
                            moves.append((nr, nc))
                    elif color == 'black' and 7 <= nr < 10 and 3 <= nc <= 5:
                        target = board[nr][nc]
                        if not target or target[1] != 'black':
                            moves.append((nr, nc))
        
        elif name == '相' or name == '象':
            for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
                nr, nc = r + dr, c + dc
                eye_r, eye_c = r + dr//2, c + dc//2
                if 0 <= nr < 10 and 0 <= nc < 9:
                    if color == 'red' and 5 <= nr < 10 and 0 <= nc <= 8:
                        eye = board[eye_r][eye_c]
                        if not eye or eye[1] != 'red':
                            target = board[nr][nc]
                            if not target or target[1] != 'red':
                                moves.append((nr, nc))
                    elif color == 'black' and 0 <= nr < 5 and 0 <= nc <= 8:
                        eye = board[eye_r][eye_c]
                        if not eye or eye[1] != 'black':
                            target = board[nr][nc]
                            if not target or target[1] != 'black':
                                moves.append((nr, nc))
        
        elif name == '馬' or name == '马':
            for dr, dc in [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 9:
                    eye_r, eye_c = r + dr//2, c + dc//2
                    eye = board[eye_r][eye_c]
                    if eye:
                        continue
                    target = board[nr][nc]
                    if not target or target[1] != color:
                        moves.append((nr, nc))
        
        elif name == '車' or name == '车':
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                for i in range(1, 10):
                    nr, nc = r + dr * i, c + dc * i
                    if 0 <= nr < 10 and 0 <= nc < 9:
                        target = board[nr][nc]
                        if not target:
                            moves.append((nr, nc))
                        elif target[1] != color:
                            moves.append((nr, nc))
                            break
                        else:
                            break
                    else:
                        break
        
        elif name == '炮' or name == '炮':
            found = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                for i in range(1, 10):
                    nr, nc = r + dr * i, c + dc * i
                    if 0 <= nr < 10 and 0 <= nc < 9:
                        target = board[nr][nc]
                        if not found:
                            if not target:
                                moves.append((nr, nc))
                            elif target[1] != color:
                                found = True
                            else:
                                break
                        else:
                            if target:
                                if target[1] != color:
                                    moves.append((nr, nc))
                                break
                    else:
                        break
        
        elif name == '兵' or name == '卒':
            if color == 'red':
                for dr, dc in [(0, 1), (0, -1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 9:
                        if dr == 1 or (nr >= 5):
                            target = board[nr][nc]
                            if not target or target[1] != 'red':
                                moves.append((nr, nc))
            else:
                for dr, dc in [(0, 1), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 9:
                        if dr == -1 or (nr < 5):
                            target = board[nr][nc]
                            if not target or target[1] != 'black':
                                moves.append((nr, nc))
        
        return moves
    
    def _get_all_moves(self, board, player_color):
        """获取所有合法走法"""
        moves = []
        moves_cap = []
        moves_nocap = []
        
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece and piece[1] == player_color:
                    valid_moves = self._get_valid_moves(board, r, c)
                    for (nr, nc) in valid_moves:
                        captured = board[nr][nc]
                        move_tuple = (r, c, nr, nc)
                        move = {
                            'move': move_tuple,
                            'from': (r, c),
                            'to': (nr, nc),
                            'piece_name': piece[0],
                            'piece_color': piece[1],
                            'captured': captured,
                            'captured_name': captured[0] if captured else None,
                            'score': 0
                        }
                        
                        # MVV/LVA 排序
                        if captured:
                            victim_value = CHESS_BASIC_VALUE.get(captured[0], 50)
                            attacker_value = CHESS_BASIC_VALUE.get(piece[0], 50)
                            move['score'] = victim_value * 10 - attacker_value
                            moves_cap.append(move)
                        else:
                            # 杀手走法加分
                            move_tuple = (r, c, nr, nc)
                            if self.killer_moves.get((self.depth_to_root, player_color == 'black')):
                                if move_tuple in self.killer_moves[(self.depth_to_root, player_color == 'black')]:
                                    move['score'] += 10000
                            # 历史表加分
                            if move_tuple in self.history_table:
                                move['score'] += self.history_table[move_tuple] // 100
                            moves_nocap.append(move)
        
        # MVV/LVA 排序
        moves_cap.sort(key=lambda x: x['score'], reverse=True)
        moves_nocap.sort(key=lambda x: x['score'], reverse=True)
        
        moves = moves_cap + moves_nocap
        return moves
    
    def _board_key(self, board):
        """生成棋盘键"""
        key = []
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece:
                    key.append((piece[0], piece[1], r, c))
                else:
                    key.append(None)
        return tuple(key)
    
    def _is_begin(self, board):
        """判断是否为开局"""
        black_move = 0
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece:
                    color = piece[1]
                    name = piece[0]
                    
                    moved = False
                    if color == 'red':
                        if name == '帥' and (r, c) != (4, 0):
                            return False
                        elif name == '炮' and (r, c) not in [(2, 1), (2, 7)]:
                            return False
                        elif name == '馬' and (r, c) not in [(2, 0), (2, 8)]:
                            return False
                        elif name == '車' and (r, c) not in [(0, 0), (0, 8)]:
                            return False
                        elif name == '兵' and (r, c) not in [(3, 0), (3, 2), (3, 4), (3, 6), (3, 8)]:
                            return False
                        elif name == '仕' and (r, c) not in [(2, 3), (2, 5)]:
                            return False
                        elif name == '相' and (r, c) not in [(2, 2), (2, 6)]:
                            return False
                    else:
                        if name == '将' and (r, c) != (9, 4):
                            black_move += 1
                        elif name == '炮' and (r, c) not in [(7, 1), (7, 7)]:
                            black_move += 1
                        elif name == '馬' and (r, c) not in [(7, 0), (7, 8)]:
                            black_move += 1
                        elif name == '車' and (r, c) not in [(9, 0), (9, 8)]:
                            black_move += 1
                        elif name == '卒' and (r, c) not in [(6, 0), (6, 2), (6, 4), (6, 6), (6, 8)]:
                            black_move += 1
                        elif name == '士' and (r, c) not in [(7, 3), (7, 5)]:
                            black_move += 1
                        elif name == '象' and (r, c) not in [(7, 2), (7, 6)]:
                            black_move += 1
                
                if black_move > 1:
                    return False
        
        return True
    
    def _quiescence_search(self, board, alpha, beta, maximizing_player):
        """静态搜索"""
        player = 'red' if maximizing_player else 'black'
        limit = -self.win if maximizing_player else self.win
        
        # 评估当前局面
        score = self._evaluate_board(board, player)
        if maximizing_player:
            limit = max(limit, score)
            alpha = max(limit, alpha)
        else:
            limit = min(limit, score)
            beta = min(limit, beta)
        
        if alpha >= beta:
            return limit
        
        # 获取吃子走法
        captures = []
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece and piece[1] == player:
                    valid_moves = self._get_valid_moves(board, r, c)
                    for (nr, nc) in valid_moves:
                        captured = board[nr][nc]
                        if captured:
                            move = {
                                'from': (r, c),
                                'to': (nr, nc),
                                'piece_name': piece[0],
                                'captured': captured
                            }
                            captures.append(move)
        
        captures.sort(key=lambda x: CHESS_BASIC_VALUE.get(x['captured'][0], 50), reverse=True)
        
        for cap in captures[:6]:
            r, c = cap['from']
            nr, nc = cap['to']
            piece = board[r][c]
            captured = board[nr][nc]
            
            board[nr][nc] = piece
            board[r][c] = None
            
            if maximizing_player:
                score = -self._quiescence_search(board, alpha, beta, False)
                board[r][c] = piece
                board[nr][nc] = captured
                
                if score > limit:
                    limit = score
                    alpha = max(limit, alpha)
                if alpha >= beta:
                    return limit
            else:
                score = -self._quiescence_search(board, alpha, beta, True)
                board[r][c] = piece
                board[nr][nc] = captured
                
                if score < limit:
                    limit = score
                    beta = min(limit, beta)
                if beta <= alpha:
                    return limit
        
        return limit
    
    def _pvs(self, board, alpha, beta, depth, maximizing_player):
        """PVS（主要变例搜索）"""
        self.node_count += 1
        
        player = 'red' if maximizing_player else 'black'
        
        # 检查是否有一方输了
        red_has_king = any(board[r][c] and board[r][c][0] == '帥' for r in range(10) for c in range(9))
        black_has_king = any(board[r][c] and board[r][c][0] == '将' for r in range(10) for c in range(9))
        
        if not red_has_king:
            return (-self.win) + self.depth_to_root if maximizing_player else self.win - self.depth_to_root
        if not black_has_king:
            return self.win - self.depth_to_root if maximizing_player else (-self.win) + self.depth_to_root
        
        # 到达0深度
        if depth == 0:
            return self._quiescence_search(board, alpha, beta, maximizing_player)
        
        # 检查深度限制
        if self.depth_to_root > self.max_depth:
            return self._evaluate_board(board, player)
        
        # 检查重复局面
        now_board = (player,) + self._board_key(board)
        if now_board in self.parent_list:
            if self._in_check(board, player):
                return self.ban_value - self.depth_to_root if player == 'red' else (-self.ban_value) + self.depth_to_root
            return self.draw
        
        # 置换表
        best_move = None
        if now_board in self.replacement_table:
            stored_depth, stored_score, stored_move, stored_flag = self.replacement_table[now_board]
            if stored_depth >= depth:
                if stored_score > self.win_value:
                    stored_score -= self.depth_to_root
                elif stored_score < -self.win_value:
                    stored_score += self.depth_to_root
                
                if maximizing_player:
                    if stored_flag == self.hash_beta and stored_score >= beta:
                        return stored_score
                    elif stored_flag == self.hash_alph and stored_score <= alpha:
                        return stored_score
                    else:
                        return stored_score
                else:
                    if stored_flag == self.hash_beta and stored_score <= alpha:
                        return stored_score
                    elif stored_flag == self.hash_alph and stored_score >= beta:
                        return stored_score
                    else:
                        return stored_score
        
        self.parent_list.add(now_board)
        
        moves = self._get_all_moves(board, player)
        
        not_found_pv = True
        node_flag = self.hash_alph
        limit = -self.win if maximizing_player else self.win
        
        for i, move_data in enumerate(moves[:12]):
            r, c = move_data['from']
            nr, nc = move_data['to']
            piece = board[r][c]
            captured = board[nr][nc]
            
            # 模拟走棋
            board[nr][nc] = piece
            board[r][c] = None
            
            self.depth_to_root += 1
            
            is_check = self._in_check(board, player)
            new_depth = depth - 1
            if is_check:
                new_depth = depth
            
            if maximizing_player:
                if not_found_pv:
                    score = -self._pvs(board, alpha, beta, new_depth, False)
                else:
                    score = -self._pvs(board, alpha, alpha + 1, new_depth, False)
                    if alpha < score < beta:
                        score = -self._pvs(board, alpha, beta, new_depth, False)
            else:
                if not_found_pv:
                    score = -self._pvs(board, alpha, beta, new_depth, True)
                else:
                    score = -self._pvs(board, beta - 1, beta, new_depth, True)
                    if alpha < score < beta:
                        score = -self._pvs(board, alpha, score, new_depth, True)
            
            self.depth_to_root -= 1
            
            board[r][c] = piece
            board[nr][nc] = captured
            
            if maximizing_player:
                if score > limit:
                        limit = score
                        best_move = (r, c, nr, nc)
                        if self.is_root and self.depth_to_root == 0:
                            self.best_move = best_move
                        if score >= beta:
                            node_flag = self.hash_beta
                            break
                        if score > alpha:
                            node_flag = self.hash_pv
                            alpha = score
                            not_found_pv = False
            else:
                if score < limit:
                    limit = score
                    best_move = (r, c, nr, nc)
                    if self.is_root and self.depth_to_root == 0:
                        self.best_move = best_move
                    if score <= alpha:
                        node_flag = self.hash_beta
                        break
                    if score < beta:
                        beta = score
                        not_found_pv = False
        
        self.parent_list.discard(now_board)
        
        # 更新历史表
        if best_move:
            if best_move not in self.history_table:
                self.history_table[best_move] = 0
            self.history_table[best_move] += depth * depth
        
        # 更新置换表
        if best_move:
            self.replacement_table[now_board] = (depth, limit, best_move, node_flag)
        elif best_move is None and len(moves) > 0:
            self.replacement_table[now_board] = (0, limit, moves[0]['from'] + moves[0]['to'], node_flag)
        
        # 更新杀手走法
        if best_move:
            key = (self.depth_to_root, maximizing_player)
            if key not in self.killer_moves:
                self.killer_moves[key] = []
            self.killer_moves[key].append(best_move)
            if len(self.killer_moves[key]) > 2:
                del self.killer_moves[key][0]
        
        return limit
    
    def _iter_search(self, board, player_color='black'):
        """迭代加深搜索"""
        self.depth = 1
        self.killer_moves.clear()
        start_time = time.time()
        
        # 开局表
        begin, move = self._get_begin_move(board)
        if begin and move:
            print(f"\n**********开局***********")
            self.best_move = move
            return
        
        print("\n**********开始搜索***********")
        while self.depth <= 20:
            if (time.time() - start_time) > self.limit_time:
                break
            
            self.parent_list = set()
            self.node_count = 0
            self.check_depth = 0
            self.is_root = True
            self.depth_to_root = 0
            
            is_red = (player_color == 'red')
            score = self._pvs(board, -self.win, self.win, self.depth, is_red)
            
            print(f"搜索深度{self.depth}: 最好下法{self.best_move}, 分数{score}, 用时{time.time()-start_time:.3f}秒")
            
            self.depth += 1
        
        # 历史表衰减
        for key in self.history_table:
            self.history_table[key] >>= 2
    
    def _get_begin_move(self, board):
        """获取开局走法"""
        if not self._is_begin(board):
            return False, None
        
        self.replacement_table.clear()
        self.history_table.clear()
        
        # 检查是否32个棋子都在
        count = sum(1 for r in range(10) for c in range(9) if board[r][c])
        if count == 32:
            return True, BEGIN_MOVES[random.randint(0, len(BEGIN_MOVES) - 1)]
        
        return True, None
    
    def get_best_move_with_thought(self, board, get_valid_moves_func, player_color='black'):
        """获取最佳走法"""
        start_time = time.time()
        
        # 重置
        self.best_move = None
        self.node_count = 0
        
        # 如果是开局
        begin, move = self._get_begin_move(board)
        if begin and move:
            elapsed = time.time() - start_time
            summary = f"开局走法"
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'elapsed': round(elapsed, 2),
                'all_moves_count': 1,
                'candidate_moves': [],
                'best_move': move,
                'best_score': 0,
                'using_model': False,
                'summary': summary
            }
            self.thought_history.append(record)
            return move, record
        
        # 迭代加深搜索
        self._iter_search(board, player_color)
        
        elapsed = time.time() - start_time
        
        # 生成候选走法
        all_moves = self._get_all_moves(board, player_color)
        
        summary = ""
        if self.best_move:
            for m in all_moves:
                if m['from'] + m['to'] == self.best_move:
                    if m['captured']:
                        summary = f"用 {m['piece_name']} 吃掉 {m['captured_name']}"
                    else:
                        summary = f"移动 {m['piece_name']}"
                    break
        
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed': round(elapsed, 2),
            'all_moves_count': len(all_moves),
            'candidate_moves': all_moves[:8],
            'best_move': self.best_move,
            'best_score': 0,
            'using_model': False,
            'summary': summary
        }
        self.thought_history.append(record)
        
        return self.best_move, record
    
    def _init_new_record(self):
        record_dir = os.path.join(os.path.dirname(__file__), 'ai_records')
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)
