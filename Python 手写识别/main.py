import torch
import torchvision
from torch import nn, Tensor
from PIL.Image import Image
from torchvision.transforms import functional
from torch.utils.data import DataLoader
from torch import argmax

def img_preprocess(img: Image) -> Tensor:
    img = functional.to_tensor(img)
    img = img.view(28 * 28)
    return img

mnist = torchvision.datasets.MNIST(
    root='./dataset',
    download=True,
    transform=img_preprocess)

dataloader = DataLoader(
    dataset=mnist,
    batch_size=64, 
    shuffle=True)


# 打印图片
"""import matplotlib.pyplot as plt
plt.imshow(mnist[90],cmap='gray')
plt.show()"""

class MnistModel(nn.Module):
    def __init__(self) -> None:

        super().__init__()

        self.layer1 = nn.Linear(784, 256)
        self.relu1 = nn.ReLU()
        self.layer2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.layer3 = nn.Linear(128, 10)
    
    def forward(self, x) -> Tensor:
        x = self.relu1(self.layer1(x))
        x = self.relu2(self.layer2(x))
        x = self.layer3(x)
        return x

criterion = torch.nn.CrossEntropyLoss()

logits: Tensor = torch.tensor(
    [
        [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,0.0],
        [1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8,9.9,0.0]
    ]
)
labels: Tensor = torch.tensor(
    [0,2],
    dtype=torch.long)

mnist_model = MnistModel()
learning_rate = 0.01
epoch = 5

for _ in range(epoch):
    for images,labels in dataloader:
        logits = mnist_model(images)
        loss = criterion(logits, labels)

        mnist_model.zero_grad()
        loss.backward()

        with torch.no_grad():
            for param in mnist_model.parameters():
                if param.grad is not None:
                    param.data -= learning_rate * param.grad

data, _ = mnist[90]  # mnist 返回 (image, label) 元组
logits = mnist_model(data.unsqueeze(0))  # 添加 batch 维度
print(logits)
