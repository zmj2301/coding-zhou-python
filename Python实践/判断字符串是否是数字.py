# 利用强制转化的机制
# 如果可以转化则不报错返回true
# 否则转化失败则报错返回false
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

print(is_number("45a"))
print(is_number("412348"))