# 中国象棋AI
__version__ = '1.0.0'
__author__ = 'Chinese Chess AI Team'

from .core import Board, Move, Rules, ChessEngine, Color
from .model import ChessDCNN, ChessAI
from .api import ChessAIApi, AsyncChessAIApi
from .replay import GameRecorder, PositionAnalyzer, GameVisualizer
from .training import RewardFunction, DataPreprocessor, SupervisedTrainer
from .utils import CheckpointManager, Config

__all__ = [
    # 核心
    'Board', 'Move', 'Rules', 'ChessEngine', 'Color',
    # 模型
    'ChessDCNN', 'ChessAI',
    # API
    'ChessAIApi', 'AsyncChessAIApi',
    # 复盘
    'GameRecorder', 'PositionAnalyzer', 'GameVisualizer',
    # 训练
    'RewardFunction', 'DataPreprocessor', 'SupervisedTrainer',
    # 工具
    'CheckpointManager', 'Config'
]
