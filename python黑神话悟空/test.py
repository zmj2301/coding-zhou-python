import pygame

class ChatBubble:
    def __init__(self, font, max_width=400, padding=15, typing_speed=80):
        self.font = font
        self.max_width = max_width
        self.padding = padding
        self.typing_speed = typing_speed

        self.dialogue = ""
        self.current_text = ""
        self.text_index = 0
        self.typing_event = pygame.USEREVENT + 1

        # 启动打字计时器
        pygame.time.set_timer(self.typing_event, typing_speed)

    def set_dialogue(self, text):
        self.dialogue = text
        self.current_text = ""
        self.text_index = 0

    def update(self):
        if self.text_index < len(self.dialogue):
            self.current_text += self.dialogue[self.text_index]
            self.text_index += 1

    def _wrap_text(self, text):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            w, h = self.font.size(test_line)
            if w <= self.max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        line_h = self.font.get_linesize()
        total_h = len(lines) * line_h
        max_w = max(self.font.size(line)[0] for line in lines) if lines else 0

        surf = pygame.Surface((max_w, total_h), pygame.SRCALPHA)
        y = 0
        for line in lines:
            ls = self.font.render(line, True, (0, 0, 0))
            surf.blit(ls, (0, y))
            y += line_h
        return surf, max_w, total_h

    def draw(self, screen, x, y):
        if not self.current_text:
            return
        text_surf, w, h = self._wrap_text(self.current_text)
        rect = pygame.Rect(x, y,
                           w + 2 * self.padding,
                           h + 2 * self.padding)
        pygame.draw.rect(screen, (220, 220, 255), rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)
        screen.blit(text_surf, (x + self.padding, y + self.padding))

# ==================== 主程序 ====================
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("泡泡说话类封装版")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 32)

    # 创建泡泡实例
    bubble = ChatBubble(font, max_width=420, typing_speed=70)
    bubble.set_dialogue("走走走游游游，甘为铜钱做马牛。做人哪比做妖好，不怕阎王命不休。")

    avatar_rect = pygame.Rect(100, 200, 180, 180)

    running = True
    while running:
        screen.fill((30, 30, 30))

        # 白色角色
        pygame.draw.rect(screen, (255, 255, 255), avatar_rect, border_radius=12)
        pygame.draw.rect(screen, (120, 120, 120), avatar_rect, 2, border_radius=12)

        # 绘制泡泡
        bubble.draw(screen, 330, 200)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == bubble.typing_event:
                bubble.update()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()