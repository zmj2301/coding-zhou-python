import random

# 全局字典用于存储迷宫数据
maze_dictionary = {}

# 检查并导入本地目录中的CSV文件
def import_local_maze_files():
    """检查本地目录中的CSV文件并导入到字典中"""
    import os
    import csv
    
    # 获取迷宫存储目录
    mazes_dir = os.path.join(os.getcwd(), 'mazes')
    
    # 如果目录不存在，创建它
    if not os.path.exists(mazes_dir):
        os.makedirs(mazes_dir)
    
    # 遍历mazes目录中的所有文件
    for file_name in os.listdir(mazes_dir):
        # 只处理CSV文件
        if file_name.endswith('.csv'):
            try:
                # 打开CSV文件
                file_path = os.path.join(mazes_dir, file_name)
                with open(file_path, 'r') as f:
                    reader = csv.reader(f)
                    maze_data = [list(map(int, row)) for row in reader]
                
                # 检查迷宫数据格式
                if maze_data and all(len(row) == len(maze_data[0]) for row in maze_data):
                    # 使用文件名作为迷宫名称（不包含扩展名）
                    maze_name = os.path.splitext(file_name)[0]
                    
                    # 只导入名称不重复的迷宫
                    if maze_name not in maze_dictionary:
                        # 查找起点和终点
                        start = (2, 1)  # 默认起点
                        end = (len(maze_data)-2, len(maze_data[0])-2)  # 默认终点
                        
                        # 在迷宫数据中查找实际的终点(3)
                        for i in range(len(maze_data)):
                            for j in range(len(maze_data[0])):
                                if maze_data[i][j] == 3:
                                    end = (i, j)
                                    break
                            if end != (len(maze_data)-2, len(maze_data[0])-2):
                                break
                        
                        # 添加到字典中
                        maze_dictionary[maze_name] = {
                            "data": maze_data,
                            "size": len(maze_data),
                            "start": start,
                            "end": end
                        }
                        print(f"已导入本地迷宫: {maze_name}")
                    else:
                        print(f"迷宫名称已存在，跳过导入: {maze_name}")
            except Exception as e:
                print(f"导入迷宫文件失败: {file_name}, 错误: {e}")

# 生成20x20的迷宫数据
def generate_maze(size=20, maze_name="default"):
    # 创建全墙迷宫
    maze = [[1 for _ in range(size)] for _ in range(size)]
    
    # 固定起点为(2,1)（行索引2，列索引1）
    start_x, start_y = 2, 1
    maze[start_x][start_y] = 0
    
    # 使用深度优先搜索生成迷宫
    stack = [(start_x, start_y)]
    directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]  # 四个方向，每次移动两步
    
    # 访问过的单元格
    visited = set()
    visited.add((start_x, start_y))
    
    while stack:
        x, y = stack[-1]
        random.shuffle(directions)
        found = False
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            # 检查是否在边界内且未访问
            if 0 < nx < size-1 and 0 < ny < size-1 and maze[nx][ny] == 1:
                # 打通当前位置到新位置的墙
                maze[nx][ny] = 0
                maze[x + dx//2][y + dy//2] = 0
                stack.append((nx, ny))
                visited.add((nx, ny))
                found = True
                break
        
        if not found:
            stack.pop()
    
    # 收集所有可通行的单元格
    passable_cells = [(i, j) for i in range(size) for j in range(size) if maze[i][j] == 0]
    
    # 选择一个距离起点较远的可通行单元格作为终点
    # 计算每个可通行单元格到起点的曼哈顿距离
    distances = [abs(i - start_x) + abs(j - start_y) for i, j in passable_cells]
    # 选择距离最远的5个单元格之一作为终点
    max_distance = max(distances)
    candidate_endpoints = [cell for cell, distance in zip(passable_cells, distances) if distance >= max_distance * 0.8]
    
    if candidate_endpoints:
        end_x, end_y = random.choice(candidate_endpoints)
        maze[end_x][end_y] = 3
    else:
        # 如果没有足够远的单元格，随机选择一个
        end_x, end_y = random.choice(passable_cells)
        maze[end_x][end_y] = 3
    
    # 将迷宫数据保存到字典中
    maze_dictionary[maze_name] = {
        "data": maze,
        "size": size,
        "start": (start_x, start_y),
        "end": (end_x, end_y)
    }
    
    return maze

# 从字典中获取迷宫数据
def get_maze(maze_name="default"):
    return maze_dictionary.get(maze_name, None)

# 列出所有迷宫名称
def list_mazes():
    return list(maze_dictionary.keys())

# 删除指定名称的迷宫
def delete_maze(maze_name="default"):
    if maze_name in maze_dictionary:
        del maze_dictionary[maze_name]
        return True
    return False

# 重命名迷宫
def rename_maze(old_name, new_name):
    if old_name in maze_dictionary and new_name not in maze_dictionary:
        # 获取旧迷宫数据
        maze_data = maze_dictionary[old_name]
        # 删除旧名称的迷宫
        del maze_dictionary[old_name]
        # 用新名称保存迷宫数据
        maze_dictionary[new_name] = maze_data
        return True
    return False

# 将迷宫转换为字符串格式（用于预览或导出）
def maze_to_string(maze):
    return '\n'.join([','.join(map(str, row)) for row in maze])

# 在模块导入时自动检查并导入本地迷宫文件
import_local_maze_files()

if __name__ == "__main__":
    # 生成默认迷宫（如果不存在）
    if "default" not in maze_dictionary:
        maze = generate_maze(20, "default")
    else:
        maze = maze_dictionary["default"]["data"]
    
    # 生成另一个迷宫（如果不存在）
    if "test_maze" not in maze_dictionary:
        maze2 = generate_maze(20, "test_maze")
    else:
        maze2 = maze_dictionary["test_maze"]["data"]
    
    print(f"已生成迷宫: {list_mazes()}")
    print(f"默认迷宫大小: {maze_dictionary['default']['size']}x{maze_dictionary['default']['size']}")
    print(f"默认迷宫起点: {maze_dictionary['default']['start']}")
    print(f"默认迷宫终点: {maze_dictionary['default']['end']}")
    
    # 打印迷宫预览
    print("\n迷宫预览:")
    for row in maze:
        print(''.join(['█' if cell == 1 else ' ' if cell == 0 else '3' for cell in row]))
    
    # 测试获取迷宫
    retrieved_maze = get_maze("default")
    if retrieved_maze:
        print(f"\n成功获取默认迷宫，大小: {retrieved_maze['size']}x{retrieved_maze['size']}")
    
    # 测试删除迷宫
    delete_maze("test_maze")
    print(f"删除后剩余迷宫: {list_mazes()}")
