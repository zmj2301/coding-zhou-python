from tkinter import messagebox as mg
import pygame
import os
from ollama import chat
import subprocess
from tkinter.messagebox import askokcancel
import sys


pygame.init()
screen = pygame.display.set_mode((750,850))
pygame.display.set_caption("五子棋")

border_left = 25
border_right = 725
border_top = 25
border_bottom = 725
width = 50
height = 50

board = [0]*15
for i in range(15):
    board[i] = [0]*15

player = 1
winner = 0

font = pygame.font.Font("E:/coding-zhou/font.ttf",24)

class Button:
    def __init__(self,x,y,width,height,text,color,click_color,text_color) -> None:
        self.text = text
        self.color = color
        self.click_color = click_color
        self.text_color = text_color
        self.rect = pygame.Rect(x,y,width,height)
        self.clicked = False

    def draw(self,screen):
        if self.clicked:
            pygame.draw.rect(screen,self.click_color,self.rect)
        else:
            pygame.draw.rect(screen,self.color,self.rect)

        text_surface = font.render(self.text,True,self.text_color)
        text_rect = text_surface.get_rect(center= self.rect.center)
        screen.blit(text_surface,text_rect)

class game:
    def __init__(self) -> None:
        self.player 

def check(row,col):
    #判断左右方向是否五子连线
    score = 1
    for i in range(4):
        try:
            if board[row][col+i] == board[row][col+i+1]:
                score += 1
            else:
                break
        except:
            break
    for i in range(4):
        try:
            if board[row][col-i] == board[row][col-i-1]:
                score += 1
            else:
                break
        except:
            break

    if score >= 5:
        return True

    #判断上下方向是否五子连线
    score = 1
    for i in range(4):
        try:
            if board[row+i][col] == board[row+i+1][col]:
                score += 1
            else:
                break
        except:
            break
    for i in range(4):
        try:
            if board[row-i][col] == board[row-i-1][col]:
                score += 1
            else:
                break
        except:
            break
    if score >= 5:
        return True

    #判断左下到右上倾斜方向是否五子连线
    score = 1
    for i in range(4):
        try:
            if board[row+i][col+i] == board[row+i+1][col+i+1]:
                score += 1
            else:
                break
        except:
            break
    for i in range(4):
        try:
            if board[row-i][col-i] == board[row-i-1][col-i-1]:
                score += 1
            else:
                break
        except:
            break
    if score >= 5:
        return True

    #判断左上到右下倾斜方向是否五子连线
    score = 1
    for i in range(4):
        try:
            if board[row-i][col+i] == board[row-i-1][col+i+1]:
                score += 1
            else:
                break
        except:
            break
    for i in range(4):
        try:
            if board[row+i][col-i] == board[row+i+1][col-i-1]:
                score += 1
            else:
                break
        except:
            break
    if score >= 5:
        return True

dir = os.path.dirname(__file__)

