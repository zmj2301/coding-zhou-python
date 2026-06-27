import random
import pygame
import math
import os
from collections import Counter

# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file)

class Card:
    """扑克牌类，表示单张扑克牌"""
    
    def __init__(self, card_id):
        """初始化卡牌
        
        Args:
            card_id: 卡牌ID，1-54，其中53是小王，54是大王
        """
        self.id = card_id  # 1-54，53=小王，54=大王
        
        # 计算卡牌值
        if card_id <= 52:
            # 普通卡牌，1-52
            # 1-13: 黑桃，14-26: 红桃，27-39: 梅花，40-52: 方块
            self.value = (card_id - 1) % 13 + 1
        else:
            # 王
            self.value = 15 if card_id == 53 else 16  # 15=小王，16=大王
    
    def __str__(self):
        """返回卡牌的字符串表示"""
        return f"Card(id={self.id}, value={self.value})"
    
    def __repr__(self):
        """返回卡牌的repr表示"""
        return self.__str__()
    
    def __eq__(self, other):
        """比较两张卡牌是否相等"""
        if isinstance(other, Card):
            return self.id == other.id
        return False
    
    def __lt__(self, other):
        """比较两张卡牌的大小"""
        if isinstance(other, Card):
            return self.value < other.value
        return False

class Deck:
    """牌堆类，负责洗牌和发牌"""
    
    def __init__(self):
        """初始化牌堆"""
        # 创建54张卡牌
        self.cards = [Card(i) for i in range(1, 55)]
        # 不默认洗牌，保持初始顺序一致，方便测试
    
    def shuffle(self):
        """洗牌"""
        random.shuffle(self.cards)
    
    def deal(self, num):
        """发牌
        
        Args:
            num: 要发的牌的数量
            
        Returns:
            list: 发的牌
        """
        if num > len(self.cards):
            raise ValueError("牌堆中的牌不足")
        
        dealt_cards = self.cards[:num]
        self.cards = self.cards[num:]
        return dealt_cards
    
    def __len__(self):
        """返回牌堆中剩余的牌的数量"""
        return len(self.cards)

class Player:
    """玩家类，包含玩家的牌和基本操作"""
    
    def __init__(self, name):
        """初始化玩家
        
        Args:
            name: 玩家名称
        """
        self.name = name
        self.cards = []  # 玩家手中的牌
        self.full_cards = []  # 玩家手中的完整卡牌ID
        
    def add_cards(self, cards):
        """添加卡牌
        
        Args:
            cards: 要添加的卡牌列表
        """
        self.cards.extend(cards)
        self.full_cards.extend([card.id for card in cards])
        # 按卡牌值排序
        self.sort_cards()
    
    def remove_card(self, card):
        """移除卡牌
        
        Args:
            card: 要移除的卡牌
            
        Returns:
            bool: 是否成功移除
        """
        if card in self.cards:
            index = self.cards.index(card)
            self.cards.pop(index)
            self.full_cards.pop(index)
            return True
        return False
    
    def remove_cards_by_value(self, values):
        """根据值移除卡牌
        
        Args:
            values: 要移除的卡牌值列表
            
        Returns:
            list: 移除的卡牌
        """
        removed_cards = []
        values_copy = values.copy()
        
        for card in list(self.cards):
            if card.value in values_copy:
                self.remove_card(card)
                removed_cards.append(card)
                values_copy.remove(card.value)
        
        return removed_cards
    
    def sort_cards(self):
        """按卡牌值排序"""
        # 组合两个列表，按值排序
        combined = list(zip(self.cards, self.full_cards))
        combined.sort(key=lambda x: x[0].value)
        # 分离排序后的列表
        self.cards = [x[0] for x in combined]
        self.full_cards = [x[1] for x in combined]
    
    def get_card_values(self):
        """获取卡牌值列表
        
        Returns:
            list: 卡牌值列表
        """
        return [card.value for card in self.cards]
    
    def __str__(self):
        """返回玩家的字符串表示"""
        return f"Player(name={self.name}, cards={self.get_card_values()})"
    
    def __repr__(self):
        """返回玩家的repr表示"""
        return self.__str__()

