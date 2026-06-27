"""
游戏状态管理模块
将原本分散在50+个全局变量中的游戏状态按职责组织成清晰的状态管理类。
"""

import json
import os


class PlayerState:
    """管理玩家持久化数据：金币、道具、等级等"""

    def __init__(self):
        self.coin_count = 1000
        self.owned_backgrounds = ['default']
        self.current_background = 'default'
        self.owned_items = []
        self.attack_speed_level = 0
        self.damage_level = 0
        self.easy_question_level = 0
        self.extra_time_level = 0
        self.inventory = {
            'easy_question': 0,
            'extra_time': 0,
            'shield': 0,
            'double_coin': 0,
            'hint_answer': 0,
            'attack_speed_1': 0,
            'attack_speed_2': 0,
            'attack_speed_3': 0,
            'damage_1': 0,
            'damage_2': 0,
            'damage_3': 0,
        }

    # ---- 金币操作 ----
    def add_coins(self, amount: int) -> int:
        self.coin_count += amount
        return self.coin_count

    def spend_coins(self, amount: int) -> bool:
        if self.coin_count >= amount:
            self.coin_count -= amount
            return True
        return False

    # ---- 背景操作 ----
    def owns_background(self, bg_name: str) -> bool:
        return bg_name in self.owned_backgrounds

    def add_background(self, bg_name: str):
        if bg_name not in self.owned_backgrounds:
            self.owned_backgrounds.append(bg_name)

    def set_current_background(self, bg_name: str):
        if bg_name in self.owned_backgrounds:
            self.current_background = bg_name

    # ---- 道具操作 ----
    def add_item(self, item_name: str):
        if item_name not in self.owned_items:
            self.owned_items.append(item_name)

    def has_item(self, item_name: str) -> bool:
        return item_name in self.owned_items

    def get_inventory_count(self, item_key: str) -> int:
        return self.inventory.get(item_key, 0)

    def use_inventory_item(self, item_key: str) -> bool:
        if self.inventory.get(item_key, 0) > 0:
            self.inventory[item_key] -= 1
            return True
        return False

    def add_inventory_item(self, item_key: str, count: int = 1):
        if item_key in self.inventory:
            self.inventory[item_key] += count

    # ---- 属性升级 ----
    def upgrade_attack_speed(self) -> bool:
        if self.attack_speed_level < 5:
            self.attack_speed_level += 1
            return True
        return False

    def upgrade_damage(self) -> bool:
        if self.damage_level < 5:
            self.damage_level += 1
            return True
        return False

    # ---- 序列化 ----
    def to_dict(self) -> dict:
        return {
            'coin_count': self.coin_count,
            'owned_backgrounds': self.owned_backgrounds,
            'current_background': self.current_background,
            'owned_items': self.owned_items,
            'attack_speed_level': self.attack_speed_level,
            'damage_level': self.damage_level,
            'easy_question_level': self.easy_question_level,
            'extra_time_level': self.extra_time_level,
            'inventory': self.inventory,
        }

    def from_dict(self, data: dict):
        self.coin_count = data.get('coin_count', 1000)
        self.owned_backgrounds = data.get('owned_backgrounds', ['default'])
        self.current_background = data.get('current_background', 'default')
        self.owned_items = data.get('owned_items', [])
        self.attack_speed_level = data.get('attack_speed_level', 0)
        self.damage_level = data.get('damage_level', 0)
        self.easy_question_level = data.get('easy_question_level', 0)
        self.extra_time_level = data.get('extra_time_level', 0)
        saved_inventory = data.get('inventory', {})
        for key in self.inventory:
            if key in saved_inventory:
                self.inventory[key] = saved_inventory[key]


class GameSessionState:
    """管理单次游戏会话的临时状态"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置会话状态"""
        self.score = 0
        self.health = 1
        self.questions = []
        self.answers = []
        self.current_question_index = 0
        self.question_move = [False, False, False, False, False]
        self.now_y = [400, 400, 400, 400, 400]
        self.new_y = [20, 70, 120, 170, 230]
        self.show_number = ''
        self.is_error = False
        self.is_reward = False
        self.bullet_number = 0
        self.record_reward = 0

        # 石头相关
        self.rocks_pos = []
        self.rocks_image = []
        self.rocks_speed = []
        self.rock_health = []
        self.rock_tongue = []
        self.rock_speed_reduced = []
        self.rock_speed_increased = []
        self.new_rock_speed = []
        self.rock_number = 5

        # 子弹相关
        self.bullet_x = []
        self.bullet_y = []

        # 护盾位置
        self.shield_pos = []

        # 动画状态
        self.angle = 0
        self.aim = False
        self.explode = False
        self.progress = 0
        self.explode_d_pos = [0, 0]
        self.is_white = False
        self.white_play = 0
        self.show_hp = False
        self.hp_content = 0
        self.hp_x = 50

        # 准星
        self.red_crosshair_pos = [0, 0]
        self.b_x = 0
        self.b_y = 0
        self.b_speed = 10
        self.b_angle = 0

        # 玩家
        self.player_x = 245

        # 武器冷却
        self.shoot_cooldown = 0
        self.has_shield = False

        # 技能状态
        self.easy_question_active = False
        self.easy_question_used = False
        self.hint_remain = 0
        self.show_hint = False

        # 背包UI
        self.show_inventory = False
        self.inventory_message = ""
        self.inventory_message_time = 0

        # 抖动
        self.shake_offset = 0
        self.shake_time = 0
        self.shake_duration = 20

        # 步数和关卡
        self.step_count = 0
        self.max_rock = 0
        self.count_question = 0

    def add_score(self, points: int):
        self.score += points

    def take_damage(self, amount: int = 1) -> bool:
        """返回是否死亡"""
        self.health -= amount
        return self.health <= 0

    def add_question(self, question: str, answer: int):
        self.questions.append(question)
        self.answers.append(answer)

    def pop_question(self):
        if self.questions:
            self.questions.pop(0)
        if self.answers:
            self.answers.pop(0)
        if self.now_y:
            self.now_y.pop(0)
        if self.question_move:
            self.question_move.pop(0)

    def append_question_slot(self):
        self.now_y.append(400)
        self.question_move.append(False)