background = pygame.image.load(os.path.join(dir,"img/background1.png"))
background = pygame.transform.scale(background,(background.get_width()*1.1,background.get_height()*1.1))
black_win_img = pygame.image.load(os.path.join(dir,"img/black_win.png"))
# black_win_img = pygame.transform.scale(black_win_img,(black_win_img.get_width()*1.1,black_win_img.get_height()*1.1))
white_win_img = pygame.image.load(os.path.join(dir,"img/white_win.png"))
# white_win_img = pygame.transform.scale(white_win_img,(white_win_img.get_width()*1.1,white_win_img.get_height()*1.1))
two_people_button_img = pygame.image.load(os.path.join(dir,"img/开始双人游戏.png"))
two_people_button_img = pygame.transform.scale(two_people_button_img,(140,55))
to_ai_button_img = pygame.image.load(os.path.join(dir,"img/开始对战AI.png"))
to_ai_button_img = pygame.transform.scale(to_ai_button_img,(140,50))
def 检查是否打开ollama服务():
    """
    检查ollama服务是否已启动
    """
    try:
        # 尝试执行ollama list，检查是否有响应
        subprocess.check_output(
            "ollama list",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=1.0  # 设置1秒超时
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # 捕获超时异常或命令执行失败异常，返回False
        return False
def open_cmd_and_run_ollama():
    """
    强制弹出CMD窗口并执行ollama run（Windows专用，确保窗口可见）
    """
    # 第一步：检查是否为Windows系统
    if sys.platform != "win32":
        print("❌ 此方案仅支持Windows系统！")
        return
    
    # 第二步：先验证ollama是否安装并配置环境变量
    try:
        # 静默执行ollama --version，验证命令是否可用
        subprocess.check_output(
            "ollama --version",
            shell=True,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        print("❌ 未找到ollama命令！请先：")
        print("  1. 安装ollama（官网：https://ollama.com/）")
        print("  2. 配置ollama到系统环境变量（或重启电脑让环境变量生效）")
        return
    
    # 第三步：构造强制弹出CMD的命令（修复核心）
    # start cmd 是Windows强制新建窗口的命令，优先级最高
    cmd = f'start cmd /k "ollama serve"'
    cmd2 = f'start cmd /k "ollama run minimax-m2.1:cloud"'
    
    try:
        # 执行命令（无需额外flags，start已强制新建窗口）
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=os.path.expanduser("~")  # 切换到用户主目录，避免路径问题
        )

        print(f"✅ 已弹出CMD窗口，执行命令：ollama run minimax-m2.1:cloud")
    except Exception as e:
        print(f"⚠️ 执行失败：{str(e)}")

if not 检查是否打开ollama服务():
    if askokcancel("确认", f"ollama服务未启动，是否尝试启动？"):
        print("ollama服务未启动，尝试启动...")
        open_cmd_and_run_ollama()

state = 'peoles'

running = True
mouse_down = False
while running:
    mouse_down = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_down = True
                x,y = pygame.mouse.get_pos()
                col =  round((x - 25)/50)
                row =  round((y - 25)/50)
                if x >= border_left and x <= border_right and y >= border_top and y <= border_bottom:
                    if board[row][col] == 0:
                        print(row+1,col+1)
                        board[row][col] = player
                        if(check(row,col)):
                            winner = player
                            if player == 1:
                                player = 2
                            else:
                                player = 1
                        else:
                            if player == 1:
                                player = 2
                            else:
                                player = 1
                else:
                    print("没看到已经有棋子了吗？")

    screen.fill("#EE9A49")
    screen.blit(background,(-150,-20))

    # 竖线
    for x in range(15):
        pygame.draw.line(screen,'#000000',[border_left+width*x,border_top],[border_left+width*x,border_bottom],2)
    #横线
    for y in range(15):
        pygame.draw.line(screen,'#000000',[border_left,border_top+height*y],[border_right,border_top+height*y],2)

    pygame.draw.circle(screen,"#000000",[25+50*7,25+50*7],8)

    x,y = pygame.mouse.get_pos()
    if x >= border_left and x <= border_right and y >= border_top and y <= border_bottom:
        x = round((x - border_left)/width)*width + border_left
        y = round((y - border_top)/height)*height + border_top
        # 绘制黑方还是白方
        if player == 1:
            pygame.draw.rect(screen,'#000000',[x-25,y-25,50,50],2)
        else:
            pygame.draw.rect(screen,'#FFFFFF',[x-25,y-25,50,50],2)

    # button = Button(50,750,100,50,"双人模式",(153,51,250),(221,160,221),(255,255,255))
    # button.draw(screen)

    # button = Button(200,750,100,50,"AI模式",(153,51,250),(221,160,221),(255,255,255))
    # button.draw(screen)
    screen.blit(two_people_button_img,(50,770))
    screen.blit(to_ai_button_img,(200,770))
    to_ai_button_rect = to_ai_button_img.get_rect(topleft = (200,770))
    if to_ai_button_rect.collidepoint(x,y):
        if mouse_down:
            state = 'ai'
            board = [0]*15
            for i in range(15):
                board[i] = [0]*15
        
    if state == 'ai':
        if player == 2:
            print("AI思考中...")
            # 提取黑白棋子坐标
            black_positions = []
            white_positions = []
            for row in range(15):
                for col in range(15):
                    if board[row][col] == 1:
                        black_positions.append((row+1, col+1))  # 转换为1-15的坐标，更符合人类习惯
                    elif board[row][col] == 2:
                        white_positions.append((row+1, col+1))
            
            # 构造提示词，要求AI返回具体的落子坐标
            prompt = f"你是一个五子棋AI，现在轮到白方(2)落子。\n"
            prompt += f"当前棋盘状态：\n"
            prompt += f"黑方(1)棋子位置：{black_positions}\n"
            prompt += f"白方(2)棋子位置：{white_positions}\n"
            prompt += f"请根据当前棋盘状态，分析并返回最佳落子位置。\n"
            prompt += f"要求：只返回行和列的数字，用逗号分隔，行和列范围都是1-15，不要返回其他任何内容。例如：8,8"
            
            response = chat(model="minimax-m2.1:cloud", messages=[{"role": "user", "content": prompt}])
            ai_response = response["message"]["content"].strip()
            print(f"AI返回：{ai_response}")
            
            # 解析AI返回的坐标
            try:
                ai_row, ai_col = tuple(int(x) for x in ai_response.split(","))
                # 转换为0-14的索引
                ai_row -= 1
                ai_col -= 1
                
                # 检查坐标是否有效且该位置为空
                if 0 <= ai_row < 15 and 0 <= ai_col < 15 and board[ai_row][ai_col] == 0:
                    board[ai_row][ai_col] = player
                    if check(ai_row, ai_col):
                        winner = player
                    player = 1
                else:
                    print("AI返回的坐标无效或该位置已有棋子，重新生成")
            except Exception as e:
                print(f"解析AI返回失败：{e}，重新生成")

    for row in range(15):
        for col in range(15):
            if board[row][col] == 1:
                pygame.draw.circle(screen,"#000000",[col*width+border_left,row*height+border_top],25)

            elif board[row][col] == 2:
                pygame.draw.circle(screen,"#FFFFFF",[col*width+border_left,row*height+border_top],25)  
                

    pygame.display.update()

    if(winner!=0):
        if winner == 1:
            screen.blit(black_win_img,(-150,-20))
            pygame.display.update()
            if mg.showinfo("游戏结束","恭喜黑方获胜！"):
                running = False
        else:
            screen.blit(white_win_img,(-150,-20))
            pygame.display.update()
            if mg.showinfo("游戏结束","恭喜白方获胜！"):
                running = False
        

pygame.quit()