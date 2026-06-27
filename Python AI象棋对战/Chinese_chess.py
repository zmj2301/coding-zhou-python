import pygame
import os
from ai_player import AIPlayer

pygame.init()

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((840, 680))
        self.BROWN = (165, 105, 0)
        pygame.display.set_caption("中国棋")
        
        self.checkerboard = pygame.image.load(os.path.join('img', '棋盘.png'))
        self.checkerboard = pygame.transform.scale(self.checkerboard,(self.checkerboard.get_width()*1.02-25, self.checkerboard.get_height()*1.02+20))
        self.image_names = ['红_仕.png', '红_兵.png', '红_帥.png', '红_炮.png', '红_相.png', '红_車.png', '红_馬.png', '黑_卒.png', '黑_士.png', '黑_将.png', '黑_炮.png', '黑_象.png', '黑_車.png', '黑_馬.png']
        self.images = [pygame.transform.scale(pygame.image.load(os.path.join('img', name)), (50, 50)) for name in self.image_names]
        
        self.font_32 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 32)
        self.font_24 = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'), 24)
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
        
        # AI思考信息
        self.ai_thinking = False
        self.ai_thought_message = ""
        self.ai_thought_moves = []
        self.ai_best_move = None
        self.ai_thought_summary = ""
        
        # AI滚动显示信息
        self.ai_thought_log = []  # 存储思考历史
        self.ai_thought_scroll_y = 0  # 滚动位置
        self.ai_thought_displaying = False  # 是否正在显示思考
        self.ai_thought_frame = 0  # 动画帧计数
        self.ai_thought_steps = []  # 当前思考步骤列表
        self.ai_thought_step_idx = 0  # 当前显示到第几步
        self.ai_thought_animating = False  # 是否正在播放思考动画
        self.ai_thought_timer = 0  # 思考步骤计时器

        model_path = self._find_model()
        self.ai_player = AIPlayer(model_path=model_path, difficulty=2)
    
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
    
    def _wrap_text(self, text, max_chars):
        """将文本分割成多行"""
        lines = []
        current_line = ""
        words = text.split()
        
        for word in words:
            if len(current_line + word) <= max_chars:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 如果没有空格分割，直接按字符分割
        if not lines:
            for i in range(0, len(text), max_chars):
                lines.append(text[i:i+max_chars])
        
        return lines
    
    def animate_move(self, piece, start_row, start_col, end_row, end_col):
        self.animating = True
        self.animation_piece = piece
        self.animation_start = self.get_piece_position(start_row, start_col)
        self.animation_end = self.get_piece_position(end_row, end_col)
        self.animation_target = (end_row, end_col)
        self.animation_progress = 0.0

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
        
        # 显示AI思考信息区域（始终显示）
        info_x = 580
        info_y = 50
        panel_width = 250
        panel_height = 580
        pygame.draw.rect(self.screen, (40, 45, 70), (info_x - 10, info_y - 10, panel_width, panel_height))
        

        
        # 标题
        title_text = self.font_24.render("AI 思考", True, (255, 210, 120))
        self.screen.blit(title_text, (info_x, info_y))
        info_y += 40
        
        # 如果有思考历史，显示滚动面板
        if self.ai_thought_log or self.ai_thinking or self.ai_thought_animating:
            # 滚动区域
            scroll_x = info_x
            scroll_y_start = info_y
            scroll_height = 400
            scroll_width = 230
            
            # 绘制滚动背景
            pygame.draw.rect(self.screen, (30, 35, 60), (scroll_x - 5, scroll_y_start - 5, scroll_width, scroll_height))
            
            # 显示当前思考
            current_y = scroll_y_start
            
            if self.ai_thought_animating and self.ai_thought_steps:
                # 显示正在播放思考过程
                thinking_label = self.font_24.render("AI 正在思考...", True, (255, 220, 120))
                self.screen.blit(thinking_label, (scroll_x, current_y))
                current_y += 35
                
                # 显示已完成的思考步骤
                for i, step_text in enumerate(self.ai_thought_steps[:self.ai_thought_step_idx]):
                    if current_y + 30 < scroll_y_start + scroll_height:
                        lines = self._wrap_text(step_text, 22)
                        for line in lines:
                            color = (150, 255, 150)  # 绿色表示已完成
                            text = self.font_24.render(line, True, color)
                            self.screen.blit(text, (scroll_x, current_y))
                            current_y += 28
                
                # 显示正在进行的步骤
                if self.ai_thought_step_idx < len(self.ai_thought_steps):
                    if current_y + 30 < scroll_y_start + scroll_height:
                        current_step = self.ai_thought_steps[self.ai_thought_step_idx]
                        lines = self._wrap_text(current_step, 22)
                        for line in lines:
                            color = (255, 255, 150)  # 黄色表示进行中
                            text = self.font_24.render(line, True, color)
                            self.screen.blit(text, (scroll_x, current_y))
                            current_y += 28
                
                # 进度提示
                progress = f"{self.ai_thought_step_idx}/{len(self.ai_thought_steps)}"
                prog_text = self.font_24.render(progress, True, (150, 150, 200))
                self.screen.blit(prog_text, (scroll_x, scroll_y_start + scroll_height - 30))
            
            elif self.ai_thinking:
                # 显示"思考中"
                thinking_label = self.font_24.render("分析中...", True, (150, 200, 255))
                self.screen.blit(thinking_label, (scroll_x, current_y))
                current_y += 35
                
                # 显示思考摘要（如果有）
                if hasattr(self, 'ai_thought_summary') and self.ai_thought_summary:
                    text = self.ai_thought_summary
                    # 换行显示
                    lines = self._wrap_text(text, 20)
                    for line in lines:
                        if current_y + 30 < scroll_y_start + scroll_height:
                            msg_text = self.font_24.render(line, True, (220, 220, 255))
                            self.screen.blit(msg_text, (scroll_x, current_y))
                            current_y += 30
                
                # 显示候选走法
                if self.ai_thought_moves and current_y < scroll_y_start + scroll_height - 100:
                    current_y += 10
                    move_title = self.font_24.render("候选走法:", True, (100, 255, 150))
                    self.screen.blit(move_title, (scroll_x, current_y))
                    current_y += 35
                    
                    for i, move_info in enumerate(self.ai_thought_moves[:3], 1):
                        if current_y + 30 < scroll_y_start + scroll_height:
                            is_best = move_info == self.ai_best_move
                            color = (255, 150, 150) if is_best else (200, 200, 200)
                            move_text = f"{i}. {move_info['move']}"
                            if move_info['captured']:
                                move_text += f" 吃{move_info['captured']}"
                            text = self.font_24.render(move_text, True, color)
                            self.screen.blit(text, (scroll_x, current_y))
                            current_y += 30
            else:
                # 显示历史思考（滚动显示）
                current_y = scroll_y_start - self.ai_thought_scroll_y
                
                # 从新到旧显示
                for thought in reversed(self.ai_thought_log[-20:]):
                    if current_y + 50 > scroll_y_start and current_y < scroll_y_start + scroll_height:
                        # 显示步数
                        step_text = self.font_24.render(f"第 {thought['step']} 步", True, (180, 180, 200))
                        self.screen.blit(step_text, (scroll_x, current_y))
                        current_y += 30
                        
                        # 显示摘要（换行）
                        summary = thought.get('summary', '')
                        lines = self._wrap_text(summary, 20)
                        for line in lines:
                            if current_y + 30 < scroll_y_start + scroll_height:
                                text = self.font_24.render(line, True, (200, 200, 220))
                                self.screen.blit(text, (scroll_x + 10, current_y))
                                current_y += 28
                        
                        # 分隔线
                        if current_y < scroll_y_start + scroll_height:
                            pygame.draw.line(self.screen, (60, 65, 100), (scroll_x, current_y), (scroll_x + 200, current_y), 1)
                            current_y += 15
                    elif current_y > scroll_y_start + scroll_height:
                        break
        
        # 滚动提示
        if len(self.ai_thought_log) > 5:
            scroll_hint = self.font_24.render("滚动查看历史", True, (150, 150, 180))
            self.screen.blit(scroll_hint, (info_x, 540))

    def main(self):
        # 游戏一开始，如果AI是黑方且当前轮到黑方，先让AI走棋
        ai_should_move = (self.current_player == 'black') and not self.game_over

        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.animating:
                    # 处理滚轮滚动
                    if event.button == 4:  # 向上滚动
                        self.ai_thought_scroll_y = max(0, self.ai_thought_scroll_y - 30)
                    elif event.button == 5:  # 向下滚动
                        self.ai_thought_scroll_y += 30
                    # 只有轮到人类玩家（红方）时才响应鼠标点击
                    elif self.current_player == 'red' and not self.game_over:
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
            
            # 轮到AI走棋且没有在动画中
            if ai_should_move and not self.animating and not self.game_over:
                ai_should_move = False
                self.local_ai_move()
            
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
                    
                    # 切换回合
                    self.current_player = opponent
                    # 如果下一轮是黑方AI，标记AI应该走棋
                    if self.current_player == 'black' and not self.game_over:
                        ai_should_move = True
            
            self.gui()
            pygame.display.flip()
    
    def _find_model(self):
        candidates = [
            os.path.join(os.path.dirname(__file__), 'ai_trained_final.pth'),
            os.path.join(os.path.dirname(__file__), 'ai_trained_latest.pth'),
            os.path.join(os.path.dirname(__file__), 'chess_model_500.pth'),
            os.path.join(os.path.dirname(__file__), 'chess_model_450.pth'),
            os.path.join(os.path.dirname(__file__), 'chess_model.pth'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def local_ai_move(self):
        self.ai_thinking = True
        self.ai_thought_message = "正在分析局面..."
        self.ai_thought_summary = ""
        
        # 直接调用 AI 计算
        best_move, thought = self.ai_player.get_best_move_with_thought(self.board, self.get_valid_moves, player_color='black')
        
        if best_move and thought:
            self.ai_thought_summary = thought.get('summary', '')
            self.ai_thought_moves = thought.get('candidate_moves', [])
            self.ai_thought_message = f"找到 {thought['all_moves_count']} 种走法"
            self.ai_thought_history = thought
            
            # 显示到右侧
            record = {
                'step': len(self.ai_thought_log) + 1,
                'move': best_move,
                'summary': thought.get('summary', ''),
                'all_moves_count': thought.get('all_moves_count', 0),
                'best_score': thought.get('best_score', 0)
            }
            self.ai_thought_log.append(record)
        
        if best_move:
            # 显示最佳走法
            self.ai_best_move = None
            for move_info in self.ai_thought_moves:
                if move_info['move'] == best_move:
                    self.ai_best_move = move_info
                    break
            
            self.gui()
            pygame.display.flip()
            pygame.time.delay(200)
            
            # 执行走棋动画
            sr, sc, nr, nc = best_move
            piece = self.board[sr][sc]
            self.animate_move(piece, sr, sc, nr, nc)
            self.board[sr][sc] = None
        
        self.ai_thinking = False

if __name__ == '__main__':
    game = Game()
    game.main()