class HumanPlayer(Player):
    """人类玩家类，继承自Player"""
    
    def __init__(self, name):
        """初始化人类玩家
        
        Args:
            name: 玩家名称
        """
        super().__init__(name)
    
    def select_cards(self, selected_ids):
        """选择要出的牌
        
        Args:
            selected_ids: 选择的卡牌ID列表
            
        Returns:
            list: 选择的卡牌
        """
        selected_cards = []
        
        for card_id in selected_ids:
            for card in self.cards:
                if card.id == card_id and card not in selected_cards:
                    selected_cards.append(card)
                    break
        
        return selected_cards

class AIPlayer(Player):
    """AI玩家类，继承自Player，实现AI出牌逻辑"""
    
    def __init__(self, name):
        """初始化AI玩家
        
        Args:
            name: AI玩家名称
        """
        super().__init__(name)
    
    def get_card_pattern(self, card_values):
        """识别牌型，返回牌型名称和用于比较的主值
        
        Args:
            card_values: 卡牌值列表
            
        Returns:
            tuple: (牌型名称, 主值)，如果牌型无效则返回(None, None)
        """
        # 确保是整数列表且已排序
        card_list = sorted(int(card) for card in card_values)
        
        # 单牌
        if len(card_list) == 1:
            return "single", card_list[0]
        
        # 对子
        if len(card_list) == 2:
            if card_list[0] == card_list[1]:
                return "pair", card_list[0]
            if set(card_list) == {15, 16}:
                return "bomb", 100  # 王炸，最大
            return None, None
        
        # 三条
        if len(card_list) == 3:
            if card_list[0] == card_list[1] == card_list[2]:
                return "triple", card_list[0]
            return None, None
        
        # 三带一或四条
        if len(card_list) == 4:
            # 四条
            if card_list[0] == card_list[3]:
                return "four_of_a_kind", card_list[0]
            # 三带一
            if card_list[0] == card_list[1] == card_list[2] or card_list[1] == card_list[2] == card_list[3]:
                triple_val = card_list[0] if card_list[0] == card_list[1] == card_list[2] else card_list[3]
                return "three_with_one", triple_val
            # 连续两对
            if card_list[0] == card_list[1] and card_list[2] == card_list[3] and card_list[2] == card_list[1] + 1:
                return "consecutive_pair", card_list[2]  # 返回较大的一对值
            return None, None
        
        # 三带二
        if len(card_list) == 5:
            # 检查是否为三条+一对
            if (card_list[0] == card_list[1] == card_list[2] and card_list[3] == card_list[4]) or \
               (card_list[0] == card_list[1] and card_list[2] == card_list[3] == card_list[4]):
                triple_val = card_list[0] if card_list[0] == card_list[1] == card_list[2] else card_list[4]
                return "three_with_two", triple_val
            # 检查是否为顺子
            if 2 not in card_list and len(set(card_list)) == len(card_list):
                is_straight = True
                for i in range(1, len(card_list)):
                    if card_list[i] != card_list[i-1] + 1:
                        is_straight = False
                        break
                if is_straight:
                    return "straight", card_list[-1]  # 返回最大牌值
            return None, None
        
        # 顺子（6张及以上）
        if len(card_list) >= 5:
            if 2 not in card_list and len(set(card_list)) == len(card_list):
                is_straight = True
                for i in range(1, len(card_list)):
                    if card_list[i] != card_list[i-1] + 1:
                        is_straight = False
                        break
                if is_straight:
                    return "straight", card_list[-1]  # 返回最大牌值
        
        # 连对（拖拉机，6张及以上，偶数）
        if len(card_list) >= 6 and len(card_list) % 2 == 0:
            # 检查是否每两张都是对子且连续
            is_double_pair = True
            for i in range(0, len(card_list), 2):
                if i + 1 >= len(card_list) or card_list[i] != card_list[i + 1]:
                    is_double_pair = False
                    break
            if is_double_pair:
                unique_values = sorted(set(card_list))
                is_consecutive = True
                for i in range(1, len(unique_values)):
                    if unique_values[i] != unique_values[i-1] + 1:
                        is_consecutive = False
                        break
                if is_consecutive:
                    return "consecutive_pair", unique_values[-1]  # 返回最大对子的值
        
        # 三对（6张，不连续）
        if len(card_list) == 6:
            card_counts = Counter(card_list)
            if len(set(card_list)) == 3 and all(count == 2 for count in card_counts.values()):
                return "three_pairs", max(card_counts.keys())
        
        # 飞机（连续三条，6张及以上，3的倍数）
        if len(card_list) >= 6 and len(card_list) % 3 == 0:
            # 检查是否每个三条都是相同的牌值且连续
            is_triple = True
            for i in range(0, len(card_list), 3):
                if i + 2 >= len(card_list) or not (card_list[i] == card_list[i+1] == card_list[i+2]):
                    is_triple = False
                    break
            if is_triple:
                unique_values = sorted(set(card_list))
                is_consecutive = True
                for i in range(1, len(unique_values)):
                    if unique_values[i] != unique_values[i-1] + 1:
                        is_consecutive = False
                        break
                if is_consecutive:
                    return "airplane", unique_values[-1]  # 返回最大三条的值
        
        return None, None
    
    def check_qualified(self, card_values):
        """检查牌型是否合法
        
        Args:
            card_values: 卡牌值列表
            
        Returns:
            bool: 牌型是否合法
        """
        # 检查空列表
        if len(card_values) == 0:
            return False
        
        # 转换为整数列表并排序
        card_list = sorted(int(card) for card in card_values)
        
        # 检查卡牌值是否在合法范围内
        for value in card_list:
            if not (1 <= value <= 13 or value in (15, 16)):  # 合法值范围：1-13（A-K）, 15（小王）, 16（大王）
                return False
        
        # 单牌
        if len(card_list) == 1:
            return True
        
        # 对子
        if len(card_list) == 2:
            # 普通对子
            if card_list[0] == card_list[1]:
                return True
            # 王炸（小王+大王）
            if set(card_list) == {15, 16}:
                return True
            return False
        
        # 三条
        if len(card_list) == 3:
            if card_list[0] == card_list[1] and card_list[1] == card_list[2]:
                return True
            return False
        
        # 三带一
        if len(card_list) == 4:
            # 四条（四张相同）
            if card_list[0] == card_list[3]:
                return True
            # 三带一
            if (card_list[0] == card_list[2] or card_list[1] == card_list[3]):
                return True
            # 两对（必须连续）
            if card_list[0] == card_list[1] and card_list[2] == card_list[3] and card_list[0] != card_list[2]:
                # 检查两对是否连续
                if card_list[2] == card_list[1] + 1:
                    return True
            return False
        
        # 三带二
        if len(card_list) == 5:
            # 三条+一对
            if (card_list[0] == card_list[2] and card_list[3] == card_list[4]) or \
               (card_list[0] == card_list[1] and card_list[2] == card_list[4]):
                return True
            # 检查是否为顺子
            if 2 not in card_list:
                # 检查是否有重复的牌值
                if len(card_list) == len(set(card_list)):
                    # 检查是否连续
                    is_straight = True
                    for i in range(1, len(card_list)):
                        if card_list[i] != card_list[i-1] + 1:
                            is_straight = False
                            break
                    
                    if is_straight:
                        return True
            return False
        
        # 顺子（五张或更多连续的单牌，2不能在顺子中）
        if len(card_list) > 5:
            # 检查是否有2（15和16是大小王，不在普通牌的连续范围内）
            if 2 not in card_list:
                # 检查是否有重复的牌值
                if len(card_list) == len(set(card_list)):
                    # 检查是否连续
                    is_straight = True
                    for i in range(1, len(card_list)):
                        if card_list[i] != card_list[i-1] + 1:
                            is_straight = False
                            break
                    
                    if is_straight:
                        return True
        
        # 连对（拖拉机）：连续的对子，至少3对（6张牌）
        if len(card_list) >= 6 and len(card_list) % 2 == 0:
            # 检查是否有2或大小王
            if 2 in card_list or 15 in card_list or 16 in card_list:
                return False  # 包含2或大小王，不合法
            else:
                # 检查是否每对都是相同的牌值
                is_double_pair = True
                for i in range(0, len(card_list), 2):
                    if i + 1 >= len(card_list) or card_list[i] != card_list[i + 1]:
                        is_double_pair = False
                        break
                
                if is_double_pair:
                    # 检查牌值是否连续
                    is_consecutive = True
                    unique_values = sorted(set(card_list))
                    for i in range(1, len(unique_values)):
                        if unique_values[i] != unique_values[i - 1] + 1:
                            is_consecutive = False
                            break
                    
                    if is_consecutive:
                        return True
                else:
                    # 不是连对，可能是三对
                    if len(card_list) == 6:
                        # 三对（三对不同的对子）
                        # 检查是否每个值恰好出现两次
                        card_counts = Counter(card_list)
                        if len(set(card_list)) == 3 and all(count == 2 for count in card_counts.values()):
                            return True
        
        # 飞机：连续的三条，至少2个三条（6张牌）
        if len(card_list) >= 6 and len(card_list) % 3 == 0:
            # 检查是否有2或大小王
            if 2 in card_list or 15 in card_list or 16 in card_list:
                return False  # 包含2或大小王，不合法
            else:
                # 检查是否每个三条都是相同的牌值
                is_triple = True
                for i in range(0, len(card_list), 3):
                    if i + 2 >= len(card_list) or not (card_list[i] == card_list[i + 1] == card_list[i + 2]):
                        is_triple = False
                        break
                
                if is_triple:
                    # 检查牌值是否连续
                    is_consecutive = True
                    unique_values = sorted(set(card_list))
                    for i in range(1, len(unique_values)):
                        if unique_values[i] != unique_values[i - 1] + 1:
                            is_consecutive = False
                            break
                    
                    if is_consecutive:
                        return True
        
        return False
    
    def auto_play(self, player_last_move):
        """AI自动出牌
        
        Args:
            player_last_move: 玩家上次出的牌，格式为字符串，如"3 3 4 4"或"不出"
            
        Returns:
            str: AI出的牌，格式为字符串，如"5 5 6 6"或"不出"
        """
        # 对AI的牌进行排序
        sorted_ai_values = sorted([card.value for card in self.cards])
        
        # 如果玩家不出牌，AI出最小的单牌
        if player_last_move == '不出':
            # 出最小的单牌
            return str(sorted_ai_values[0])
        
        # 否则，尝试根据玩家出牌规则出牌
        # 解析玩家出的牌
        player_cards = player_last_move.split(' ')
        # 过滤掉空字符串
        player_cards = [card for card in player_cards if card.strip()]
        # 如果玩家出的牌为空，AI出最小的单牌
        if not player_cards:
            return str(sorted_ai_values[0])
        
        # 获取玩家牌型
        player_pattern, player_main_val = self.get_card_pattern(player_cards)
        if not player_pattern:
            # 玩家牌型无效，AI出最小的单牌
            return str(sorted_ai_values[0])
        
        # 尝试找出AI可以出的牌
        # 遍历所有可能的牌组合，找出符合规则且能压过玩家牌的牌
        valid_combos = []
        
        # 获取玩家出牌的长度，AI出的牌必须长度相同
        player_len = len(player_cards)
        
        # 生成所有可能的卡牌值组合
        from itertools import combinations
        for combo in combinations(sorted_ai_values, player_len):
            # 检查组合是否符合规则
            if self.check_qualified(combo):
                # 检查组合是否与玩家牌型相同
                combo_pattern, combo_main_val = self.get_card_pattern(combo)
                if combo_pattern == player_pattern and combo_main_val > player_main_val:
                    valid_combos.append(combo)
        
        # 如果有符合规则的牌，返回其中最小的一组
        if valid_combos:
            # 找出最小的组合（按主值大小排序）
            valid_combos.sort(key=lambda x: self.get_card_pattern(x)[1])
            return ' '.join(map(str, valid_combos[0]))
        
        # 如果没有符合规则的牌，才返回'不出'
        return '不出'

