# 人生重开模拟器 - 属性系统实现计划

## 问题总结

当前属性（CHR/STR/INT/MNY）仅用于显示，没有实际游戏效果。需要实现：

1. 事件条件过滤（include/exclude）
2. 属性追踪和更新（effect）
3. 条件分支事件（branch）

## 当前代码分析

### 数据结构

* `events.json` 中每个事件包含：

  * `event`: 事件文本

  * `include`: 触发条件（如 "CHR>7", "MNY>4"）

  * `exclude`: 排除条件

  * `effect`: 属性变化（如 {"MNY": -1, "STR": 1}）

  * `branch`: 条件分支（如 \["INT>5:20008", "CHR>5:20007"]）

### 当前问题

1. `get_all_events()` 只存储 `temp[k]['event']`，丢失了其他字段
2. 游戏循环没有条件过滤逻辑
3. 没有属性追踪机制
4. 没有 effect 处理

## 实现方案

### 步骤1：修改 `get_all_events()` 存储完整事件数据

**文件**: `life_restart.py` 第13-23行

修改为存储完整事件对象，而不仅仅是文本：

```python
def get_all_events():
    if os.path.isfile(event_file):
        with open(event_file, "r", encoding="utf-8") as f:
            temp = json.load(f)
            for k in temp.keys():
                events_dict[int(k)] = temp[k]  # 存储完整事件对象
        return events_dict
```

### 步骤2：添加属性追踪变量

**文件**: `life_restart.py` 第60行附近

在 `past = {}` 后添加属性追踪：

```python
# 当前属性值（初始值来自用户输入）
current_stats = {
    'CHR': CHR,  # 颜值
    'STR': STR,  # 体质
    'INT': INT,  # 智力
    'MNY': MNY,  # 家境
    'SPR': 5,    # 精神（初始值5）
    'LIF': 100   # 生命（初始值100）
}
```

### 步骤3：实现条件解析函数

**文件**: `life_restart.py` 添加新函数

添加条件评估函数，解析 include/exclude 条件：

```python
def check_condition(condition, stats, past_events):
    """
    解析条件表达式，如 "CHR>7", "MNY>4", "EVT?[10009]"
    返回 True/False
    """
    if not condition:
        return True
    
    # 处理 AND (&) 和 OR (|) 逻辑
    # 处理属性比较: CHR>7, STR<3, MNY>=5 等
    # 处理事件检查: EVT?[10009,10010]
    # 处理天赋检查: TLT?[1001]
    pass
```

### 步骤4：实现事件过滤逻辑

**文件**: `life_restart.py` 修改 `weight_choice()` 或添加新函数

在选择事件前，过滤掉不满足条件的事件：

```python
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
```

### 步骤5：实现 effect 处理

**文件**: `life_restart.py` 添加新函数

事件发生后应用属性变化：

```python
def apply_effect(effect, stats):
    """应用事件效果到属性"""
    if not effect:
        return
    for stat, change in effect.items():
        if stat in stats:
            stats[stat] += change
```

### 步骤6：实现 branch 处理

**文件**: `life_restart.py` 添加新函数

处理条件分支事件：

```python
def process_branch(branch, stats):
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
```

### 步骤7：修改游戏主循环

**文件**: `life_restart.py` 第105-113行

整合所有新功能：

```python
while age < 100 and current_stats['LIF'] > 0:
    age_list = age_event_list.get(age, [])
    
    # 过滤满足条件的事件
    valid_events = filter_events_by_conditions(age_list, current_stats, past)
    
    if not valid_events:
        age += 1
        continue
    
    # 选择事件
    event_id = weight_choice(valid_events)
    while event_id in past and len(valid_events) > len(past):
        event_id = weight_choice(valid_events)
    
    past[event_id] = age
    event_data = events[event_id]
    
    # 显示事件
    print(str(age) + "岁：" + event_data['event'])
    
    # 处理分支
    branch = event_data.get('branch')
    if branch:
        branch_event_id = process_branch(branch, current_stats)
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
```

## 验证步骤

1. 运行程序，设置不同属性组合
2. 验证高颜值（CHR>7）触发特殊事件
3. 验证低家境（MNY<3）触发困难事件
4. 验证事件效果正确修改属性值
5. 验证条件分支正确触发

## 注意事项

* 条件解析需要支持：属性比较（>, <, >=, <=, ==, !=）、AND(&)、OR(|)、事件检查(EVT?)、天赋检查(TLT?)

* 属性值应该有合理范围（如生命<=0游戏结束）

* 需要处理事件ID不存在的情况

