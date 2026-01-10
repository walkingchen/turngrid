"""
TurnGrid 游戏状态管理模块
负责管理玩家、地图、宝藏等游戏核心状态
使用线程锁保证并发安全
"""

import json
import os
import random
import time
import threading
from typing import Dict, List, Tuple, Optional
import config


class GameState:
    """
    游戏状态类
    管理所有玩家、宝藏、地图等游戏数据
    """

    def __init__(self):
        # 线程锁，保证并发访问安全
        self.lock = threading.Lock()

        # revision 版本号，每次状态变化时递增，用于客户端判断是否需要更新
        self.revision = 0

        # 玩家数据：{player_id: {x, y, nickname, score, last_move_time, last_active_time}}
        self.players: Dict[str, dict] = {}

        # 宝藏位置列表：[(x, y), (x, y), ...]
        self.treasures: List[Tuple[int, int]] = []

        # 初始化游戏地图
        self._init_game()

        # 尝试从文件加载之前的状态
        self._load_state()

    def _init_game(self):
        """
        初始化游戏：生成随机宝藏位置
        """
        self.treasures = []
        # 生成指定数量的宝藏，确保位置不重复
        positions = set()
        while len(positions) < config.TREASURE_COUNT:
            x = random.randint(0, config.GRID_WIDTH - 1)
            y = random.randint(0, config.GRID_HEIGHT - 1)
            positions.add((x, y))
        self.treasures = list(positions)

    def _increment_revision(self):
        """递增版本号"""
        self.revision += 1

    def add_player(self, player_id: str, nickname: str) -> dict:
        """
        添加新玩家到游戏
        返回玩家信息
        """
        with self.lock:
            # 如果玩家已存在，更新活跃时间并返回
            if player_id in self.players:
                self.players[player_id]['last_active_time'] = time.time()
                return self.players[player_id]

            # 找一个不与其他玩家和宝藏重叠的位置
            occupied = {(p['x'], p['y']) for p in self.players.values()}
            occupied.update(self.treasures)

            # 随机生成位置，直到找到空位
            while True:
                x = random.randint(0, config.GRID_WIDTH - 1)
                y = random.randint(0, config.GRID_HEIGHT - 1)
                if (x, y) not in occupied:
                    break

            # 限制昵称长度
            nickname = nickname[:config.MAX_NICKNAME_LENGTH]

            # 检查昵称是否重复，如果重复则添加编号
            nickname = self._make_unique_nickname(nickname)

            # 创建新玩家
            current_time = time.time()
            self.players[player_id] = {
                'x': x,
                'y': y,
                'nickname': nickname,
                'score': 0,
                'last_move_time': 0,  # 上次移动时间，用于冷却判断
                'last_active_time': current_time  # 上次活跃时间，用于超时判断
            }

            self._increment_revision()
            return self.players[player_id]

    def _make_unique_nickname(self, nickname: str) -> str:
        """
        确保昵称唯一，如果重复则添加编号
        例如：如果"玩家"已存在，则返回"玩家(2)"
        """
        # 获取所有现有昵称
        existing_nicknames = {p['nickname'] for p in self.players.values()}

        # 如果昵称不重复，直接返回
        if nickname not in existing_nicknames:
            return nickname

        # 如果重复，尝试添加编号
        counter = 2
        while True:
            new_nickname = f"{nickname}({counter})"
            if new_nickname not in existing_nicknames:
                return new_nickname
            counter += 1
            # 防止无限循环（理论上不会发生）
            if counter > 1000:
                return f"{nickname}({int(time.time())})"

    def move_player(self, player_id: str, direction: str) -> dict:
        """
        移动玩家
        direction: 'up', 'down', 'left', 'right'
        返回 {'success': bool, 'message': str, 'player': dict}
        """
        with self.lock:
            # 检查玩家是否存在
            if player_id not in self.players:
                return {'success': False, 'message': 'Player not found'}

            player = self.players[player_id]
            current_time = time.time()

            # 检查移动冷却时间（防刷）
            if current_time - player['last_move_time'] < config.MOVE_COOLDOWN:
                remaining = config.MOVE_COOLDOWN - (current_time - player['last_move_time'])
                return {
                    'success': False,
                    'message': f'Move cooldown: {remaining:.1f}s remaining'
                }

            # 计算新位置
            new_x, new_y = player['x'], player['y']
            if direction == 'up':
                new_y -= 1
            elif direction == 'down':
                new_y += 1
            elif direction == 'left':
                new_x -= 1
            elif direction == 'right':
                new_x += 1
            else:
                return {'success': False, 'message': 'Invalid direction'}

            # 检查是否超出地图边界
            if not (0 <= new_x < config.GRID_WIDTH and 0 <= new_y < config.GRID_HEIGHT):
                return {'success': False, 'message': 'Out of bounds'}

            # 检查是否与其他玩家碰撞
            for other_id, other in self.players.items():
                if other_id != player_id and other['x'] == new_x and other['y'] == new_y:
                    return {'success': False, 'message': 'Collision with another player'}

            # 移动玩家
            player['x'] = new_x
            player['y'] = new_y
            player['last_move_time'] = current_time
            player['last_active_time'] = current_time

            # 检查是否捡到宝藏
            if (new_x, new_y) in self.treasures:
                self.treasures.remove((new_x, new_y))
                player['score'] += config.TREASURE_SCORE
                # 生成新宝藏
                self._spawn_new_treasure()

            self._increment_revision()
            return {'success': True, 'message': 'Moved successfully', 'player': player}

    def _spawn_new_treasure(self):
        """
        生成一个新宝藏（当旧宝藏被捡走后）
        """
        # 获取所有被占用的位置
        occupied = {(p['x'], p['y']) for p in self.players.values()}
        occupied.update(self.treasures)

        # 如果地图已满，不生成新宝藏
        if len(occupied) >= config.GRID_WIDTH * config.GRID_HEIGHT:
            return

        # 随机生成位置
        while True:
            x = random.randint(0, config.GRID_WIDTH - 1)
            y = random.randint(0, config.GRID_HEIGHT - 1)
            if (x, y) not in occupied:
                self.treasures.append((x, y))
                break

    def update_player_activity(self, player_id: str):
        """更新玩家活跃时间（用于轮询时保持在线）"""
        with self.lock:
            if player_id in self.players:
                self.players[player_id]['last_active_time'] = time.time()

    def remove_inactive_players(self):
        """
        移除超时的玩家
        返回被移除的玩家数量
        """
        with self.lock:
            current_time = time.time()
            inactive = [
                pid for pid, p in self.players.items()
                if current_time - p['last_active_time'] > config.PLAYER_TIMEOUT
            ]

            for pid in inactive:
                del self.players[pid]

            if inactive:
                self._increment_revision()

            return len(inactive)

    def get_world_state(self) -> dict:
        """
        获取完整的世界状态（供客户端渲染）
        """
        with self.lock:
            return {
                'revision': self.revision,
                'grid_width': config.GRID_WIDTH,
                'grid_height': config.GRID_HEIGHT,
                'players': self.players.copy(),
                'treasures': self.treasures.copy()
            }

    def reset(self):
        """重置游戏（管理员功能）"""
        with self.lock:
            self.players.clear()
            self._init_game()
            self._increment_revision()

    def save_state(self):
        """将游戏状态保存到文件"""
        try:
            with self.lock:
                state = {
                    'revision': self.revision,
                    'players': self.players,
                    'treasures': self.treasures
                }

                # 确保 data 目录存在
                os.makedirs(os.path.dirname(config.STATE_FILE), exist_ok=True)

                # 保存到文件
                with open(config.STATE_FILE, 'w') as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def _load_state(self):
        """从文件加载游戏状态"""
        try:
            if os.path.exists(config.STATE_FILE):
                with open(config.STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.revision = state.get('revision', 0)
                    self.players = state.get('players', {})
                    self.treasures = [tuple(t) for t in state.get('treasures', [])]
                    print(f"Loaded game state: {len(self.players)} players, {len(self.treasures)} treasures")
        except Exception as e:
            print(f"Error loading state: {e}")


# 全局游戏状态实例
game = GameState()