class ConfigState:
    """管理游戏配置和设置"""

    def __init__(self):
        self.developer_mode = True
        self.settings = {
            'music_volume': 0.3,
            'sfx_volume': 0.5,
            'screen_width': 500,
            'screen_height': 600,
        }

    def to_dict(self) -> dict:
        return {
            'developer_mode': self.developer_mode,
            'settings': self.settings,
        }

    def from_dict(self, data: dict):
        self.developer_mode = data.get('developer_mode', True)
        self.settings.update(data.get('settings', {}))


class GameState:
    """统一的游戏状态管理器，聚合所有子状态"""

    def __init__(self):
        self.player = PlayerState()
        self.session = GameSessionState()
        self.config = ConfigState()

        # 游戏流程控制
        self.running = True
        self.stop = False
        self.game_type = 'main_page'
        self.content = 0  # 0=主菜单, 1=关卡选择, 2=关卡网格, 3=游戏/商店
        self.oral_click = 0

        # 关卡进度
        self.level_progress = []
        self._init_level_progress()

    def _init_level_progress(self):
        # 先尝试从 user_data.json 加载（包含 level_progress 字段）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(script_dir, 'user_data.json')
        try:
            if os.path.exists(save_path):
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 如果文件是旧格式（纯列表就是关卡进度）
                if isinstance(data, list) and len(data) == 20:
                    self.level_progress = data
                    return
                # 新格式：从 dict 中提取
                if isinstance(data, dict) and 'level_progress' in data:
                    self.level_progress = data['level_progress']
                    return
        except Exception:
            pass

        self.level_progress = [True] * 20
        self.level_progress[0] = False

    # ---- 持久化 ----
    def save(self, save_file: str):
        data = {
            'player_state': self.player.to_dict(),
            'config_state': self.config.to_dict(),
            'level_progress': self.level_progress,
        }
        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def load(self, save_file: str):
        try:
            if os.path.exists(save_file):
                with open(save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.player.from_dict(data.get('player_state', {}))
                self.config.from_dict(data.get('config_state', {}))
                self.level_progress = data.get('level_progress', self.level_progress)
                return True
        except Exception as e:
            print(f"加载失败: {e}")
        return False

    def save_user_data(self):
        """保存用户数据（兼容原接口）"""
        user_data = self.player.to_dict()
        self.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.json'))

    def load_user_data(self):
        """加载用户数据（兼容原接口）"""
        return self.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.json'))


# ============================================================
# 商店物品配置（常量数据，不属于游戏状态但全局使用）
# ============================================================

shop_categories = {
    'backgrounds': {
        'name': '🎨 背景',
        'items': {
            'sunset': {'name': '日落', 'price': 100, 'desc': '温暖的日落景色'},
            'night': {'name': '夜晚', 'price': 150, 'desc': '神秘的夜空'},
            'forest': {'name': '森林', 'price': 200, 'desc': '清新的森林'},
            'ocean': {'name': '海洋', 'price': 250, 'desc': '蓝色的大海'},
            'space': {'name': '太空', 'price': 300, 'desc': '浩瀚的宇宙'},
            'volcano': {'name': '火山', 'price': 350, 'desc': '燃烧的火山'},
            'snow': {'name': '雪地', 'price': 400, 'desc': '白雪皑皑'},
            'rainbow': {'name': '彩虹', 'price': 500, 'desc': '美丽的彩虹'},
        }
    },
    'weapons': {
        'name': '⚔️ 武器升级',
        'items': {
            'attack_speed_1': {'name': '攻速 I', 'price': 80, 'desc': '提升10%攻速', 'max_level': 1},
            'attack_speed_2': {'name': '攻速 II', 'price': 160, 'desc': '再提升10%攻速', 'max_level': 2},
            'attack_speed_3': {'name': '攻速 III', 'price': 240, 'desc': '再提升10%攻速', 'max_level': 3},
            'damage_1': {'name': '伤害 I', 'price': 100, 'desc': '提升1点伤害', 'max_level': 1},
            'damage_2': {'name': '伤害 II', 'price': 200, 'desc': '再提升1点伤害', 'max_level': 2},
            'damage_3': {'name': '伤害 III', 'price': 300, 'desc': '再提升1点伤害', 'max_level': 3},
        }
    },
    'skills': {
        'name': '✨ 技能',
        'items': {
            'easy_question': {'name': '简化题目', 'price': 200, 'desc': '10以内加减法(限一次)', 'max_level': 1},
            'extra_time': {'name': '额外时间', 'price': 120, 'desc': '增加5秒思考时间', 'max_level': 1},
            'shield': {'name': '护盾', 'price': 150, 'desc': '获得一个护盾', 'max_level': 1},
            'double_coin': {'name': '双倍金币', 'price': 180, 'desc': '答题金币翻倍', 'max_level': 1},
            'hint_answer': {'name': '提示答案', 'price': 50, 'desc': '显示答案最高位(限1次)', 'max_level': 3},
        }
    }
}