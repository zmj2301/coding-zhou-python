import unittest
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟Pygame初始化，避免测试时需要Pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # 防止Pygame初始化显示

# 导入需要测试的模块
from card_game import GameState, get_card_pattern, Check_qualified, Check_qualified_basic

class TestGameState(unittest.TestCase):
    """测试游戏状态管理"""
    
    def setUp(self):
        """设置测试环境"""
        self.game_state = GameState()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertIsNone(self.game_state.last_play)
        self.assertEqual(self.game_state.current_turn, 'player')
        self.assertEqual(self.game_state.produce_history, [])
        self.assertFalse(self.game_state.game_over)
        self.assertIsNone(self.game_state.winner)
    
    def test_update_last_play(self):
        """测试更新上一次有效出牌"""
        self.game_state.update_last_play("AI", "pair", 5)
        self.assertEqual(self.game_state.last_play, ("AI", "pair", 5))
    
    def test_reset_last_play(self):
        """测试重置上一次有效出牌"""
        self.game_state.update_last_play("AI", "pair", 5)
        self.game_state.reset_last_play()
        self.assertIsNone(self.game_state.last_play)
    
    def test_add_produce(self):
        """测试添加出牌记录"""
        self.game_state.add_produce("玩家", "3 3")
        self.assertEqual(self.game_state.produce_history, ["玩家：3 3"])
        
        self.game_state.add_produce("AI", "4 4")
        self.assertEqual(self.game_state.produce_history, ["玩家：3 3", "AI：4 4"])
    
    def test_get_last_valid_play(self):
        """测试获取最近的一次有效出牌"""
        # 初始情况，没有出牌记录
        self.assertIsNone(self.game_state.get_last_valid_play())
        
        # 添加有效出牌
        self.game_state.add_produce("玩家", "3 3")
        self.assertEqual(self.game_state.get_last_valid_play(), "玩家：3 3")
        
        # 添加AI不出牌
        self.game_state.add_produce("AI", "不出")
        self.assertEqual(self.game_state.get_last_valid_play(), "玩家：3 3")
        
        # 添加新的有效出牌
        self.game_state.add_produce("玩家", "5 5")
        self.assertEqual(self.game_state.get_last_valid_play(), "玩家：5 5")
    
    def test_switch_turn(self):
        """测试切换当前出牌玩家"""
        self.assertEqual(self.game_state.current_turn, 'player')
        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, 'ai')
        self.game_state.switch_turn()
        self.assertEqual(self.game_state.current_turn, 'player')
    
    def test_set_game_over(self):
        """测试设置游戏结束"""
        self.game_state.set_game_over("AI")
        self.assertTrue(self.game_state.game_over)
        self.assertEqual(self.game_state.winner, "AI")

class TestLastPlayHandling(unittest.TestCase):
    """测试last_play状态管理"""
    
    def setUp(self):
        """设置测试环境"""
        self.game_state = GameState()
    
    def test_first_play(self):
        """测试第一次出牌"""
        # 第一次出牌，last_play为None，应该允许任何合法牌型
        player_play = ['5']
        self.assertTrue(Check_qualified(player_play, None))
        
        # 更新last_play
        pattern, main_val = get_card_pattern(player_play)
        self.game_state.update_last_play("玩家", pattern, main_val)
        self.assertEqual(self.game_state.last_play, ("玩家", "single", 5))
    
    def test_same_pattern_higher_value(self):
        """测试相同牌型，更高值"""
        # AI出对三
        ai_play = ['3', '3']
        ai_pattern, ai_main_val = get_card_pattern(ai_play)
        self.game_state.update_last_play("AI", ai_pattern, ai_main_val)
        
        # 玩家出对四，应该允许
        player_play = ['4', '4']
        self.assertTrue(Check_qualified(player_play, self.game_state.last_play))
        
        # 玩家出对二，应该允许
        player_play = ['2', '2']
        self.assertTrue(Check_qualified(player_play, self.game_state.last_play))
    
    def test_different_pattern(self):
        """测试不同牌型"""
        # AI出对三
        ai_play = ['3', '3']
        ai_pattern, ai_main_val = get_card_pattern(ai_play)
        self.game_state.update_last_play("AI", ai_pattern, ai_main_val)
        
        # 玩家出单张5，牌型不同，应该不允许
        player_play = ['5']
        self.assertFalse(Check_qualified(player_play, self.game_state.last_play))
        
        # 玩家出三条5，牌型不同，应该不允许
        player_play = ['5', '5', '5']
        self.assertFalse(Check_qualified(player_play, self.game_state.last_play))
    
    def test_same_pattern_lower_value(self):
        """测试相同牌型，更低值"""
        # AI出对五
        ai_play = ['5', '5']
        ai_pattern, ai_main_val = get_card_pattern(ai_play)
        self.game_state.update_last_play("AI", ai_pattern, ai_main_val)
        
        # 玩家出对三，牌值更低，应该不允许
        player_play = ['3', '3']
        self.assertFalse(Check_qualified(player_play, self.game_state.last_play))

