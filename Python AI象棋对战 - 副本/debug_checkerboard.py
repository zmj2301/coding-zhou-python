"""
棋盘位置/尺寸调试工具
================================
用途：快速调整 checkerboard（棋盘）的 x、y 坐标以及缩放宽高，
      通过键盘实时微调，找到合适的值后回填到 Chinese_chess.py。

运行：
    python debug_checkerboard.py

按键说明：
    方向键 ← → ↑ ↓       调整棋盘 blit 偏移 (x, y)，步长由 STEP 决定
    [ / ]                 减小 / 增大 步长 STEP（1 / 5 / 10 循环）
    - / = (或 0 / 9)      调整棋盘缩放宽度（宽高按比例同步）
    , / .                 仅调整缩放高度（宽高独立）
    S                     保存当前偏移与缩放值到 checkerboard_layout.json
    R                     重置为初始值
    Q / ESC               退出

输出参考（保存的 JSON 与打印内容）：
    {
      "board_offset_x": 30,   # 约等于 blit_x - 20
      "board_offset_y": 30,   # 约等于 blit_y + 10
      "blit_x": 50,
      "blit_y": 20,
      "scale_w": 531,
      "scale_h": 593
    }
    回填 Chinese_chess.py：
      self.board_offset_x = blit_x - 20
      self.board_offset_y = blit_y + 10
      self.checkerboard = pygame.transform.scale(orig, (scale_w, scale_h))
"""

import os
import sys
import json

import pygame

# 让脚本无论从哪个目录运行都能找到资源
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'img')
FONT_PATH = os.path.join(BASE_DIR, 'font.ttf')

# 原始棋盘图（未缩放），用于按宽高比复位
ORIG_BOARD_PATH = os.path.join(IMG_DIR, '棋盘.png')

# 初始值（与 Chinese_chess.py 当前取值保持一致，便于对照）
INIT_BLIT_X = 50    # board_offset_x(30) + 20
INIT_BLIT_Y = 20    # board_offset_y(30) - 10
INIT_SCALE_W = 531  # 原图宽 * 1.02（大约值，运行后会按实际原图尺寸校正）
INIT_SCALE_H = 593  # 原图高 * 1 + 33

SAVE_PATH = os.path.join(BASE_DIR, 'checkerboard_layout.json')

# 步长档位
STEP_LEVELS = [1, 5, 10]
STEP_INDEX = 1  # 默认 5


def load_font(size):
    if os.path.exists(FONT_PATH):
        return pygame.font.Font(FONT_PATH, size)
    return pygame.font.SysFont('simhei', size)


def main():
    global STEP_INDEX

    pygame.init()
    screen = pygame.display.set_mode((1200, 680))
    pygame.display.set_caption("棋盘调试工具 (Checkerboard Debugger)")
    clock = pygame.time.Clock()

    # 加载原图作为基准
    orig = pygame.image.load(ORIG_BOARD_PATH).convert_alpha()
    orig_w, orig_h = orig.get_size()

    # 校正初始缩放值（保持原图宽高比按比例）
    blit_x, blit_y = INIT_BLIT_X, INIT_BLIT_Y
    # 以 INIT_SCALE_W 为基准宽度，高度按比例
    scale_w = INIT_SCALE_W
    scale_h = int(round(orig_h * (scale_w / orig_w)))

    board_surf = pygame.transform.scale(orig, (scale_w, scale_h))

    font_small = load_font(20)
    font_mid = load_font(24)

    running = True
    while running:
        step = STEP_LEVELS[STEP_INDEX]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_LEFT:
                    blit_x -= step
                elif event.key == pygame.K_RIGHT:
                    blit_x += step
                elif event.key == pygame.K_UP:
                    blit_y -= step
                elif event.key == pygame.K_DOWN:
                    blit_y += step
                elif event.key == pygame.K_LEFTBRACKET:   # [
                    STEP_INDEX = (STEP_INDEX - 1) % len(STEP_LEVELS)
                elif event.key == pygame.K_RIGHTBRACKET:  # ]
                    STEP_INDEX = (STEP_INDEX + 1) % len(STEP_LEVELS)
                elif event.key in (pygame.K_MINUS, pygame.K_0):
                    scale_w = max(50, scale_w - step)
                    scale_h = int(round(orig_h * (scale_w / orig_w)))
                elif event.key in (pygame.K_EQUALS, pygame.K_9):
                    scale_w += step
                    scale_h = int(round(orig_h * (scale_w / orig_w)))
                elif event.key == pygame.K_COMMA:   # , 仅改高度
                    scale_h = max(50, scale_h - step)
                elif event.key == pygame.K_PERIOD:  # . 仅改高度
                    scale_h += step
                elif event.key == pygame.K_r:
                    blit_x, blit_y = INIT_BLIT_X, INIT_BLIT_Y
                    scale_w = INIT_SCALE_W
                    scale_h = int(round(orig_h * (scale_w / orig_w)))
                elif event.key == pygame.K_s:
                    layout = {
                        "board_offset_x": blit_x - 20,
                        "board_offset_y": blit_y + 10,
                        "blit_x": blit_x,
                        "blit_y": blit_y,
                        "scale_w": scale_w,
                        "scale_h": scale_h,
                    }
                    with open(SAVE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(layout, f, ensure_ascii=False, indent=2)
                    print("[已保存] checkerboard_layout.json:")
                    print(json.dumps(layout, ensure_ascii=False, indent=2))

                # 尺寸变化后实时重新缩放
                board_surf = pygame.transform.scale(orig, (scale_w, scale_h))

        # 绘制
        screen.fill((165, 105, 0))  # BROWN 背景
        screen.blit(board_surf, (blit_x, blit_y))

        # 叠加信息文字
        lines = [
            f"blit_x={blit_x}  blit_y={blit_y}",
            f"scale_w={scale_w}  scale_h={scale_h}",
            f"board_offset_x={blit_x - 20}  board_offset_y={blit_y + 10}",
            f"STEP={step} (按 [ / ] 调整步长)",
            "",
            "方向键: 移动   -/=: 宽度(等比)   ,/.: 仅高度",
            "R: 重置   S: 保存   Q/ESC: 退出",
        ]
        y = 10
        for line in lines:
            surf = font_small.render(line, True, (255, 255, 255))
            screen.blit(surf, (10, y))
            y += 26

        # 画一个标记框，标出棋盘边界
        pygame.draw.rect(screen, (255, 0, 0),
                         pygame.Rect(blit_x, blit_y, scale_w, scale_h), 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    # 退出时打印最终值，方便直接复制
    final = {
        "board_offset_x": blit_x - 20,
        "board_offset_y": blit_y + 10,
        "scale_w": scale_w,
        "scale_h": scale_h,
    }
    print("[退出] 最终棋盘参数:")
    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
