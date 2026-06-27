# 监督学习训练脚本
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm

from model.dcnn_model import ChessDCNN
from training.data_preprocessor import DataPreprocessor
from training.reward import RewardFunction


class ChessDataset(Dataset):
    """象棋数据集"""
    def __init__(self, samples):
        self.samples = samples
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        state = torch.tensor(sample['state'], dtype=torch.float32)
        target = torch.tensor([sample['result']], dtype=torch.float32)
        return state, target


class SupervisedTrainer:
    """监督学习训练器"""
    
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=0.001)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 'min', patience=5, factor=0.5
        )
    
    def train(self, train_loader, val_loader=None, num_epochs=50, save_dir='models'):
        """训练模型"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        best_val_loss = float('inf')
        
        for epoch in range(num_epochs):
            self.model.train()
            train_loss = 0.0
            
            # 训练
            pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}")
            for states, targets in pbar:
                states = states.to(self.device)
                targets = targets.to(self.device)
                
                # 前向传播
                outputs = self.model(states)
                loss = self.criterion(outputs, targets)
                
                # 反向传播
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                train_loss += loss.item()
                pbar.set_postfix({'loss': loss.item()})
            
            train_loss /= len(train_loader)
            
            # 验证
            val_loss = 0.0
            if val_loader:
                val_loss = self.validate(val_loader)
                self.scheduler.step(val_loss)
            
            print(f"Epoch {epoch+1}, Train Loss: {train_loss:.6f}, "
                  f"Val Loss: {val_loss:.6f}")
            
            # 保存最佳模型
            if val_loader and val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_checkpoint(epoch + 1, save_dir, is_best=True)
            
            # 定期保存
            if (epoch + 1) % 10 == 0:
                self.save_checkpoint(epoch + 1, save_dir)
    
    def validate(self, val_loader):
        """验证"""
        self.model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for states, targets in val_loader:
                states = states.to(self.device)
                targets = targets.to(self.device)
                outputs = self.model(states)
                val_loss += self.criterion(outputs, targets).item()
        return val_loss / len(val_loader)
    
    def save_checkpoint(self, epoch, save_dir, is_best=False):
        """保存检查点"""
        filename = 'best_model.pth' if is_best else f'checkpoint_epoch{epoch}.pth'
        filepath = os.path.join(save_dir, filename)
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, filepath)
        print(f"检查点已保存: {filepath}")


def main():
    """主训练函数"""
    import sys
    sys.path.append('..')
    
    print("="*50)
    print("中国象棋AI - 监督学习训练")
    print("="*50)
    
    # 初始化
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用设备: {device}")
    
    # 创建模型
    model = ChessDCNN()
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")
    
    # 准备数据
    preprocessor = DataPreprocessor()
    print("\n生成演示数据集...")
    samples = preprocessor.create_dummy_dataset(num_games=50)
    
    if len(samples) == 0:
        print("没有训练数据！")
        return
    
    # 划分训练集和验证集
    split = int(0.8 * len(samples))
    train_samples = samples[:split]
    val_samples = samples[split:]
    
    train_dataset = ChessDataset(train_samples)
    val_dataset = ChessDataset(val_samples)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    print(f"\n训练集: {len(train_samples)}, 验证集: {len(val_samples)}")
    
    # 训练
    trainer = SupervisedTrainer(model, device)
    trainer.train(train_loader, val_loader, num_epochs=30)
    
    print("\n训练完成！")


if __name__ == "__main__":
    main()
