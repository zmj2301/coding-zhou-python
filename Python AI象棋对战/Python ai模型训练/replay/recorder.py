# 对局记录模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
from datetime import datetime
from core.board import Board
from core.move import Move


class GameRecorder:
    """游戏记录器"""
    
    def __init__(self, save_dir='data/games'):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.move_history = []
        self.score_history = []
        self.current_board = Board()
        self.start_time = datetime.now()
    
    def record_move(self, move, score=None):
        """记录一步走法"""
        board_state = self.current_board.to_numpy().copy()
        
        record = {
            'move': move,
            'move_ucci': move.to_ucci(),
            'from': (move.from_row, move.from_col),
            'to': (move.to_row, move.to_col),
            'board_before': board_state,
            'score': score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.move_history.append(record)
        if score is not None:
            self.score_history.append(score)
        
        # 执行走法
        self.current_board.make_move(move)
    
    def get_record(self, index):
        """获取指定记录"""
        if 0 <= index < len(self.move_history):
            return self.move_history[index]
        return None
    
    def get_all_records(self):
        """获取所有记录"""
        return self.move_history
    
    def get_game_info(self):
        """获取游戏信息"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_moves': len(self.move_history),
            'final_board': self.current_board.to_numpy().tolist()
        }
    
    def save_game(self, filename=None):
        """保存游戏"""
        if filename is None:
            filename = f"game_{self.start_time.strftime('%Y%m%d_%H%M%S')}.pkl"
        
        filepath = os.path.join(self.save_dir, filename)
        
        save_data = {
            'game_info': self.get_game_info(),
            'moves': self.move_history,
            'scores': self.score_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"游戏已保存: {filepath}")
        return filepath
    
    def load_game(self, filepath):
        """加载游戏"""
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        self.move_history = save_data['moves']
        self.score_history = save_data.get('scores', [])
        print(f"游戏已加载: {filepath}")
        return save_data
    
    def reset(self):
        """重置记录器"""
        self.move_history = []
        self.score_history = []
        self.current_board = Board()
        self.start_time = datetime.now()
