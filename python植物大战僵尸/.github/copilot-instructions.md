# Copilot Instructions for 植物大战僵尸 Codebase

## 项目架构与主要组件
- 本项目为《植物大战僵尸》简易复刻，核心逻辑集中在 `PVZ.py`，使用 Pygame 实现游戏主循环、渲染、事件处理。
- 资源（图片、字体、关卡数据）存放于 `garden/` 目录下，按类型细分（如 `bullet/`, `plant_animation/`, `zombie/`, `grass/`, `font/`）。
- 游戏启动时会加载 `garden/grass/garden.json`，根据关卡配置背景、卡牌、僵尸种类。
- 植物、僵尸、子弹等实体通过字典和列表进行管理，动画帧由图片序列实现。

## 关键开发流程
- **构建/运行**：直接运行 `PVZ.py` 即可启动游戏，无需额外构建步骤。依赖 Pygame、Numpy、Shapely。
- **调试**：主要通过修改 `PVZ.py`，可用 print 调试。按 `W` 键可切换僵尸血量显示。
- **资源扩展**：新增植物/僵尸需在 `garden/` 下添加图片，并在 `l_plants_loading_information` 或 `l_zombie_loading_information` 中注册。
- **关卡配置**：通过 `garden/grass/garden.json` 控制关卡内容。

## 项目约定与特殊模式
- 所有图片资源需放在对应子目录，命名需与实体注册名一致（如 `pea_shooter.png`、`普通僵尸-走路3.png`）。
- 字体文件需放在 `garden/font/`，主字体为 `font-1.ttf`。
- 英文输入法自动切换：启动时会尝试切换为英文输入法，相关逻辑见 `switch_to_english_input()`。
- 游戏窗口大小固定为 1200x650。
- 仅支持单关卡（level=1 或 2），如需扩展需修改关卡相关逻辑。

## 重要文件/目录
- `PVZ.py`：主游戏逻辑，事件循环，实体管理。
- `garden/grass/garden.json`：关卡配置。
- `garden/plant_animation/`、`garden/zombie/`、`garden/bullet/`：动画帧图片。
- `output/`：打包生成的可执行文件（如 `PVZ.exe`）。

## 示例：新增植物流程
1. 在 `garden/` 下添加植物图片（如 `pea_shooter.png` 和动画帧）。
2. 在 `l_plants_loading_information` 添加新植物及动画帧数。
3. 在 `plant_bullet`、`plant_firing_`、`plant_sun` 等字典注册属性。
4. 确认 `garden.json` 中关卡卡牌列表包含新植物。

---
如有不清楚或遗漏的部分，请反馈具体需求或问题场景，以便进一步完善说明。