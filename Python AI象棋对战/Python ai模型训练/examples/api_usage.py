# API使用示例
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath('..'))

from api.chess_ai_api import ChessAIApi
from replay.recorder import GameRecorder
from replay.analyzer import PositionAnalyzer
from replay.visualizer import GameVisualizer
import matplotlib.pyplot as plt


def example_basic_usage():
    """基本API使用示例"""
    print("="*50)
    print("示例1: 基本API使用")
    print("="*50)
    
    # 初始化AI（中等难度）
    api = ChessAIApi(difficulty=2)
    
    # 打印初始棋盘
    print("\n初始棋盘:")
    api.print_board()
    
    # 让AI走一步
    print("\nAI思考中...")
    move_info = api.get_best_move()
    
    if move_info:
        print(f"AI选择走法: {move_info['ucci']}")
        api.make_move(move_info['move'])
        print("\nAI走棋后:")
        api.print_board()
    
    # 评估局面
    score = api.evaluate_position()
    print(f"\n当前局面评分: {score:.4f}")


def example_game_play():
    """游戏对弈和复盘示例"""
    print("\n" + "="*50)
    print("示例2: 游戏对弈和复盘")
    print("="*50)
    
    api = ChessAIApi(difficulty=1)
    recorder = GameRecorder()
    analyzer = PositionAnalyzer()
    
    # 演示几回合
    print("\n演示对弈开始:")
    for i in range(5):
        print(f"\n回合 {i+1}:")
        
        # AI走棋
        move_info = api.get_best_move()
        if not move_info:
            break
        
        print(f"AI走法: {move_info['ucci']}")
        
        # 记录
        score = api.evaluate_position()
        recorder.record_move(move_info['move'], score)
        
        # 执行
        api.make_move(move_info['move'])
        
        # 检查游戏状态
        game_over, reason = api.is_game_over()
        if game_over:
            print(f"游戏结束: {reason}")
            break
    
    # 分析和复盘
    print("\n分析对局...")
    analysis = analyzer.analyze_game(recorder.get_all_records())
    
    # 生成报告
    game_info = recorder.get_game_info()
    GameVisualizer.generate_html_report(game_info, analysis)
    
    # 绘制评分曲线
    scores = [a['evaluation'] for a in analysis]
    GameVisualizer.plot_score_curve(scores)
    plt.savefig('score_curve.png')
    print("\n评分曲线已保存: score_curve.png")
    
    # 保存游戏
    saved_path = recorder.save_game()
    print(f"游戏记录已保存: {saved_path}")


def example_async_usage():
    """异步API使用示例"""
    print("\n" + "="*50)
    print("示例3: 异步API使用")
    print("="*50)
    
    import asyncio
    from api.async_api import AsyncChessAIApi
    
    async def async_game():
        api = AsyncChessAIApi(difficulty=1)
        
        print("\n异步获取AI走法...")
        move_info = await api.get_best_move_async()
        
        if move_info:
            print(f"AI走法: {move_info['ucci']}")
    
    asyncio.run(async_game())


if __name__ == "__main__":
    print("中国象棋AI - API使用示例\n")
    
    # 运行示例
    example_basic_usage()
    example_game_play()
    example_async_usage()
    
    print("\n" + "="*50)
    print("所有示例运行完成！")
    print("="*50)
