"""
TurnGrid 游戏配置文件
所有配置参数都在这里定义，方便调整游戏规则
"""

# 地图配置
GRID_WIDTH = 20  # 地图宽度（格子数）
GRID_HEIGHT = 20  # 地图高度（格子数）

# 游戏规则配置
MOVE_COOLDOWN = 0.3  # 移动冷却时间（秒），防止玩家刷新移动
PLAYER_TIMEOUT = 300  # 玩家超时时间（秒），5分钟无操作则踢出
MAX_NICKNAME_LENGTH = 20  # 昵称最大长度

# 宝藏配置
TREASURE_COUNT = 5  # 地图上的宝藏数量
TREASURE_SCORE = 10  # 收集宝藏获得的分数

# 服务器配置
HOST = '0.0.0.0'  # 监听所有网络接口
PORT = 5000  # 服务端口
DEBUG = False  # 生产环境关闭调试模式

# 数据持久化配置
STATE_FILE = 'data/game_state.json'  # 游戏状态保存文件
AUTO_SAVE_INTERVAL = 60  # 自动保存间隔（秒）

# 管理员配置
ADMIN_TOKEN = 'your-secret-admin-token-here'  # 管理员令牌，用于重置游戏
