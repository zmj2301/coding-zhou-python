# 强化学习训练脚本
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import random
import numpy as np
from collections import deque
from tqdm import tqdm
from model.dcnn_model import ChessDCNN, predict_board_score
from model.agent import ChessAI
from core.board import Board
from core.rules import Rules
from training.reward import RewardFunction


class ReplayBuffer:
    """经验回放缓冲区"""
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        return zip(*batch)
    
    def __len__(self):
        return len(self.buffer)


class RLTrainer:
    """强化学习训练器"""
    
    def __init__(self, model, target_model, device='cpu'):
        self.model = model
        self.target_model = target_model
        self.device = device
        self.model.to(device)
        self.target_model.to(device)
        
        self.optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
        self.criterion = torch.nn.MSELoss()
        self.replay_buffer = ReplayBuffer(10000)
        
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995
    
    def train_step(self, batch_size=64):
        """训练一步"""
        if len(self.replay_buffer) < batch_size:
            return 0.0
        
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)
        
        states = torch.FloatTensor(np.array(states)).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # 当前Q值
        current_q = self.model(states)
        
        # 目标Q值
        with torch.no_grad():
            next_q = self.target_model(next_states)
            max_next_q, _ = torch.max(next_q, 1)
            target_q = rewards + (1 - dones) * self.gamma * max_next_q
        
        # 计算损失
        loss = self.criterion(current_q, target_q.unsqueeze(1))
        
        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # 更新epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def update_target_network(self):
        """更新目标网络"""
        self.target_model.load_state_dict(self.model.state_dict())
    
    def self_play(self, num_games=10):
        """自我对弈收集经验"""
        for _ in tqdm(range(num_games), desc="自我对弈"):
            board = Board()
            done = False
            game_history = []
            
            while not done:
                state = self._encode_state(board)
                legal_moves = Rules.get_legal_moves(board)
                
                if not legal_moves:
                    break
                
                # Epsilon-greedy选择走法
                if random.random() < self.epsilon:
                    move = random.choice(legal_moves)
                else:
                    move = self._select_best_move(board, legal_moves)
                
                # 执行走法
                prev_board = board.copy()
                board.make_move(move)
                
                # 计算奖励
                reward = RewardFunction.compute_reward(board, prev_board)
                game_over, _ = Rules.is_game_over(board)
                
                # 保存经验
                next_state = self._encode_state(board)
                game_history.append((state, move, reward, next_state, game_over))
                
                done = game_over
            
            # 将经验存入回放缓冲区
            for state, move, reward, next_state, done in game_history:
                self.replay_buffer.push(state, 0, reward, next_state, done)
    
    def _encode_state(self, board):
        """编码局面状态"""
        from ..model.dcnn_model import encode_board
        return encode_board(board.to_numpy())
    
    def _select_best_move(self, board, moves):
        """选择最佳走法"""
        best_move = None
        best_score = -float('inf')
        
        for move in moves:
            board.make_move(move)
            score = predict_board_score(self.model, board.to_numpy(), self.device)
            board.undo_move()
            
            if board.current_player == Board.BLACK:
                score = -score
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move if best_move else random.choice(moves)


def main():
    """强化学习训练主函数"""
    print("="*50)
    print("中国象棋AI - 强化学习训练")
    print("="*50)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用设备: {device}")
    
    # 创建模型
    model = ChessDCNN()
    target_model = ChessDCNN()
    target_model.load_state_dict(model.state_dict())
    
    trainer = RLTrainer(model, target_model, device)
    
    # 训练循环
    num_iterations = 100
    for i in range(num_iterations):
        print(f"\n迭代 {i+1}/{num_iterations}")
        
        # 自我对弈收集经验
        trainer.self_play(num_games=5)
        
        # 训练
        total_loss = 0.0
        for _ in range(100):
            loss = trainer.train_step(batch_size=32)
            total_loss += loss
        
        avg_loss = total_loss / 100 if total_loss > 0 else 0
        print(f"平均损失: {avg_loss:.6f}, Epsilon: {trainer.epsilon:.3f}")
        
        # 更新目标网络
        if (i + 1) % 10 == 0:
            trainer.update_target_network()
            print("目标网络已更新")


if __name__ == "__main__":
    main()
