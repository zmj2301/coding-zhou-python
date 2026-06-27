# 中国象棋AI - 基础测试脚本
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试导入"""
    print("="*50)
    print("测试1: 模块导入")
    print("="*50)
    
    try:
        from core.board import Board
        from core.rules import Rules
        from core.move import Move
        print("✓ core模块导入成功")
        
        from model.agent import ChessAI
        print("✓ model模块导入成功")
        
        from api.chess_ai_api import ChessAIApi
        print("✓ api模块导入成功")
        
        from training.reward import RewardFunction
        print("✓ training模块导入成功")
        
        from replay.recorder import GameRecorder
        print("✓ replay模块导入成功")
        
        print("\n所有模块导入成功！\n")
        return True
        
    except Exception as e:
        print(f"✗ 导入失败: {e}\n")
        return False


def test_board():
    """测试棋盘功能"""
    print("="*50)
    print("测试2: 棋盘功能")
    print("="*50)
    
    try:
        from core.board import Board
        
        board = Board()
        print("✓ 棋盘初始化成功")
        
        # 测试初始局面
        board_state = board.to_numpy()
        assert board_state.shape == (10, 9)
        print(f"✓ 棋盘形状正确: {board_state.shape}")
        
        print("棋盘功能测试通过！\n")
        return True
        
    except Exception as e:
        print(f"✗ 棋盘测试失败: {e}\n")
        return False


def test_rules():
    """测试规则"""
    print("="*50)
    print("测试3: 规则功能")
    print("="*50)
    
    try:
        from core.board import Board
        from core.rules import Rules
        
        board = Board()
        
        # 测试合法走法
        legal_moves = Rules.get_legal_moves(board)
        print(f"✓ 初始局面有 {len(legal_moves)} 个合法走法")
        
        # 测试将军检测
        in_check = Rules.is_in_check(board)
        print(f"✓ 初始局面将军状态: {in_check}")
        
        # 测试游戏结束
        game_over, reason = Rules.is_game_over(board)
        print(f"✓ 初始局面游戏状态: {game_over}")
        
        print("规则功能测试通过！\n")
        return True
        
    except Exception as e:
        print(f"✗ 规则测试失败: {e}\n")
        return False


def test_api():
    """测试API"""
    print("="*50)
    print("测试4: API功能")
    print("="*50)
    
    try:
        from api.chess_ai_api import ChessAIApi
        
        # 初始化API
        api = ChessAIApi(difficulty=1)
        print("✓ API初始化成功")
        
        # 测试获取走法
        print("获取AI走法（可能需要几秒钟）...")
        move_info = api.get_best_move()
        
        if move_info:
            print(f"✓ AI走法: {move_info['ucci']}")
            print(f"  从: {move_info['from']}")
            print(f"  到: {move_info['to']}")
            
            # 执行走法
            api.make_move(move_info['move'])
            print("✓ 走法执行成功")
            
        # 测试局面评估
        score = api.evaluate_position()
        print(f"✓ 局面评分: {score:.4f}")
        
        print("API功能测试通过！\n")
        return True
        
    except Exception as e:
        print(f"✗ API测试失败: {e}\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("   中国象棋AI - 基础测试")
    print("="*50 + "\n")
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("棋盘功能", test_board()))
    results.append(("规则功能", test_rules()))
    results.append(("API功能", test_api()))
    
    print("="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！项目运行正常！\n")
    else:
        print(f"\n⚠️ 有 {len(results) - passed} 个测试失败\n")


if __name__ == "__main__":
    main()