class CardGame:
    """游戏类，负责游戏状态管理和核心逻辑"""
    
    def __init__(self):
        """初始化游戏"""
        self.deck = Deck()  # 牌堆
        self.player = HumanPlayer("玩家")  # 人类玩家
        self.ai_player = AIPlayer("AI")  # AI玩家
        self.current_turn = "player"  # 当前回合，'player'或'ai'
        self.game_log = []  # 游戏日志
        self.is_game_over = False  # 游戏是否结束
        self.winner = None  # 获胜者
        
    def start_game(self):
        """开始游戏，洗牌并发牌"""
        # 洗牌
        self.deck.shuffle()
        
        # 发牌
        card_number = 13
        player_cards = self.deck.deal(card_number)
        ai_cards = self.deck.deal(card_number)
        
        # 给玩家和AI分配牌
        self.player.add_cards(player_cards)
        self.ai_player.add_cards(ai_cards)
        
        # 随机决定谁先出牌，这里固定玩家先出
        self.current_turn = "player"
        
        # 记录游戏开始
        self.game_log.append(f"游戏开始，玩家和AI各获得{card_number}张牌")
        
    def get_winner(self):
        """获取获胜者
        
        Returns:
            str: 获胜者名称，如果游戏未结束则返回None
        """
        if len(self.player.cards) == 0:
            self.winner = self.player.name
            self.is_game_over = True
        elif len(self.ai_player.cards) == 0:
            self.winner = self.ai_player.name
            self.is_game_over = True
        return self.winner
    
    def player_play(self, card_values, card_ids):
        """玩家出牌
        
        Args:
            card_values: 玩家出的牌的值列表
            card_ids: 玩家出的牌的ID列表
            
        Returns:
            tuple: (bool, str)，是否出牌成功和结果消息
        """
        if self.current_turn != "player" or self.is_game_over:
            return False, "不是玩家回合或游戏已结束"
        
        # 检查出牌是否合法
        if not self.ai_player.check_qualified(card_values):
            return False, "出牌不合法"
        
        # 移除玩家出的牌
        for card_id in card_ids:
            # 找到对应的卡牌并移除
            for card in self.player.cards:
                if card.id == card_id:
                    self.player.remove_card(card)
                    break
        
        # 记录出牌
        player_move = ' '.join(map(str, card_values))
        self.game_log.append(f"玩家出牌：{player_move}")
        
        # 检查玩家是否获胜
        if len(self.player.cards) == 0:
            self.get_winner()
            return True, f"玩家获胜！"
        
        # 切换到AI回合
        self.current_turn = "ai"
        
        return True, f"玩家出了：{player_move}"
    
    def ai_play(self, player_last_move):
        """AI出牌
        
        Args:
            player_last_move: 玩家上次出的牌
            
        Returns:
            tuple: (str, str)，AI出的牌和结果消息
        """
        if self.current_turn != "ai" or self.is_game_over:
            return "", "不是AI回合或游戏已结束"
        
        # AI自动出牌
        ai_move = self.ai_player.auto_play(player_last_move)
        
        # 记录出牌
        self.game_log.append(f"AI出牌：{ai_move}")
        
        # 如果AI出了牌，移除AI出的牌
        if ai_move != '不出':
            ai_move_values = list(map(int, ai_move.split(' ')))
            
            # 移除AI出的牌
            self.ai_player.remove_cards_by_value(ai_move_values)
            
            # 检查AI是否获胜
            if len(self.ai_player.cards) == 0:
                self.get_winner()
                return ai_move, f"AI获胜！"
        
        # 切换到玩家回合
        self.current_turn = "player"
        
        return ai_move, f"AI出了：{ai_move}"
    
    def get_game_status(self):
        """获取游戏状态
        
        Returns:
            dict: 游戏状态信息
        """
        return {
            "current_turn": self.current_turn,
            "player_cards_count": len(self.player.cards),
            "ai_cards_count": len(self.ai_player.cards),
            "is_game_over": self.is_game_over,
            "winner": self.winner,
            "game_log": self.game_log
        }

