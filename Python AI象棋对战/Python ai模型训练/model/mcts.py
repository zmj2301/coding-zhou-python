# 蒙特卡洛树搜索(MCTS)实现
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import time
import numpy as np
from core.board import Board
from core.rules import Rules
from core.move import Move, Color


class MCTSNode:
    """MCTS树节点"""
    def __init__(self, board: Board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move  # 到达此节点的走法
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.is_leaf = True
        self.untried_moves = Rules.get_legal_moves(board)
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def best_child(self, c_param=1.414):
        """选择UCT值最高的子节点"""
        choices_weights = [
            (child.value / child.visits) +
            c_param * math.sqrt(2 * math.log(self.visits) / child.visits)
            for child in self.children
        ]
        return self.children[np.argmax(choices_weights)]


class MCTS:
    """蒙特卡洛树搜索类"""
    
    def __init__(self, model=None, simulation_limit=1000, time_limit=2.0):
        self.model = model
        self.simulation_limit = simulation_limit
        self.time_limit = time_limit
    
    def search(self, board: Board):
        """搜索最佳走法"""
        root = MCTSNode(board.copy())
        start_time = time.time()
        simulations = 0
        
        while (simulations < self.simulation_limit and 
               time.time() - start_time < self.time_limit):
            node = self._tree_policy(root)
            reward = self._default_policy(node.board)
            self._backpropagate(node, reward)
            simulations += 1
        
        # 选择访问次数最多的子节点
        if root.children:
            best_node = max(root.children, key=lambda n: n.visits)
            return best_node.move
        return None
    
    def _tree_policy(self, node: MCTSNode):
        """树策略：选择-扩展"""
        while not Rules.is_game_over(node.board)[0]:
            if not node.is_fully_expanded():
                return self._expand(node)
            else:
                node = node.best_child()
        return node
    
    def _expand(self, node: MCTSNode):
        """扩展节点"""
        move = node.untried_moves.pop()
        new_board = node.board.copy()
        new_board.make_move(move)
        child_node = MCTSNode(new_board, parent=node, move=move)
        node.children.append(child_node)
        node.is_leaf = False
        return child_node
    
    def _default_policy(self, board: Board):
        """默认策略：快速走子模拟"""
        temp_board = board.copy()
        
        # 快速随机走子直到游戏结束
        for _ in range(200):
            game_over, result = Rules.is_game_over(temp_board)
            if game_over:
                break
            legal_moves = Rules.get_legal_moves(temp_board)
            if not legal_moves:
                break
            
            if self.model:
                # 有模型时：使用模型辅助选择
                move = self._select_move_with_model(temp_board, legal_moves)
            else:
                # 无模型时：随机走子
                move = np.random.choice(legal_moves)
            
            temp_board.make_move(move)
        
        # 计算奖励
        return self._compute_reward(temp_board, board.current_player)
    
    def _select_move_with_model(self, board, moves):
        """使用模型评估选择走法"""
        best_move = None
        best_score = -float('inf')
        
        for move in moves:
            board.make_move(move)
            score = self._evaluate_board(board)
            board.undo_move()
            
            if board.current_player == Color.BLACK:
                score = -score
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else np.random.choice(moves)
    
    def _evaluate_board(self, board):
        """使用模型评估局面"""
        if self.model:
            from .dcnn_model import predict_board_score
            return predict_board_score(self.model, board.to_numpy())
        else:
            # 简单子力评估
            return self._simple_evaluation(board)
    
    def _simple_evaluation(self, board):
        """简单子力价值评估"""
        values = {
            1: 1000, 2: 10, 3: 10, 4: 40, 5: 90, 6: 45, 7: 10,
            -8: -1000, -9: -10, -10: -10, -11: -40, -12: -90, 
            -13: -45, -14: -10
        }
        score = 0
        for r in range(10):
            for c in range(9):
                p = board.board[r][c]
                if p != 0:
                    score += values.get(p, 0)
        return score / 1000.0
    
    def _compute_reward(self, board, original_player):
        """计算奖励"""
        game_over, result = Rules.is_game_over(board)
        
        if game_over:
            if result == "将死":
                # 检查是谁被将死
                if board.current_player == original_player:
                    return -1.0  # 我被将死
                else:
                    return 1.0  # 对方被将死
            else:
                return 0.0  # 困毙
        else:
            # 简单评估
            return self._simple_evaluation(board)
    
    def _backpropagate(self, node: MCTSNode, reward):
        """回传更新"""
        while node is not None:
            node.visits += 1
            
            # 根据节点所属玩家更新value
            if node.parent:
                # 如果是黑方回合，reward取反
                if node.parent.board.current_player == Color.BLACK:
                    reward = -reward
            
            node.value += reward
            node = node.parent
