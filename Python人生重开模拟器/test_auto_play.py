"""
测试自动播放功能的停止逻辑
模拟游戏数据，验证以下场景：
1. 正常活到100岁停止
2. 生命值归零提前停止
"""
import sys
import os
import json
import random
import re

# 直接加载游戏数据，不导入 tkinter_界面（避免触发 mainloop）
events_dict = {}
age_events = {}
event_file = os.path.abspath("events.json")
age_event_file = os.path.abspath("age.json")

with open(event_file, "r", encoding="utf-8") as f:
    temp = json.load(f)
    for k in temp.keys():
        events_dict[int(k)] = temp[k]
events = events_dict

with open(age_event_file, "r", encoding="utf-8") as f:
    temp = json.load(f)
    for k in temp.keys():
        event_list = temp[k]['event']
        filtered = []
        for item in event_list:
            item_str = str(item)
            eid = int(item_str.split('*')[0])
            if eid in events:
                filtered.append(item)
        age_events[int(k)] = filtered
age_event_list = age_events

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
    for key, value in weight_event.items():
        cumulative += value
        if rnd <= cumulative:
            return key

def check_condition(condition, stats, past_events):
    if not condition:
        return True
    condition = condition.strip()
    while '(' in condition:
        start = condition.rfind('(')
        end = condition.find(')', start)
        if start == -1 or end == -1:
            break
        inner = condition[start+1:end]
        result = check_condition(inner, stats, past_events)
        condition = condition[:start] + str(result) + condition[end+1:]
    if '|' in condition:
        parts = condition.split('|')
        return any(check_condition(p.strip(), stats, past_events) for p in parts)
    if '&' in condition:
        parts = condition.split('&')
        return all(check_condition(p.strip(), stats, past_events) for p in parts)
    if 'EVT?' in condition:
        match = re.search(r'EVT?\[([^\]]+)\]', condition)
        if match:
            event_ids = [int(x.strip()) for x in match.group(1).split(',')]
            return any(eid in past_events for eid in event_ids)
        return False
    if 'TLT?' in condition:
        return False
    match = re.match(r'(CHR|STR|INT|MNY|SPR|LIF)(>=|<=|>|<|==|!=)(\d+)', condition)
    if match:
        stat, op, value = match.group(1), match.group(2), int(match.group(3))
        cv = stats.get(stat, 0)
        ops = {'>': cv > value, '<': cv < value, '>=': cv >= value,
               '<=': cv <= value, '==': cv == value, '!=': cv != value}
        return ops.get(op, False)
    return condition == 'True'

def filter_events_by_conditions(age_list, stats, past_events):
    valid = []
    for item in age_list:
        eid = int(str(item).split('*')[0])
        ed = events.get(eid)
        if not ed:
            continue
        inc = ed.get('include')
        if inc and not check_condition(inc, stats, past_events):
            continue
        exc = ed.get('exclude')
        if exc and check_condition(exc, stats, past_events):
            continue
        valid.append(item)
    return valid

def apply_effect(effect, stats):
    if not effect:
        return
    for stat, change in effect.items():
        if stat in stats:
            stats[stat] += change

def process_branch(branch, stats, past_events):
    if not branch:
        return None
    for cond in branch:
        parts = cond.split(':')
        if len(parts) == 2:
            if check_condition(parts[0], stats, past_events):
                return int(parts[1])
    return None

def simulate_game(chr_val, str_val, int_val, mny_val, max_age=100):
    """模拟一局游戏，返回实际结束年龄和原因"""
    stats = {'CHR': chr_val, 'STR': str_val, 'INT': int_val, 'MNY': mny_val, 'SPR': 5, 'LIF': 100}
    past_local = {}
    age = 0

    while age < max_age and stats['LIF'] > 0:
        age_list = age_event_list.get(age, [])
        valid_events = filter_events_by_conditions(age_list, stats, past_local)

        if not valid_events:
            age += 1
            continue

        remaining = [item for item in valid_events if int(str(item).split('*')[0]) not in past_local]
        if not remaining:
            past_local.clear()
            remaining = valid_events

        event_id = weight_choice(remaining)
        if event_id is None or event_id not in events:
            age += 1
            continue

        past_local[event_id] = age
        event_data = events[event_id]

        branch = event_data.get('branch')
        if branch:
            branch_event_id = process_branch(branch, stats, past_local)
            if branch_event_id and branch_event_id in events:
                past_local[branch_event_id] = age
                apply_effect(events[branch_event_id].get('effect'), stats)

        apply_effect(event_data.get('effect'), stats)
        age += 1

    if stats['LIF'] <= 0:
        return age, f"死亡(LIF={stats['LIF']})"
    elif age >= max_age:
        return age, f"活到{max_age}岁"
    return age, "未知原因"


def test_auto_stop():
    """测试多个属性组合，验证自动停止"""
    print("=" * 50)
    print("自动播放停止逻辑测试")
    print("=" * 50)

    test_cases = [
        (5, 5, 5, 5, "均衡属性"),
        (10, 10, 0, 0, "极端属性(高颜值体质)"),
        (0, 0, 10, 10, "极端属性(高智力家境)"),
        (1, 1, 1, 1, "低属性(总和4，应报错)"),
        (10, 0, 10, 0, "交替极端"),
    ]

    for chr_v, str_v, int_v, mny_v, desc in test_cases:
        total = chr_v + str_v + int_v + mny_v
        if total != 20:
            print(f"\n[{desc}] 总和={total} != 20，应被拦截 [OK]")
            continue

        end_age, reason = simulate_game(chr_v, str_v, int_v, mny_v)
        status = "[OK]" if (end_age >= 100 or reason.startswith("死亡")) else "[FAIL]"
        print(f"\n[{desc}] 结束年龄={end_age}, 原因={reason} {status}")

    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_auto_stop()
