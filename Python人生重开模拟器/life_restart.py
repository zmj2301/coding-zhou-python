from pickle import INT
import random
import time
import os
import json
from tkinter import messagebox as mg

events_dict = {}
age_events = {}

event_file = os.path.abspath("events.json")
age_event_file = os.path.abspath("age.json")
def get_all_events():
    if os.path.isfile(event_file):
        with open(event_file, "r", encoding="utf-8") as f:
            temp = json.load(f)
            for k in temp.keys():
                events_dict[int(k)] = temp[k]  # 存储完整事件对象
        
        return events_dict
    else:
        mg.showinfo("提示", "事件文件不存在")
        exit()
def get_age_events():
    if os.path.isfile(age_event_file):
        with open(age_event_file, "r", encoding="utf-8") as f:
            temp = json.load(f)
            for k in temp.keys():
                event_list = temp[k]['event']
                # 过滤掉events.json中不存在的事件
                filtered = []
                for item in event_list:
                    item_str = str(item)
                    eid = int(item_str.split('*')[0])
                    if eid in events:
                        filtered.append(item)
                age_events[int(k)] = filtered
        return age_events
    else:
        mg.showinfo("提示", "年龄事件文件不存在")
        exit()

def weight_choice(age_list):
    weight_event = {}
    for item in age_list:
        if '*' in str(item):
            _list = str(item).split('*')
            weight_event[int(_list[0])] = float(_list[1])
        else:
            weight_event[int(item)] = 1
    
    rnd = random.random() * sum(weight_event.values())
    cumulative = 0
    for key,value in weight_event.items():
        cumulative += value
        if rnd <= cumulative:
            return key
        
            
past = {}
events = get_all_events()
age_event_list = get_age_events()

# 当前属性值（初始值来自用户输入）
current_stats = {
    'CHR': 0,  # 颜值
    'STR': 0,  # 体质
    'INT': 0,  # 智力
    'MNY': 0,  # 家境
    'SPR': 5,  # 精神（初始值5）
    'LIF': 100 # 生命（初始值100）
}

def check_condition(condition, stats, past_events):
    """
    解析条件表达式，如 "CHR>7", "MNY>4", "EVT?[10009]"
    返回 True/False
    """
    if not condition:
        return True
    
    condition = condition.strip()
    
    # 处理括号
    while '(' in condition:
        # 找到最内层括号
        start = condition.rfind('(')
        end = condition.find(')', start)
        if start == -1 or end == -1:
            break
        inner = condition[start+1:end]
        result = check_condition(inner, stats, past_events)
        condition = condition[:start] + str(result) + condition[end+1:]
    
    # 处理 OR (|)
    if '|' in condition:
        parts = condition.split('|')
        return any(check_condition(p.strip(), stats, past_events) for p in parts)
    
    # 处理 AND (&)
    if '&' in condition:
        parts = condition.split('&')
        return all(check_condition(p.strip(), stats, past_events) for p in parts)
    
    # 处理事件检查: EVT?[10009,10010]
    if 'EVT?' in condition:
        import re
        match = re.search(r'EVT?\[([^\]]+)\]', condition)
        if match:
            event_ids = [int(x.strip()) for x in match.group(1).split(',')]
            return any(eid in past_events for eid in event_ids)
        return False
    
    # 处理天赋检查: TLT?[1001] (暂时返回False，因为没有天赋系统)
    if 'TLT?' in condition:
        return False
    
    # 处理属性比较: CHR>7, STR<3, MNY>=5, INT<=8, CHR==5, INT!=3
    import re
    match = re.match(r'(CHR|STR|INT|MNY|SPR|LIF)(>=|<=|>|<|==|!=)(\d+)', condition)
    if match:
        stat = match.group(1)
        op = match.group(2)
        value = int(match.group(3))
        current_value = stats.get(stat, 0)
        
        if op == '>':
            return current_value > value
        elif op == '<':
            return current_value < value
        elif op == '>=':
            return current_value >= value
        elif op == '<=':
            return current_value <= value
        elif op == '==':
            return current_value == value
        elif op == '!=':
            return current_value != value
    
    # 处理布尔值字符串
    if condition == 'True':
        return True
    if condition == 'False':
        return False
    
    return False

