# 局面分析模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.board import Board
from core.rules import Rules
from model.agent import ChessAI


class PositionAnalyzer:
    """局面分析器"""
    
    def __init__(self, ai=None):
        self.ai = ai if ai else ChessAI(difficulty=1)
    
    def analyze_position(self, board_state, step=None):
        """分析单个局面"""
        analysis = {
            'step': step,
            'legal_moves_count': 0,
            'is_check': False,
            'is_game_over': False,
            'game_over_reason': '',
            'evaluation': 0.0,
            'top_moves': []
        }
        
        # 创建临时棋盘
        board = Board()
        board.board = board_state.copy()
        
        # 基本信息
        legal_moves = Rules.get_legal_moves(board)
        analysis['legal_moves_count'] = len(legal_moves)
        analysis['is_check'] = Rules.is_in_check(board)
        game_over, reason = Rules.is_game_over(board)
        analysis['is_game_over'] = game_over
        analysis['game_over_reason'] = reason
        
        # 局面评估
        analysis['evaluation'] = self.ai.evaluate_position(board_state)
        
        # 分析最佳走法
        if legal_moves and not game_over:
            top_moves = self._analyze_top_moves(board, legal_moves, 5)
            analysis['top_moves'] = top_moves
        
        return analysis
    
    def _analyze_top_moves(self, board, moves, limit=5):
        """分析最佳几个走法"""
        scored_moves = []
        for move in moves:
            board.make_move(move)
            score = self.ai.evaluate_position(board)
            board.undo_move()
            
            if board.current_player == Board.BLACK:
                score = -score
            
            scored_moves.append((move, score))
        
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        return [{'move': m[0].to_ucci(), 'score': m[1]} 
                for m in scored_moves[:limit]]
    
    def analyze_game(self, game_records):
        """分析整局游戏"""
        full_analysis = []
        
        board = Board()
        for i, record in enumerate(game_records):
            # 分析走法前的局面
            state_before = record['board_before']
            analysis = self.analyze_position(state_before, step=i + 1)
            analysis['actual_move'] = record['move_ucci']
            analysis['actual_move_score'] = record.get('score')
            full_analysis.append(analysis)
            
            # 执行实际走法
            board.make_move(record['move'])
        
        return full_analysis
