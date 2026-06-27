# DCNN棋力评估网络模型
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class ChessDCNN(nn.Module):
    """
    中国象棋DCNN棋力评估网络
    输入：10×9×N 的局面编码
    输出：局面评分（范围：[-1, 1]，1表示红方绝对优势）
    """
    
    def __init__(self, input_channels=14, num_filters=[64, 128, 256], 
                 hidden_size=512):
        super(ChessDCNN, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(input_channels, num_filters[0], 
                              kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(num_filters[0], num_filters[1], 
                              kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(num_filters[1], num_filters[2], 
                              kernel_size=3, padding=1)
        
        # 批归一化
        self.bn1 = nn.BatchNorm2d(num_filters[0])
        self.bn2 = nn.BatchNorm2d(num_filters[1])
        self.bn3 = nn.BatchNorm2d(num_filters[2])
        
        # 全连接层
        self.fc1 = nn.Linear(num_filters[2] * 10 * 9, hidden_size)
        self.fc2 = nn.Linear(hidden_size, 1)
        
        # Dropout用于防止过拟合
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        # 卷积层1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        
        # 卷积层2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        
        # 卷积层3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # 展平
        x = x.view(x.size(0), -1)
        
        # 全连接层
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        
        # 使用tanh输出[-1,1]范围的评分
        x = torch.tanh(x)
        return x


def encode_board(board_state):
    """
    将棋盘状态编码为神经网络输入格式
    编码为14个通道的10×9特征图
    """
    encoded = np.zeros((14, 10, 9), dtype=np.float32)
    
    piece_map = {
        1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,  # 红方
        -8: 7, -9: 8, -10: 9, -11: 10, -12: 11, -13: 12, -14: 13  # 黑方
    }
    
    for r in range(10):
        for c in range(9):
            piece = board_state[r][c]
            if piece != 0 and piece in piece_map:
                channel = piece_map[piece]
                encoded[channel][r][c] = 1.0
    
    return encoded


def predict_board_score(model, board_state, device='cpu'):
    """
    使用模型预测局面评分
    返回值：正数表示红方优势，负数表示黑方优势
    """
    model.eval()
    encoded = encode_board(board_state)
    x = torch.tensor(encoded).unsqueeze(0).to(device)
    
    with torch.no_grad():
        score = model(x).item()
    
    return score
