import pygame
from openai import OpenAI
import os
import json
import threading
import queue
import time
import requests

pygame.init()

class ChessMoveValidator:
    @staticmethod
    def is_valid_move(board, from_row, from_col, to_row, to_col, piece):
        if piece is None:
            return False, "起始位置没有棋子"
        
        name, color, img_idx = piece
        
        if color != 'black':
            return False, "只能移动黑方棋子"
        
        valid_moves = Game().get_valid_moves(from_row, from_col)
        
        if (to_row, to_col) not in valid_moves:
            return False, f"{name}从({from_row},{from_col})到({to_row},{to_col})不是合法走法"
        
        return True, "合法走法"

    @staticmethod
    def validate_and_apply_move(game, from_row, from_col, to_row, to_col):
        piece = game.board[from_row][from_col]
        
        is_valid, message = ChessMoveValidator.is_valid_move(game.board, from_row, from_col, to_row, to_col, piece)
        
        if not is_valid:
            return False
        
        captured = game.board[to_row][to_col]
        game.board[from_row][from_col] = None
        game.board[to_row][to_col] = piece
        
        return True

class AIAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('NVIDIA_API_KEY')
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置NVIDIA_API_KEY环境变量")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
            timeout=60.0
        )
        
        self.max_retries = 3
        self.retry_delay = 2
    
    def chat(self, prompt, model="stepfun-ai/step-3.5-flash", temperature=1, top_p=0.9, max_tokens=16384, thinking_budget=0):
        extra_body = {}
        extra_body["thinking_budget"] = 0
        if thinking_budget:
            extra_body["thinking_budget"] = thinking_budget
        
        for attempt in range(self.max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=False,
                    extra_body=extra_body if extra_body else None,
                    timeout=60.0
                )
                return completion.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API连接失败，{self.retry_delay}秒后重试... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    raise e

    def chat_with_thinking(self, prompt, thinking_budget=2048):
        return self.chat(prompt, model="bytedance/seed-oss-36b-instruct", temperature=1.1, top_p=0.95, max_tokens=4096, thinking_budget=thinking_budget)

    def deepseek_chat(self, prompt):
        return self.chat(prompt, model="deepseek/deepseek-3.2")

    def qwen_chat(self, prompt):
        return self.chat(prompt, model="qwen/qwen3-coder-480b-a35b-instruct")

    def chat_fast(self, prompt):
        return self.chat(prompt, model="stepfun-ai/step-3.5-flash", temperature=1, top_p=0.9, max_tokens=16384)

    def chat_stream(self, prompt, model="qwen/qwen3-coder-480b-a35b-instruct", temperature=1, top_p=0.9, max_tokens=16384):
        for attempt in range(self.max_retries):
            try:
                print(f"尝试连接AI服务器... ({attempt + 1}/{self.max_retries})")
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=120.0
                )
                
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                print(f"流式连接错误: {e}")
                if attempt < self.max_retries - 1:
                    print(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("达到最大重试次数，放弃连接")
                    raise e

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((1200, 680))
        self.BROWN = (165, 105, 0)
        pygame.display.set_caption("中国棋")
        
        self.checkerboard = pygame.image.load(os.path.join('img', '棋盘.png'))
        self.checkerboard = pygame.transform.scale(self.checkerboard,(self.checkerboard.get_width()*1.02-25, self.checkerboard.get_height()*1.02+20))
        self.image_names = ['红_仕.png', '红_兵.png', '红_帥.png', '红_炮.png', '红_相.png', '红_車.png', '红_馬.png', '黑_卒.png', '黑_士.png', '黑_将.png', '黑_炮.png', '黑_象.png', '黑_車.png', '黑_馬.png']
        self.images = [pygame.transform.scale(pygame.image.load(os.path.join('img', name)), (50, 50)) for name in self.image_names]
        
        self.font_32 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 32)
        self.font_24 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 24)
        self.font_20 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 20)
        self.font_50 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 50)
        
        self.board = [[None for _ in range(9)] for _ in range(10)]
        
        self.cell_width = 55
        self.cell_height = 60
        self.board_offset_x = 30
        self.board_offset_y = 30
        
        self.init_pieces()
        
        self.current_player = 'red'
        self.selected_piece = None
        self.valid_moves = []
        
        self.animating = False
        self.animation_piece = None
        self.animation_start = (0, 0)
        self.animation_end = (0, 0)
        self.animation_target = (None, None)
        self.animation_progress = 0.0
        
        self.check_flag = False
        self.checkmate_flag = False
        self.game_over = False
        
        self.ai_thinking = False
        self.ai_thinking_text = ""
        self.ai_thinking_lines = []
        self.panel_width = 340
        self.panel_x = 850
    
    def merge_boards(self, current_board, ai_board):
        new_board = [[None for _ in range(9)] for _ in range(10)]
        
        for row in range(10):
            for col in range(9):
                current_piece = current_board[row][col]
                ai_piece = None
                
                if row < len(ai_board) and col < len(ai_board[row]):
                    elem = ai_board[row][col]
                    if elem is not None and isinstance(elem, list) and len(elem) == 3:
                        ai_piece = (elem[0], elem[1], elem[2])
                
                if ai_piece is not None and ai_piece[1] == 'black':
                    new_board[row][col] = ai_piece
                elif current_piece is not None:
                    new_board[row][col] = current_piece
        
        return new_board
    
    def init_pieces(self):
        # 红方底线
        self.board[9][0] = ('車', 'red', 5)
        self.board[9][1] = ('馬', 'red', 6)
        self.board[9][2] = ('相', 'red', 4)
        self.board[9][3] = ('仕', 'red', 0)
        self.board[9][4] = ('帥', 'red', 2)
        self.board[9][5] = ('仕', 'red', 0)
        self.board[9][6] = ('相', 'red', 4)
        self.board[9][7] = ('馬', 'red', 6)
        self.board[9][8] = ('車', 'red', 5)
        
        # 红炮
        self.board[7][1] = ('炮', 'red', 3)
        self.board[7][7] = ('炮', 'red', 3)
        
        # 红兵
        for i in range(5):
            self.board[6][i * 2] = ('兵', 'red', 1)
        
        # 黑方底线
        self.board[0][0] = ('車', 'black', 12)
        self.board[0][1] = ('馬', 'black', 13)
        self.board[0][2] = ('象', 'black', 11)
        self.board[0][3] = ('士', 'black', 8)
        self.board[0][4] = ('将', 'black', 9)
        self.board[0][5] = ('士', 'black', 8)
        self.board[0][6] = ('象', 'black', 11)
        self.board[0][7] = ('馬', 'black', 13)
        self.board[0][8] = ('車', 'black', 12)
        
        # 黑炮
        self.board[2][1] = ('炮', 'black', 10)
        self.board[2][7] = ('炮', 'black', 10)
        
        # 黑卒
        for i in range(5):
            self.board[3][i * 2] = ('卒', 'black', 7)
    
    def get_cell_center(self, row, col):
        x = self.board_offset_x + col * self.cell_width + self.cell_width // 2
        y = self.board_offset_y + row * self.cell_height + self.cell_height // 2
        return x, y
    
    def get_piece_position(self, row, col):
        x, y = self.get_cell_center(row, col)
        return x - 25, y - 25
    
    def get_valid_moves(self, row, col):
        piece = self.board[row][col]
        if not piece:
            return []
        
        name, color, img_idx = piece
        
        if name == '車':
            return self._get_chariot_moves(row, col, color)
        elif name == '馬':
            return self._get_horse_moves(row, col, color)
        elif name == '相' or name == '象':
            return self._get_elephant_moves(row, col, name, color)
        elif name == '仕' or name == '士':
            return self._get_advisor_moves(row, col, name, color)
        elif name == '帥' or name == '将':
            return self._get_general_moves(row, col, name, color)
        elif name == '炮':
            return self._get_cannon_moves(row, col, color)
        elif name == '兵' or name == '卒':
            return self._get_soldier_moves(row, col, name, color)
        else:
            return []
    
    def _get_chariot_moves(self, row, col, color):
        moves = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            r, c = row + dr, col + dc
            while 0 <= r < 10 and 0 <= c < 9:
                if self.board[r][c] is None:
                    moves.append((r, c))
                else:
                    if self.board[r][c][1] != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves
    
    def _get_horse_moves(self, row, col, color):
        moves = []
        horse_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dr, dc in horse_moves:
            r, c = row + dr, col + dc
            if 0 <= r < 10 and 0 <= c < 9:
                hr, hc = row + dr // 2, col + dc // 2
                if self.board[hr][hc] is None and (self.board[r][c] is None or self.board[r][c][1] != color):
                    moves.append((r, c))
        return moves
    
    def _get_elephant_moves(self, row, col, name, color):
        moves = []
        for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
            r, c = row + dr, col + dc
            if 0 <= r < 10 and 0 <= c < 9:
                if name == '相':
                    if r < 5:
                        continue
                else:
                    if r > 4:
                        continue
                hr, hc = row + dr // 2, col + dc // 2
                if self.board[hr][hc] is None:
                    if self.board[r][c] is None or self.board[r][c][1] != color:
                        moves.append((r, c))
        return moves
    
    def _get_advisor_moves(self, row, col, name, color):
        moves = []
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            r, c = row + dr, col + dc
            if 0 <= r < 10 and 0 <= c < 9:
                if name == '仕':
                    if r < 7 or c < 3 or c > 5:
                        continue
                else:
                    if r > 2 or c < 3 or c > 5:
                        continue
                if self.board[r][c] is None or self.board[r][c][1] != color:
                    moves.append((r, c))
        return moves
    
    def _get_general_moves(self, row, col, name, color):
        moves = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            r, c = row + dr, col + dc
            if name == '帥':
                if r < 7 or c < 3 or c > 5:
                    continue
            else:
                if r > 2 or c < 3 or c > 5:
                    continue
            if 0 <= r < 10 and 0 <= c < 9:
                if self.board[r][c] is None or self.board[r][c][1] != color:
                    moves.append((r, c))
        return moves
    
    def _get_cannon_moves(self, row, col, color):
        moves = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            r, c = row + dr, col + dc
            found_piece = False
            while 0 <= r < 10 and 0 <= c < 9:
                if self.board[r][c] is None:
                    if not found_piece:
                        moves.append((r, c))
                else:
                    if found_piece:
                        if self.board[r][c][1] != color:
                            moves.append((r, c))
                        break
                    else:
                        found_piece = True
                r += dr
                c += dc
        return moves
    
    def _get_soldier_moves(self, row, col, name, color):
        moves = []
        direction = -1 if color == 'red' else 1
        r, c = row + direction, col
        if 0 <= r < 10 and 0 <= c < 9:
            if self.board[r][c] is None or self.board[r][c][1] != color:
                moves.append((r, c))
        if (color == 'red' and row <= 4) or (color == 'black' and row >= 5):
            for dc in [-1, 1]:
                r, c = row, col + dc
                if 0 <= r < 10 and 0 <= c < 9:
                    if self.board[r][c] is None or self.board[r][c][1] != color:
                        moves.append((r, c))
        return moves
    
    def wrap_text(self, text, font, max_width):
        words = list(text)
        lines = []
        current_line = ""
        
        for char in words:
            test_line = current_line + char
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def draw_ai_panel(self):
        panel_rect = pygame.Rect(self.panel_x, 10, self.panel_width - 20, 660)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 80), panel_rect, 3, border_radius=10)
        
        title = self.font_24.render("AI 思考中...", True, (255, 255, 255))
        self.screen.blit(title, (self.panel_x + 15, 20))
        
        y_offset = 55
        max_text_width = self.panel_width - 50
        
        for line in self.ai_thinking_lines[-28:]:
            text_surface = self.font_20.render(line, True, (220, 220, 220))
            self.screen.blit(text_surface, (self.panel_x + 15, y_offset))
            y_offset += 25
    
    def draw_chessman(self):
        selected_row, selected_col = self.selected_piece if self.selected_piece else (None, None)
        
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece:
                    name, color, img_idx = piece
                    x, y = self.get_piece_position(row, col)
                    if row == selected_row and col == selected_col:
                        y -= 10
                    self.screen.blit(self.images[img_idx], (x, y))
        
        if self.animating and self.animation_piece:
            start_x, start_y = self.animation_start
            end_x, end_y = self.animation_end
            x = start_x + (end_x - start_x) * self.animation_progress
            y = start_y + (end_y - start_y) * self.animation_progress
            self.screen.blit(self.images[self.animation_piece[2]], (x, y))
    
    def draw_valid_moves(self):
        for r, c in self.valid_moves:
            x, y = self.get_cell_center(r, c)
            if self.board[r][c] is not None:
                pygame.draw.circle(self.screen, (255, 0, 0), (x, y), 18, 3)
            else:
                pygame.draw.circle(self.screen, (0, 255, 0), (x, y), 15, 3)
    
    def get_clicked_piece(self, mouse_pos):
        x, y = mouse_pos
        col = (x - self.board_offset_x) // self.cell_width
        row = (y - self.board_offset_y) // self.cell_height
        if 0 <= row < 10 and 0 <= col < 9:
            return row, col
        return None, None
    
    def animate_move(self, piece, start_row, start_col, end_row, end_col):
        self.animating = True
        self.animation_piece = piece
        self.animation_start = self.get_piece_position(start_row, start_col)
        self.animation_end = self.get_piece_position(end_row, end_col)
        self.animation_target = (end_row, end_col)
        self.animation_progress = 0.0
    
        
       
    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = ''
        
        for word in words:
            test_line = current_line + word + ' '
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                if font.size(word)[0] > max_width:
                    chars = list(word)
                    current_part = ''
                    for char in chars:
                        test_part = current_part + char
                        if font.size(test_part)[0] <= max_width:
                            current_part = test_part
                        else:
                            lines.append(current_part)
                            current_part = char
                    if current_part:
                        lines.append(current_part)
                    current_line = ''
                else:
                    current_line = word + ' '
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines

    def draw_ai_panel(self):
        panel_rect = pygame.Rect(self.panel_x, 10, self.panel_width - 20, 660)
        pygame.draw.rect(self.screen, (30, 30, 35), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), panel_rect, 2, border_radius=10)
        
        if self.ai_thinking:
            title = self.font_24.render("🧠 AI 深度思考中...", True, (100, 200, 255))
        else:
            title = self.font_24.render("AI 助手", True, (150, 150, 150))
        self.screen.blit(title, (self.panel_x + 20, 25))
        
        separator_y = 60
        pygame.draw.line(self.screen, (80, 80, 100), 
                        (self.panel_x + 10, separator_y), 
                        (self.panel_x + self.panel_width - 30, separator_y), 2)
        
        content_y = 75
        max_content_width = self.panel_width - 50
        
        if self.ai_thinking:
            if self.ai_thinking_text:
                text_no_newlines = self.ai_thinking_text.replace('\n', ' ').replace('\r', '')
                all_lines = self.wrap_text(text_no_newlines, self.font_20, max_content_width)
                
                max_lines = 26
                if len(all_lines) > max_lines:
                    all_lines = all_lines[-max_lines:]
                
                for i, line in enumerate(all_lines):
                    y_pos = content_y + i * 22
                    if y_pos < 640:
                        line_stripped = line.strip()
                        
                        if line_stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.')) or line_stripped.startswith('【'):
                            color = (255, 200, 100)
                        elif line_stripped.startswith(('-', '•', '★', '●', '○')):
                            color = (150, 255, 150)
                        elif any(keyword in line_stripped for keyword in ['吃掉', '将军', '威胁', '危险', '最优', '选择', '理由']):
                            color = (255, 150, 150)
                        else:
                            color = (200, 200, 220)
                        
                        text_surface = self.font_20.render(line, True, color)
                        self.screen.blit(text_surface, (self.panel_x + 15, y_pos))
            else:
                loading_text = self.font_20.render("正在分析棋局...", True, (100, 200, 255))
                self.screen.blit(loading_text, (self.panel_x + 15, content_y))
                
                loading_time = pygame.time.get_ticks() // 200
                animation_frame = loading_time % 4
                
                think_indicators = ['思考中  ', '思考中. ', '思考中..', '思考中...']
                indicator_surface = self.font_20.render(think_indicators[animation_frame], True, (100, 200, 255))
                self.screen.blit(indicator_surface, (self.panel_x + 15, content_y + 30))
                
                brain_x = self.panel_x + 200
                brain_y = content_y + 15
                if animation_frame == 0:
                    pygame.draw.circle(self.screen, (100, 200, 255), (brain_x, brain_y), 8)
                elif animation_frame == 1:
                    pygame.draw.circle(self.screen, (100, 200, 255), (brain_x, brain_y), 10)
                elif animation_frame == 2:
                    pygame.draw.circle(self.screen, (100, 200, 255), (brain_x, brain_y), 12)
                else:
                    pygame.draw.circle(self.screen, (100, 200, 255), (brain_x, brain_y), 10)
        else:
            status_text = self.font_20.render("等待玩家走棋...", True, (100, 100, 120))
            self.screen.blit(status_text, (self.panel_x + 15, content_y))
            
            tips = [
                "💡 提示：点击棋子选中",
                "💡 提示：绿色圆点可移动",
                "💡 提示：红色圆圈可吃子"
            ]
            tip_index = (pygame.time.get_ticks() // 3000) % 3
            tip_surface = self.font_20.render(tips[tip_index], True, (80, 150, 80))
            self.screen.blit(tip_surface, (self.panel_x + 15, content_y + 40))

    def gui(self):
        self.screen.fill(self.BROWN)
        self.screen.blit(self.checkerboard, (self.board_offset_x+20, self.board_offset_y+27))
        self.draw_chessman()
        self.draw_valid_moves()
        
        text_color = (255, 255, 255)
        if self.game_over:
            text = self.font_50.render("绝杀", True, (255, 0, 0))
            text_rect = text.get_rect(center=(200, 340))
            self.screen.blit(text, text_rect)
        elif self.check_flag:
            text = self.font_50.render("将军", True, (255, 0, 0))
            text_rect = text.get_rect(center=(200, 340))
            self.screen.blit(text, text_rect)
        
        player_text = self.font_24.render(f"当前玩家：{'红方' if self.current_player == 'red' else '黑方'}", True, text_color)
        self.screen.blit(player_text, (10, 10))
        
        self.draw_ai_panel()

    def ai_think_thread(self, prompt, result_queue):
        try:
            assistant = AIAssistant()
            full_response = ""
            
            for chunk in assistant.chat_stream(prompt):
                if chunk:
                    full_response += chunk
                    result_queue.put(('chunk', chunk))
            
            result_queue.put(('done', full_response))
        except Exception as e:
            result_queue.put(('error', str(e)))

    def process_ai_response(self, full_response):
        try:
            json_str = full_response
            json_str = json_str.strip()
            
            if '```json' in json_str:
                json_str = json_str.split('```json', 1)[1]
            elif '```' in json_str:
                json_str = json_str.split('```', 1)[1]
            
            if '```' in json_str:
                json_str = json_str.rsplit('```', 1)[0]
            
            json_str = json_str.strip().replace('\n', '').replace('\r', '')
            
            data = json.loads(json_str)
            if isinstance(data, str):
                data = json.loads(data)
            
            with open(os.path.join(os.path.dirname(__file__), "answer.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            if 'move' in data and data['move'] is not None:
                move = data['move']
                
                if not isinstance(move, dict):
                    print("❌ AI走棋失败：move格式错误")
                    if 'analysis' in data:
                        print("\n" + "="*50)
                        print("AI分析：")
                        print(data['analysis'])
                        print("="*50 + "\n")
                else:
                    from_row = move.get('from_row')
                    from_col = move.get('from_col')
                    to_row = move.get('to_row')
                    to_col = move.get('to_col')
                    
                    if (from_row is not None and from_col is not None and to_row is not None and to_col is not None and
                        isinstance(from_row, int) and isinstance(from_col, int) and isinstance(to_row, int) and isinstance(to_col, int) and
                        0 <= from_row < 10 and 0 <= from_col < 9 and 0 <= to_row < 10 and 0 <= to_col < 9):
                        piece = self.board[from_row][from_col]
                        if piece and piece[1] == 'black':
                            if ChessMoveValidator.validate_and_apply_move(self, from_row, from_col, to_row, to_col):
                                print("✅ AI走棋成功")
                                print("\n" + "="*80)
                                print("AI完整原始回答：")
                                print("="*80)
                                print(full_response)
                                print("="*80 + "\n")
                                return True
                            else:
                                print("❌ AI走棋失败：走法不合法")
                                print("\n" + "="*80)
                                print("AI完整原始回答：")
                                print("="*80)
                                print(full_response)
                                print("="*80 + "\n")
                        else:
                            print("❌ AI走棋失败：起始位置没有黑方棋子")
                            print("\n" + "="*80)
                            print("AI完整原始回答：")
                            print("="*80)
                            print(full_response)
                            print("="*80 + "\n")
                    else:
                        print("❌ AI走棋失败：坐标无效")
                        print("\n" + "="*80)
                        print("AI完整原始回答：")
                        print("="*80)
                        print(full_response)
                        print("="*80 + "\n")
            
            if 'board' in data and data['board'] is not None:
                new_board_data = data['board']
                
                if not isinstance(new_board_data, list) or len(new_board_data) != 10:
                    print("❌ AI走棋失败：board格式错误")
                    print("\n" + "="*80)
                    print("AI完整原始回答：")
                    print("="*80)
                    print(full_response)
                    print("="*80 + "\n")
                    return False
                
                def convert_board_element(elem):
                    if elem is None:
                        return None
                    if isinstance(elem, list) and len(elem) == 3:
                        return (elem[0], elem[1], elem[2])
                    return elem
                
                red_count = 0
                black_count = 0
                
                for row in new_board_data:
                    for elem in row:
                        if elem is not None and isinstance(elem, list) and len(elem) == 3:
                            if elem[1] == 'red':
                                red_count += 1
                            elif elem[1] == 'black':
                                black_count += 1
                
                if red_count < 16 or black_count < 16:
                    self.board = self.merge_boards(self.board, new_board_data)
                    print("⚠️ AI走棋部分成功：棋盘已修复")
                    print("\n" + "="*80)
                    print("AI完整原始回答：")
                    print("="*80)
                    print(full_response)
                    print("="*80 + "\n")
                    return True
                
                new_board = []
                for row in new_board_data:
                    new_row = [convert_board_element(elem) for elem in row]
                    new_board.append(new_row)
                self.board = new_board
                print("✅ AI走棋成功")
                print("\n" + "="*80)
                print("AI完整原始回答：")
                print("="*80)
                print(full_response)
                print("="*80 + "\n")
                return True
            
            print("❌ AI走棋失败：响应中既没有move字段也没有board字段")
            print("\n" + "="*80)
            print("AI完整原始回答：")
            print("="*80)
            print(full_response)
            print("="*80 + "\n")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ AI走棋失败：JSON解析错误 - {e}")
            print("\n" + "="*80)
            print("AI完整原始回答：")
            print("="*80)
            print(full_response)
            print("="*80 + "\n")
            return False
        except Exception as e:
            print(f"❌ AI走棋失败：{e}")
            print("\n" + "="*80)
            print("AI完整原始回答：")
            print("="*80)
            print(full_response)
            print("="*80 + "\n")
            return False

    def main(self):
        ai_thread = None
        ai_queue = None
        ai_done = False
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.animating and not self.ai_thinking:
                    row, col = self.get_clicked_piece(mouse_pos)
                    
                    if row is not None and col is not None:
                        if (row, col) in self.valid_moves:
                            sr, sc = self.selected_piece
                            piece = self.board[sr][sc]
                            self.animate_move(piece, sr, sc, row, col)
                            self.board[sr][sc] = None
                            self.selected_piece = None
                            self.valid_moves = []
                        else:
                            piece = self.board[row][col]
                            if piece and piece[1] == self.current_player:
                                self.selected_piece = (row, col)
                                self.valid_moves = self.get_valid_moves(row, col)
                            else:
                                self.selected_piece = None
                                self.valid_moves = []
            
            if ai_queue is not None:
                try:
                    while True:
                        try:
                            msg_type, msg_data = ai_queue.get_nowait()
                            
                            if msg_type == 'chunk':
                                self.ai_thinking_text += msg_data
                                if len(self.ai_thinking_text) > 2000:
                                    self.ai_thinking_text = self.ai_thinking_text[-1500:]
                            elif msg_type == 'done':
                                self.ai_thinking = False
                                self.process_ai_response(msg_data)
                                self.current_player = 'red'
                                ai_queue = None
                                ai_thread = None
                                break
                            elif msg_type == 'error':
                                self.ai_thinking = False
                                self.ai_thinking_text = f"错误: {msg_data}"
                                self.current_player = 'red'
                                ai_queue = None
                                ai_thread = None
                                break
                        except queue.Empty:
                            break
                except:
                    pass
            
            if self.animating:
                self.animation_progress += 0.1
                if self.animation_progress >= 1.0:
                    self.animation_progress = 1.0
                    target_row, target_col = self.animation_target
                    if target_row is not None and target_col is not None:
                        self.board[target_row][target_col] = self.animation_piece
                    self.animating = False
                    self.animation_piece = None
                    self.animation_target = (None, None)
                    
                    self.game_over = False
                    self.check_flag = False
                    
                    opponent = 'black' if self.current_player == 'red' else 'red'
                    
                    general_found = False
                    for r in range(10):
                        for c in range(9):
                            p = self.board[r][c]
                            if p and p[1] == opponent:
                                if p[0] == '将' or p[0] == '帥':
                                    general_found = True
                                    break
                        if general_found:
                            break
                    
                    if not general_found:
                        self.game_over = True
                    else:
                        for r in range(10):
                            for c in range(9):
                                p = self.board[r][c]
                                if p and p[1] == opponent and p[0] != '将' and p[0] != '帥':
                                    moves = self.get_valid_moves(r, c)
                                    for mr, mc in moves:
                                        mp = self.board[mr][mc]
                                        if mp and (mp[0] == '将' or mp[0] == '帥') and mp[1] != opponent:
                                            self.check_flag = True
                                            break
                                    if self.check_flag:
                                        break
                            if self.check_flag:
                                break
                    
                    self.current_player = opponent
                    
                    if self.current_player == 'black':
                        self.ai_thinking = True
                        self.ai_thinking_text = ""
                        
                        prompt = f'''你是一个专业的中国象棋棋手，当前棋盘状态为：{self.board}

                        请按照以下步骤详细思考，每一步都要认真分析，为黑方选择一步最优的合法走法：

                        【第一步：局面分析】
                        仔细观察当前棋盘，分析黑方和红方各自的优势和劣势。注意双方的棋子数量、位置分布、战线推进情况。

                        【第二步：列举可移动棋子】
                        逐一列出黑方所有可以移动的棋子，标注它们当前位置。

                        【第三步：分析每个棋子的移动选项】
                        对每个可移动的棋子，详细分析它可以移动到哪些位置，以及每个选项的优劣。

                        【第四步：评估走法】
                        综合评估每个走法，考虑：
                        - 能否吃掉对方有价值的棋子
                        - 是否会让自己陷入危险
                        - 能否对对方将帅形成威胁
                        - 是否能控制战略要地
                        - 是否能加强防守或进攻

                        【第五步：选择最优走法】
                        经过深思熟虑，选择最有利的一步棋。

                        【第六步：总结理由】
                        详细解释为什么选择这步棋，它有什么特别之处。

                        注意：以上为思考过程，返回不要包含以上内容。请直接返回JSON格式的结果。

                        完成思考后，请以JSON格式返回结果：
                        {{
                            "analysis": "完整的思考过程，包括以上六个步骤的详细分析",
                            "move": {{
                                "from_row": 起始行号,
                                "from_col": 起始列号,
                                "to_row": 目标行号,
                                "to_col": 目标列号,
                                "piece_name": "棋子名称",
                                "reason": "走这步棋的理由"
                            }},
                            "board": [
                                棋盘内容
                            ]
                        }}

                        【重要说明】
                        1. board数组必须包含10行9列的完整棋盘
                        2. 红方和黑方的所有棋子都必须保留在board中
                        3. 只移动一个黑方棋子到新位置
                        4. 如果吃掉了红方棋子，从board中移除该红方棋子
                        5. 其他所有棋子位置保持不变
                        6. 使用null代替空位置
                        7. 只返回纯JSON，不要包含任何markdown格式
                        8. 保证棋盘完整，不带\n\n等特殊字符
                        '''
                        
                        ai_queue = queue.Queue()
                        ai_thread = threading.Thread(
                            target=self.ai_think_thread,
                            args=(prompt, ai_queue)
                        )
                        ai_thread.daemon = True
                        ai_thread.start()
            
            self.gui()
            pygame.display.flip()

if __name__ == '__main__':
    # 清空json文件,进入测试模式，保留当前牌面，仅测试 AI 回答后进行黑棋移动。
    try:
        os.remove("answer.json")
    except FileNotFoundError:
        pass
    game = Game()
    game.main()