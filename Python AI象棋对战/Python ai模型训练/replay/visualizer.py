# 可视化复盘报告模块
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime


class GameVisualizer:
    """游戏可视化器"""
    
    # 棋子字符
    PIECE_CHARS = {
        0: '',
        1: '帥', 2: '仕', 3: '相', 4: '馬', 5: '車', 6: '炮', 7: '兵',
        -8: '將', -9: '士', -10: '象', -11: '馬', -12: '車', -13: '炮', -14: '卒'
    }
    
    @staticmethod
    def plot_board(board_state, title="", ax=None):
        """绘制棋盘"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 9))
        
        ax.set_xlim(-0.5, 8.5)
        ax.set_ylim(-0.5, 9.5)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        
        # 绘制网格
        for i in range(10):
            ax.axhline(i, color='k', linewidth=0.5)
        for i in range(9):
            ax.axvline(i, color='k', linewidth=0.5)
        
        # 绘制九宫格
        rect1 = patches.Rectangle((2.5, -0.5), 4, 3, 
                                  linewidth=1, edgecolor='k', facecolor='none')
        rect2 = patches.Rectangle((2.5, 6.5), 4, 3, 
                                  linewidth=1, edgecolor='k', facecolor='none')
        ax.add_patch(rect1)
        ax.add_patch(rect2)
        
        # 绘制楚河汉界
        ax.text(4, 4.5, '楚河汉界', ha='center', va='center', 
                fontsize=14, fontweight='bold', color='k')
        
        # 绘制棋子
        for r in range(10):
            for c in range(9):
                p = board_state[r][c]
                if p != 0:
                    piece = GameVisualizer.PIECE_CHARS[p]
                    color = 'red' if p > 0 else 'black'
                    ax.text(c, r, piece, ha='center', va='center', 
                            fontsize=18, color=color, fontweight='bold',
                            bbox=dict(boxstyle='circle,pad=0.3', 
                                     facecolor='white', 
                                     edgecolor=color))
        
        # 坐标标签
        ax.set_xticks(range(9))
        ax.set_yticks(range(10))
        ax.set_xticklabels(['a','b','c','d','e','f','g','h','i'])
        ax.set_yticklabels([str(9-i) for i in range(10)])
        
        ax.set_title(title, fontsize=14, pad=20)
        ax.grid(False)
        
        return ax
    
    @staticmethod
    def plot_score_curve(scores, title="局面评分曲线", ax=None):
        """绘制评分曲线"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        
        steps = range(1, len(scores) + 1)
        ax.plot(steps, scores, 'o-', linewidth=2, color='b', 
                label='评分')
        
        # 标注关键节点
        if scores:
            max_idx = np.argmax(scores)
            min_idx = np.argmin(scores)
            ax.scatter([max_idx+1], [scores[max_idx]], c='g', s=100, zorder=5)
            ax.scatter([min_idx+1], [scores[min_idx]], c='r', s=100, zorder=5)
        
        ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
        ax.set_xlabel('步数', fontsize=12)
        ax.set_ylabel('评分', fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return ax
    
    @staticmethod
    def generate_html_report(game_info, analysis, output_dir='data/reports'):
        """生成HTML复盘报告"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = f"replay_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(output_dir, filename)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>中国象棋AI 复盘报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 15px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .info-box {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .red {{ color: #e74c3c; }}
        .green {{ color: #27ae60; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>中国象棋AI 复盘报告</h1>
        
        <div class="info-box">
            <h2>对局信息</h2>
            <p><strong>开始时间:</strong> {game_info.get('start_time', 'N/A')}</p>
            <p><strong>结束时间:</strong> {game_info.get('end_time', 'N/A')}</p>
            <p><strong>总步数:</strong> {game_info.get('total_moves', 0)}</p>
        </div>
        
        <h2>走法记录</h2>
        <table>
            <thead>
                <tr>
                    <th>步数</th>
                    <th>走法</th>
                    <th>评分</th>
                    <th>将军</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for step_analysis in analysis:
            step = step_analysis.get('step', 0)
            move = step_analysis.get('actual_move', '')
            score = step_analysis.get('evaluation', 0)
            is_check = step_analysis.get('is_check', False)
            
            score_color = 'green' if score > 0 else 'red' if score < 0 else ''
            check_str = '是' if is_check else '否'
            
            html += f"""
                <tr>
                    <td>{step}</td>
                    <td>{move}</td>
                    <td class="{score_color}">{score:.4f}</td>
                    <td>{check_str}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"复盘报告已生成: {filepath}")
        return filepath
