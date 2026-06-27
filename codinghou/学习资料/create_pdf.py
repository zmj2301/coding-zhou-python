from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# 创建PDF对象
c = canvas.Canvas("数学题目.pdf", pagesize=A4)
width, height = A4

# 设置字体和初始位置
c.setFont("Helvetica", 12)
y = height - 2*cm

# 添加文字内容
text = "题目\n"
text += "（1）观察发现：\n"
text += "解方程组 {x + y = 4 ①\n"
text += "          3(x + y) + y = 14 ②\n"
text += "将①整体代入②，得3×4 + y = 14，解得y = 2.\n"
text += "将y = 2代入①，解得x = 2，\n"
text += "所以原方程组的解是 {x = 2\n"
text += "                      y = 2\n"
text += "这种解法称为\"整体代入法\"，你若留心观察，\n"
text += "会发现有很多方程组可采用此方法求解.\n"
text += "请写出方程组 {x - y - 1 = 0 ①\n"
text += "              4(x - y) - y = 5 ② 的解为______；\n"
text += "（2）实践运用：请用\"整体代入法\"解方程组：\n"
text += "{2x - 3y - 2 = 0 ①\n"
text += " {(2x - 3y + 5)/7 + 2y = 9 ②\n"
text += "（3）已知x,y满足方程组\n"
text += "{3x² - 2xy + 12y² = 47\n"
text += " {2x² + xy + 8y² = 36 ，求x² + 4y² - xy的值.\n"

# 写入文字到PDF
lines = text.split('\n')
for line in lines:
    c.drawString(2*cm, y, line)
    y -= 0.5*cm

# 保存PDF文件
c.save()

print("PDF文件已生成：数学题目.pdf")