
import sys
import os

# 添加项目路径
sys.path.insert(0, r"e:\coding-zhou\Python\python AI实战")

from video_call import make_call

if __name__ == "__main__":
    contact_name = sys.argv[1] if len(sys.argv) > 1 else "联系人"
    make_call(contact_name)