def filter_events_by_conditions(age_list, stats, past_events):
    """过滤满足 include/exclude 条件的事件"""
    valid_events = []
    for item in age_list:
        event_id = int(str(item).split('*')[0])
        event_data = events.get(event_id)
        if not event_data:
            continue
        
        # 检查 include 条件
        include_cond = event_data.get('include')
        if include_cond and not check_condition(include_cond, stats, past_events):
            continue
        
        # 检查 exclude 条件
        exclude_cond = event_data.get('exclude')
        if exclude_cond and check_condition(exclude_cond, stats, past_events):
            continue
        
        valid_events.append(item)
    
    return valid_events

def apply_effect(effect, stats):
    """应用事件效果到属性"""
    if not effect:
        return
    for stat, change in effect.items():
        if stat in stats:
            stats[stat] += change

def process_branch(branch, stats, past_events):
    """处理事件分支，返回应该触发的事件ID"""
    if not branch:
        return None
    for cond in branch:
        # 解析 "条件:事件ID" 格式
        parts = cond.split(':')
        if len(parts) == 2:
            condition, event_id = parts
            if check_condition(condition, stats, past_events):
                return int(event_id)
    return None

print("***********************************************")
print("*                                             *")
print("*     《人生重开模拟器》——Python版            *")
print("*                                             *")
print("***********************************************")

while True:
    print("请设置初始属性(可用共20)")
    CHR =  input("请输入颜值属性点数（0-10）：")
    while not (CHR.isdigit() or int(CHR) < 0 or int(CHR) > 10):
        CHR =  input("输入错误请重新输入：")
    CHR = int(CHR)

    STR =  input("请输入体质属性点数（0-10）：")
    while not (STR.isdigit() or int(STR) < 0 or int(STR) > 10):
        STR =  input("输入错误请重新输入：")
    STR = int(STR)

    INT =  input("请输入智力属性点数（0-10）：")
    while not (INT.isdigit() or int(INT) < 0 or int(INT) > 10):
        INT =  input("输入错误请重新输入：")
    INT = int(INT)

    MNY = 20 - CHR - STR - INT
    if MNY < 0:
        print("属性点数总和不能超过20")
        continue
    else:
        print("属性设置成功")
        # 打印各个属性
        print("颜值属性点数：" + str(CHR))
        print("体质属性点数：" + str(STR))
        print("智力属性点数：" + str(INT))
        print("家境点数：" + str(MNY))
        # 初始化属性追踪
        current_stats['CHR'] = CHR
        current_stats['STR'] = STR
        current_stats['INT'] = INT
        current_stats['MNY'] = MNY
        break
    

input("请任意键开始游戏：")

age = 0

while age < 100 and current_stats['LIF'] > 0:
    age_list = age_event_list.get(age, [])
    
    # 过滤满足条件的事件
    valid_events = filter_events_by_conditions(age_list, current_stats, past)
    
    if not valid_events:
        age += 1
        continue
    
    # 排除已发生过的事件，确保不重复
    remaining = [item for item in valid_events if int(str(item).split('*')[0]) not in past]
    
    if not remaining:
        past.clear()  # 清空已发生事件列表，重新开始
        remaining = valid_events
    
    # 从剩余事件中选择
    event_id = weight_choice(remaining)
    
    if event_id is None or event_id not in events:
        age += 1
        continue
    
    past[event_id] = age
    event_data = events[event_id]
    
    # 显示事件
    print(str(age) + "岁：" + event_data['event'])
    
    # 处理分支
    branch = event_data.get('branch')
    if branch:
        branch_event_id = process_branch(branch, current_stats, past)
        if branch_event_id and branch_event_id in events:
            branch_event = events[branch_event_id]
            print("  → " + branch_event['event'])
            past[branch_event_id] = age
            # 应用分支事件效果
            apply_effect(branch_event.get('effect'), current_stats)
    
    # 应用效果
    apply_effect(event_data.get('effect'), current_stats)
    
    age += 1
    time.sleep(1)


















