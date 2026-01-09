"""
TurnGrid 单元测试
测试游戏核心规则：移动、碰撞检测、宝藏收集
"""

import unittest
import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_state import GameState
import config


class TestGameState(unittest.TestCase):
    """测试游戏状态管理"""

    def setUp(self):
        """每个测试前初始化游戏状态"""
        self.game = GameState()
        self.game.reset()

    def test_add_player(self):
        """测试添加玩家"""
        player = self.game.add_player('player1', 'Alice')

        # 检查玩家是否被添加
        self.assertIn('player1', self.game.players)
        self.assertEqual(player['nickname'], 'Alice')
        self.assertEqual(player['score'], 0)
        self.assertGreaterEqual(player['x'], 0)
        self.assertLess(player['x'], config.GRID_WIDTH)
        self.assertGreaterEqual(player['y'], 0)
        self.assertLess(player['y'], config.GRID_HEIGHT)

    def test_add_multiple_players(self):
        """测试添加多个玩家"""
        self.game.add_player('player1', 'Alice')
        self.game.add_player('player2', 'Bob')
        self.game.add_player('player3', 'Charlie')

        # 检查所有玩家都被添加
        self.assertEqual(len(self.game.players), 3)
        self.assertIn('player1', self.game.players)
        self.assertIn('player2', self.game.players)
        self.assertIn('player3', self.game.players)

    def test_nickname_length_limit(self):
        """测试昵称长度限制"""
        long_nickname = 'A' * 50  # 超长昵称
        player = self.game.add_player('player1', long_nickname)

        # 昵称应该被截断
        self.assertLessEqual(len(player['nickname']), config.MAX_NICKNAME_LENGTH)

    def test_move_player_valid(self):
        """测试有效移动"""
        # 添加玩家到固定位置
        self.game.add_player('player1', 'Alice')
        self.game.players['player1']['x'] = 10
        self.game.players['player1']['y'] = 10
        self.game.players['player1']['last_move_time'] = 0  # 重置冷却

        # 向上移动
        result = self.game.move_player('player1', 'up')
        self.assertTrue(result['success'])
        self.assertEqual(self.game.players['player1']['y'], 9)

        # 等待冷却
        import time
        time.sleep(config.MOVE_COOLDOWN + 0.1)

        # 向右移动
        result = self.game.move_player('player1', 'right')
        self.assertTrue(result['success'])
        self.assertEqual(self.game.players['player1']['x'], 11)

    def test_move_player_out_of_bounds(self):
        """测试移动超出边界"""
        self.game.add_player('player1', 'Alice')
        # 移动到左上角
        self.game.players['player1']['x'] = 0
        self.game.players['player1']['y'] = 0
        self.game.players['player1']['last_move_time'] = 0

        # 尝试向上移动（超出边界）
        result = self.game.move_player('player1', 'up')
        self.assertFalse(result['success'])
        self.assertIn('bounds', result['message'].lower())

        # 尝试向左移动（超出边界）
        result = self.game.move_player('player1', 'left')
        self.assertFalse(result['success'])

    def test_move_player_collision(self):
        """测试玩家碰撞检测"""
        # 添加两个玩家到相邻位置
        self.game.add_player('player1', 'Alice')
        self.game.add_player('player2', 'Bob')

        self.game.players['player1']['x'] = 10
        self.game.players['player1']['y'] = 10
        self.game.players['player2']['x'] = 11
        self.game.players['player2']['y'] = 10

        self.game.players['player1']['last_move_time'] = 0

        # 尝试让 player1 向右移动到 player2 的位置
        result = self.game.move_player('player1', 'right')
        self.assertFalse(result['success'])
        self.assertIn('collision', result['message'].lower())

    def test_move_cooldown(self):
        """测试移动冷却时间"""
        self.game.add_player('player1', 'Alice')
        self.game.players['player1']['x'] = 10
        self.game.players['player1']['y'] = 10

        # 第一次移动
        result = self.game.move_player('player1', 'up')
        self.assertTrue(result['success'])

        # 立即尝试第二次移动（应该失败）
        result = self.game.move_player('player1', 'down')
        self.assertFalse(result['success'])
        self.assertIn('cooldown', result['message'].lower())

    def test_treasure_collection(self):
        """测试宝藏收集"""
        self.game.add_player('player1', 'Alice')

        # 在玩家前面放置一个宝藏
        player_x = self.game.players['player1']['x']
        player_y = self.game.players['player1']['y']

        # 清空宝藏并在玩家上方放置一个
        self.game.treasures = [(player_x, player_y - 1)]
        initial_treasure_count = len(self.game.treasures)

        self.game.players['player1']['last_move_time'] = 0

        # 向上移动捡到宝藏
        result = self.game.move_player('player1', 'up')
        self.assertTrue(result['success'])

        # 检查分数增加
        self.assertEqual(self.game.players['player1']['score'], config.TREASURE_SCORE)

        # 检查宝藏被捡走并生成新宝藏
        self.assertEqual(len(self.game.treasures), initial_treasure_count)
        self.assertNotIn((player_x, player_y - 1), self.game.treasures)

    def test_revision_increment(self):
        """测试版本号递增"""
        initial_revision = self.game.revision

        # 添加玩家应该增加版本号
        self.game.add_player('player1', 'Alice')
        self.assertGreater(self.game.revision, initial_revision)

        rev_after_add = self.game.revision

        # 移动玩家应该增加版本号
        self.game.players['player1']['last_move_time'] = 0
        self.game.move_player('player1', 'up')
        self.assertGreater(self.game.revision, rev_after_add)

    def test_remove_inactive_players(self):
        """测试移除超时玩家"""
        import time

        # 添加玩家
        self.game.add_player('player1', 'Alice')

        # 手动设置玩家为超时状态
        self.game.players['player1']['last_active_time'] = time.time() - config.PLAYER_TIMEOUT - 1

        # 移除超时玩家
        removed_count = self.game.remove_inactive_players()

        # 检查玩家被移除
        self.assertEqual(removed_count, 1)
        self.assertNotIn('player1', self.game.players)

    def test_get_world_state(self):
        """测试获取世界状态"""
        self.game.add_player('player1', 'Alice')
        self.game.add_player('player2', 'Bob')

        world = self.game.get_world_state()

        # 检查世界状态包含必要字段
        self.assertIn('revision', world)
        self.assertIn('grid_width', world)
        self.assertIn('grid_height', world)
        self.assertIn('players', world)
        self.assertIn('treasures', world)

        # 检查玩家数量
        self.assertEqual(len(world['players']), 2)

    def test_reset_game(self):
        """测试重置游戏"""
        # 添加一些玩家
        self.game.add_player('player1', 'Alice')
        self.game.add_player('player2', 'Bob')

        # 重置游戏
        self.game.reset()

        # 检查所有玩家被清除
        self.assertEqual(len(self.game.players), 0)

        # 检查宝藏被重新生成
        self.assertEqual(len(self.game.treasures), config.TREASURE_COUNT)


class TestGameRules(unittest.TestCase):
    """测试游戏规则逻辑"""

    def test_treasures_initialized(self):
        """测试宝藏初始化"""
        game = GameState()
        game.reset()

        # 检查宝藏数量
        self.assertEqual(len(game.treasures), config.TREASURE_COUNT)

        # 检查宝藏位置在有效范围内
        for x, y in game.treasures:
            self.assertGreaterEqual(x, 0)
            self.assertLess(x, config.GRID_WIDTH)
            self.assertGreaterEqual(y, 0)
            self.assertLess(y, config.GRID_HEIGHT)

        # 检查宝藏位置不重复
        self.assertEqual(len(game.treasures), len(set(game.treasures)))

    def test_players_dont_spawn_on_treasures(self):
        """测试玩家不会生成在宝藏上"""
        game = GameState()
        game.reset()

        # 添加多个玩家
        for i in range(10):
            game.add_player(f'player{i}', f'Player{i}')

        # 检查没有玩家在宝藏位置上
        for player in game.players.values():
            player_pos = (player['x'], player['y'])
            self.assertNotIn(player_pos, game.treasures)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
