from torch import nn

# 定义线性层，输入维度为5，输出维度为3
linear = nn.Linear(5, 3)

result = linear.state_dict()

# n维向量是一个包含n个数，每个元素的维度为1
# n维张量是一个n维数组，每个元素的维度为n

from torch import Tensor

input = Tensor([[1, 2, 3, 4, 5]])

import torchvision

train_data = torchvision.datasets.MNIST(root='./dataset',
 train=True, 
 download=True)
test_data = torchvision.datasets.MNIST(root='./dataset',
 train=False, 
 download=True)

# 将测试数据展平为2维张量，每个样本为784个像素
flat_test_data = trat_data.view(-1, 784)

float_flat_test_data = flat_test_data.float() / 255.0
# 归一化到[0, 1]范围
print(float_flat_test_data)

class MnistModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.linear2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.linear3 = nn.Linear(128, 10)
    
    # forward 方法定义了模型的前向传播过程,自动调用每个层的 forward 方法,并返回最终的输出
    def forward(self, x):
        x = self.linear(x)
        x = self.relu(x)
        x = self.linear2(x)
        x = self.relu2(x)
        x = self.linear3(x)
        return x