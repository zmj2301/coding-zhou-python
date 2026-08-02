# Python实践

一组 Python 编程练习脚本合集，包含文件批量操作与字符串判断等实用小工具，适合初学者学习 Python 基础语法。

## 包含脚本

### 1. 判断字符串是否是数字（`判断字符串是否是数字.py`）

利用 Python 强制类型转化机制判断字符串能否转为数字：

```python
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
```

- `is_number("45a")` → `False`
- `is_number("412348")` → `True`

### 2. 批量修改文件名（`批量修改文件名.py`）

文件重命名 / 删除的操作示例，内含注释掉的交互式重命名代码，以及按路径删除文件的示例。

## 环境要求

- Python 3.7+（仅标准库）

## 运行

```bash
cd "Python实践"
python 判断字符串是否是数字.py
python 批量修改文件名.py
```

## 学习要点

- 异常处理（`try / except ValueError`）
- 字符串与数字的强制转换
- `os` 模块的文件操作（`os.rename`、`os.remove`）

## 许可证

本项目仅供学习交流使用。
