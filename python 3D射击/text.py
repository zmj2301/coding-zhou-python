# 将迷宫数据转换为图片
from PIL import Image, ImageDraw
import csv

# 读取迷宫数据
def read_maze_data(filename):
    maze = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            maze.append([int(cell) for cell in row])
    return maze

# 将迷宫数据转换为图片
def maze_to_image(maze, output_filename):
    # 设置图片尺寸
    cell_size = 20  # 每个单元格的像素大小
    width = len(maze[0]) * cell_size
    height = len(maze) * cell_size
    
    # 创建新图片
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 定义颜色映射
    colors = {
        0: (255, 255, 255),  # 可通行区域 - 白色
        1: (0, 0, 0),        # 墙 - 黑色
        3: (212,224,232)       # 终点 - 灰色
    }
    
    # 绘制迷宫
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            color = colors.get(cell, (255, 255, 255))
            draw.rectangle(
                [(x * cell_size, y * cell_size), 
                 ((x + 1) * cell_size, (y + 1) * cell_size)],
                fill=color
            )
    
    # 保存图片
    image.show(output_filename)
    print(f"迷宫图片已生成: {output_filename}")

# 主函数
if __name__ == "__main__":
    # 读取迷宫数据
    maze_data = read_maze_data('maze_data.csv')
    
    # 转换为图片
    maze_to_image(maze_data, 'maze_image.png')