class GameUI:
    """游戏界面类，负责图形界面显示"""
    
    def __init__(self):
        """初始化游戏界面"""
        self.game = CardGame()  # 游戏逻辑
        
        # 游戏常量
        self.WIDTH, self.HEIGHT = 850, 530
        self.FPS = 60
        
        # 游戏状态
        self.ai_card_pos = []  # AI卡牌位置
        self.player_card_pos = []  # 玩家卡牌位置
        self.number_of_layers_player = []  # 玩家卡牌图层数量
        self.show_player_card = ""  # 玩家当前选择要出的牌
        self.show_index = []  # 玩家当前选择要出的牌的完整卡牌ID
        
        # 加载素材
        self.card_images = []  # 卡牌图像
        self.background = None  # 背景图像
        self.card_box = None  # 卡牌盒子图像
        self.card_back = None  # 卡牌背面图像
        self.produce_card = None  # 出牌按钮图像
        self.not_out_img = None  # 不出牌按钮图像
        
        # 初始化pygame
        pygame.init()
        pygame.mixer.init()
        
        # 加载音效
        pygame.mixer.music.load(os.path.join(current_dir, 'img', '背景音乐.mp3'))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
        
        self.not_out_sound = pygame.mixer.Sound(os.path.join(current_dir, 'img', '要不起.mp3'))
        self.playing_non_compliant_cards_sound = pygame.mixer.Sound(os.path.join(current_dir, 'img', '出牌不合规.mp3'))
        
        # 创建游戏窗口
        self.screen = pygame.display.set_mode((self.WIDTH + 200, self.HEIGHT))
        pygame.display.set_caption("AI扑克牌")
        self.clock = pygame.time.Clock()
        
        # 加载图像素材
        self.load_images()
        
        # 开始游戏
        self.game.start_game()
        self.ai_card_pos = self.calculate_card_positions(self.game.ai_player.cards, is_ai=True)
        self.player_card_pos = self.calculate_card_positions(self.game.player.cards)
        self.number_of_layers_player = [1 for _ in range(len(self.game.player.cards))]
    
    def load_images(self):
        """加载游戏图像素材"""
        # 加载卡牌图像
        for i in range(1, 54):
            img_path = os.path.join(current_dir, 'img', f'{i}.png')
            img = pygame.image.load(img_path)
            img = pygame.transform.scale(img, (img.get_width() // 3, img.get_height() // 3))
            self.card_images.append(img)
        
        # 加载背景图像
        bg_path = os.path.join(current_dir, 'img', 'background.png')
        self.background = pygame.transform.scale(pygame.image.load(bg_path), (self.WIDTH, self.HEIGHT))
        
        # 加载卡牌盒子图像
        box_path = os.path.join(current_dir, 'img', 'card_box.png')
        self.card_box = pygame.transform.scale(pygame.image.load(box_path), (150, 200))
        
        # 加载卡牌背面图像
        back_path = os.path.join(current_dir, 'img', '卡背.png')
        img = pygame.image.load(back_path)
        self.card_back = pygame.transform.scale(img, (img.get_width() // 3, img.get_height() // 3))
        
        # 加载出牌按钮图像
        produce_path = os.path.join(current_dir, 'img', '出牌.png')
        img = pygame.image.load(produce_path)
        self.produce_card = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
        
        # 加载不出牌按钮图像
        not_out_path = os.path.join(current_dir, 'img', '不出.png')
        img = pygame.image.load(not_out_path)
        self.not_out_img = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
    
    def calculate_card_positions(self, cards, is_ai=False):
        """计算卡牌位置
        
        Args:
            cards: 卡牌列表
            is_ai: 是否是AI卡牌
            
        Returns:
            list: 卡牌位置列表
        """
        positions = []
        x_pos = 10
        y_pos = 25 if is_ai else 407
        
        # 获取卡牌值列表
        card_values = [card.value for card in cards]
        
        for i in range(len(card_values)):
            positions.append((x_pos, y_pos))
            
            # 如果不是最后一张牌，计算下一张牌的位置
            if i < len(card_values) - 1:
                if card_values[i] == card_values[i + 1]:
                    x_pos += 20
                else:
                    x_pos += 80
        
        return positions
    
    def draw_game(self):
        """绘制游戏界面"""
        # 清空屏幕
        self.screen.fill((255, 255, 255))
        
        # 绘制背景
        self.screen.blit(self.background, (0, 0))
        
        # 绘制卡牌盒子
        self.screen.blit(self.card_box, (16, 180))
        
        # 绘制AI卡牌（背面）
        for pos in self.ai_card_pos:
            self.screen.blit(self.card_back, pos)
        
        # 绘制玩家卡牌
        for i, card in enumerate(self.game.player.cards):
            if i < len(self.player_card_pos):
                pos = self.player_card_pos[i]
                self.screen.blit(self.card_images[card.id - 1], pos)
        
        # 绘制游戏日志
        y_offset = 20
        for log in self.game.game_log[-10:]:  # 只显示最近10条日志
            pygame.draw.rect(self.screen, (255, 255, 255), (self.WIDTH + 20, y_offset, 160, 25))
            font = pygame.font.Font(None, 20)
            text = font.render(log, True, (0, 0, 0))
            self.screen.blit(text, (self.WIDTH + 25, y_offset))
            y_offset += 25
    
    def handle_events(self):
        """处理游戏事件"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
        
        # 处理玩家卡牌点击
        if self.game.current_turn == "player" and not self.game.is_game_over:
            for i, card in enumerate(self.game.player.cards):
                if i < len(self.player_card_pos):
                    card_rect = self.card_images[card.id - 1].get_rect(topleft=self.player_card_pos[i])
                    if card_rect.collidepoint(mouse_pos):
                        # 只有当前牌是该值的最后一张时才能点击
                        can_click = (i == len(self.game.player.cards) - 1 or 
                                   self.game.player.cards[i].value != self.game.player.cards[i + 1].value)
                        # 提升可点击的牌
                        self.player_card_pos[i] = (self.player_card_pos[i][0], 387 if can_click else 407)
                        
                        if mouse_down and can_click:
                            # 点击后，将牌值添加到玩家出的牌中
                            if len(self.show_index) <= 6:
                                # 添加到出牌列表
                                self.show_player_card += str(card.value) + ','
                                self.show_index.append(card.id)
        
        return True
    
    def run(self):
        """运行游戏主循环"""
        running = True
        while running:
            # 处理事件
            running = self.handle_events()
            
            # 绘制游戏
            self.draw_game()
            
            # 更新屏幕
            pygame.display.flip()
            
            # 控制帧率
            self.clock.tick(self.FPS)
        
        # 退出游戏
        pygame.quit()

if __name__ == "__main__":
    # 创建游戏UI并运行
    game_ui = GameUI()
    game_ui.run()
