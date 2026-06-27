# 中国象棋AI - 演示脚本
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header():
    print("="*60)
    print("          中国象棋AI - 自动对弈系统")
    print("="*60)
    print()


def main():
    print_header()
    
    print("正在初始化...")
    
    try:
        from api.chess_ai_api import ChessAIApi
    except Exception as e:
        print(f"导入错误: {e}")
        print("请确保已安装依赖: pip install -r requirements.txt")
        return
    
    # 初始化AI
    print("初始化AI（难度: 中等）...")
    api = ChessAIApi(difficulty=2)
    
    print()
    print("初始棋盘:")
    api.print_board()
    
    # 演示AI自己对弈
    print("\n" + "="*60)
    print("AI自我对弈演示")
    print("="*60)
    
    for step in range(1, 6):
        print(f"\n第 {step} 步:")
        
        # AI走棋
        print("AI思考中...")
        move_info = api.get_best_move()
        
        if not move_info:
            print("无合法走法！游戏结束。")
            break
        
        print(f"AI走法: {move_info['ucci']}")
        
        # 执行走法
        api.make_move(move_info['move'])
        
        # 打印棋盘
        print("\n当前棋盘:")
        api.print_board()
        
        # 评估局面
        score = api.evaluate_position()
        print(f"\n局面评分: {score:.4f}")
        
        # 检查游戏状态
        game_over, reason = api.is_game_over()
        if game_over:
            print(f"\n游戏结束: {reason}")
            break
    
    print("\n" + "="*60)
    print("演示完成！")
    print("="*60)
    print("\n查看 examples/api_usage.py 了解更多使用方法")


if __name__ == "__main__":
    main()