class TestAIPassHandling(unittest.TestCase):
    """测试AI不出牌场景"""
    
    def setUp(self):
        """设置测试环境"""
        self.game_state = GameState()
    
    def test_ai_pass(self):
        """测试AI不出牌"""
        # 记录AI不出牌
        self.game_state.add_produce("AI", "不出")
        self.assertEqual(self.game_state.produce_history, ["AI：不出"])
        
        # 最近的有效出牌应该是None
        self.assertIsNone(self.game_state.get_last_valid_play())
    
    def test_consecutive_passes(self):
        """测试连续不出牌"""
        # 玩家出对三
        self.game_state.add_produce("玩家", "3 3")
        pattern, main_val = get_card_pattern(["3", "3"])
        self.game_state.update_last_play("玩家", pattern, main_val)
        
        # AI不出牌
        self.game_state.add_produce("AI", "不出")
        
        # 玩家再出对五
        self.game_state.add_produce("玩家", "5 5")
        pattern, main_val = get_card_pattern(["5", "5"])
        self.game_state.update_last_play("玩家", pattern, main_val)
        
        # AI不出牌
        self.game_state.add_produce("AI", "不出")
        
        # 最近的有效出牌应该是玩家的对五
        self.assertEqual(self.game_state.get_last_valid_play(), "玩家：5 5")
    
    def test_pass_after_valid_play(self):
        """测试有效出牌后的不出牌"""
        # 玩家出单张3
        player_play = ['3']
        pattern, main_val = get_card_pattern(player_play)
        self.game_state.update_last_play("玩家", pattern, main_val)
        self.game_state.add_produce("玩家", "3")
        
        # AI不出牌，记录但不更新last_play
        self.game_state.add_produce("AI", "不出")
        
        # 玩家出单张5，应该允许（牌型相同，值更大）
        player_play = ['5']
        self.assertTrue(Check_qualified(player_play, self.game_state.last_play))

class TestCardPatterns(unittest.TestCase):
    """测试牌型识别和合法性检查"""
    
    def test_get_card_pattern(self):
        """测试牌型识别"""
        # 单牌
        self.assertEqual(get_card_pattern(['5']), ("single", 5))
        
        # 对子
        self.assertEqual(get_card_pattern(['5', '5']), ("pair", 5))
        
        # 三条
        self.assertEqual(get_card_pattern(['5', '5', '5']), ("triple", 5))
        
        # 四条
        self.assertEqual(get_card_pattern(['5', '5', '5', '5']), ("four_of_a_kind", 5))
        
        # 王炸
        self.assertEqual(get_card_pattern(['15', '16']), ("bomb", 100))
        
        # 无效牌型
        self.assertEqual(get_card_pattern(['5', '6']), (None, None))
    
    def test_check_qualified_basic(self):
        """测试基本牌型检查"""
        # 单牌
        self.assertTrue(Check_qualified_basic(['5']))
        
        # 对子
        self.assertTrue(Check_qualified_basic(['5', '5']))
        
        # 三条
        self.assertTrue(Check_qualified_basic(['5', '5', '5']))
        
        # 四条
        self.assertTrue(Check_qualified_basic(['5', '5', '5', '5']))
        
        # 无效牌型
        self.assertFalse(Check_qualified_basic(['5', '6', '7', '9']))

if __name__ == '__main__':
    unittest.main()
