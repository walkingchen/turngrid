# 🎮 TurnGrid

一个可在 Raspberry Pi Zero W 上运行的多用户联机回合制网页游戏。

## 📋 项目简介

TurnGrid 是一个轻量级的多人在线回合制游戏，专为 Raspberry Pi Zero W 等低配置设备设计。玩家通过浏览器加入游戏，使用方向键在 20×20 的地图上移动，收集宝藏，与其他玩家竞争分数。

### ✨ 核心特性

- 🌐 **纯网页游戏**：无需安装客户端，浏览器即可玩
- 👥 **多人在线**：支持多个玩家同时游戏
- 🎯 **回合制机制**：每次移动有冷却时间（300ms），防止刷新
- 💎 **宝藏收集**：地图上随机分布宝藏，收集获得分数
- 🏆 **实时排行榜**：显示所有玩家的分数排名
- 🔒 **状态安全**：使用线程锁和版本号机制保证并发安全
- 💾 **自动保存**：定期保存游戏状态到 JSON 文件
- ⏱️ **自动剔除**：超时无活动的玩家自动移除
- 🚀 **systemd 自启**：支持开机自动启动服务

### 🎨 技术栈

- **后端**：Python 3 + Flask
- **前端**：原生 HTML5 + Canvas + JavaScript
- **状态同步**：轮询机制（500ms 一次）
- **数据持久化**：JSON 文件（无需数据库）

## 📁 项目结构

```
turngrid/
├── README.md                 # 项目文档
├── requirements.txt          # Python 依赖
├── config.py                 # 配置文件
├── game_state.py             # 游戏状态管理
├── server.py                 # Flask 服务器
├── static/                   # 前端文件
│   ├── index.html           # 游戏页面
│   ├── game.js              # 游戏客户端逻辑
│   └── style.css            # 样式表
├── tests/                    # 单元测试
│   └── test_game.py         # 游戏逻辑测试
├── data/                     # 数据目录
│   └── game_state.json      # 游戏状态持久化
├── turngrid.service          # systemd 服务文件
└── .gitignore
```

## 🚀 快速开始

### 系统要求

- Raspberry Pi Zero W（或任何 Linux 系统）
- Python 3.7+
- 至少 100MB 可用内存
- 网络连接

### 1. 克隆项目

```bash
cd ~
git clone <your-repo-url> turngrid
cd turngrid
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 运行游戏

#### 方式一：直接运行（开发/测试）

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行服务器
python3 server.py
```

服务器启动后，在浏览器中访问：
- **本地访问**：`http://localhost:5000`
- **局域网访问**：`http://<树莓派IP>:5000`

#### 方式二：使用 systemd 自启（生产环境）

```bash
# 修改 systemd 服务文件中的路径（如果不是 /home/pi/turngrid）
sudo nano turngrid.service

# 复制服务文件
sudo cp turngrid.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start turngrid

# 查看服务状态
sudo systemctl status turngrid

# 设置开机自启
sudo systemctl enable turngrid

# 查看日志
sudo journalctl -u turngrid -f
```

## ⚙️ 配置说明

编辑 `config.py` 文件可以自定义游戏参数：

```python
# 地图配置
GRID_WIDTH = 20              # 地图宽度
GRID_HEIGHT = 20             # 地图高度

# 游戏规则
MOVE_COOLDOWN = 0.3          # 移动冷却时间（秒）
PLAYER_TIMEOUT = 300         # 玩家超时时间（秒）
MAX_NICKNAME_LENGTH = 20     # 昵称最大长度

# 宝藏配置
TREASURE_COUNT = 5           # 地图上的宝藏数量
TREASURE_SCORE = 10          # 每个宝藏的分数

# 服务器配置
HOST = '0.0.0.0'             # 监听地址
PORT = 5000                  # 服务端口
DEBUG = False                # 调试模式

# 管理员配置
ADMIN_TOKEN = 'your-secret-admin-token-here'  # 管理员令牌
```

**重要**：修改配置后需要重启服务：

```bash
sudo systemctl restart turngrid
```

## 🎮 游戏玩法

### 如何开始

1. 在浏览器中打开游戏地址
2. 输入你的昵称
3. 点击"加入游戏"按钮

### 游戏规则

- **移动**：使用键盘方向键 ↑↓←→ 或 WASD 控制你的角色
- **收集宝藏**：移动到宝藏位置（黄色钻石）自动收集，获得 10 分
- **碰撞**：不能移动到其他玩家所在的位置
- **边界**：不能移动出地图边界
- **冷却**：每次移动后有 300ms 冷却时间
- **超时**：5 分钟无操作会被自动剔除

### 游戏界面

- **左上角**：显示你的昵称和分数
- **右上角**：显示在线玩家数和地图上的宝藏数
- **中间画布**：游戏地图
  - 红色圆圈：你的角色
  - 紫色圆圈：其他玩家
  - 黄色钻石：宝藏
- **下方排行榜**：显示所有玩家的分数排名

## 🔌 API 文档

### 1. 加入游戏

```http
POST /api/join
Content-Type: application/json

{
  "nickname": "玩家昵称"
}
```

**响应**：
```json
{
  "player_id": "uuid",
  "player": {
    "x": 10,
    "y": 15,
    "nickname": "玩家昵称",
    "score": 0,
    "last_move_time": 1234567890,
    "last_active_time": 1234567890
  }
}
```

### 2. 获取世界状态

```http
GET /api/world?player_id=<uuid>&revision=<number>
```

**响应**：
```json
{
  "revision": 123,
  "grid_width": 20,
  "grid_height": 20,
  "players": {
    "uuid1": {
      "x": 10,
      "y": 15,
      "nickname": "玩家1",
      "score": 30,
      "last_move_time": 1234567890,
      "last_active_time": 1234567890
    }
  },
  "treasures": [[5, 8], [12, 3], [18, 19]]
}
```

### 3. 移动玩家

```http
POST /api/move
Content-Type: application/json

{
  "player_id": "uuid",
  "direction": "up"  // up, down, left, right
}
```

**响应**：
```json
{
  "success": true,
  "message": "Moved successfully",
  "player": { ... }
}
```

### 4. 管理员重置游戏

```http
POST /api/admin/reset
Content-Type: application/json

{
  "admin_token": "your-secret-admin-token-here"
}
```

**响应**：
```json
{
  "success": true,
  "message": "Game reset successfully"
}
```

## 🧪 运行测试

项目包含单元测试，测试游戏核心逻辑：

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行所有测试
python3 -m pytest tests/

# 或使用 unittest
python3 tests/test_game.py

# 运行测试并显示详细信息
python3 tests/test_game.py -v
```

测试内容包括：
- 玩家添加和管理
- 移动逻辑和边界检测
- 碰撞检测
- 宝藏收集
- 冷却时间机制
- 超时玩家移除
- 版本号递增

## 🔧 常见问题

### 1. 无法访问游戏页面

**症状**：浏览器无法打开 `http://<树莓派IP>:5000`

**解决方案**：
```bash
# 检查服务是否运行
sudo systemctl status turngrid

# 检查端口是否被占用
sudo netstat -tulpn | grep 5000

# 检查防火墙
sudo ufw status
sudo ufw allow 5000/tcp  # 如果需要

# 查看日志
sudo journalctl -u turngrid -n 50
```

### 2. 游戏运行缓慢

**可能原因**：
- Raspberry Pi Zero W 性能有限
- 太多玩家同时在线

**优化方案**：
```python
# 在 config.py 中调整参数
MOVE_COOLDOWN = 0.5      # 增加冷却时间
GRID_WIDTH = 15          # 减小地图尺寸
GRID_HEIGHT = 15
TREASURE_COUNT = 3       # 减少宝藏数量
```

### 3. 玩家经常被踢出

**原因**：超时时间太短

**解决方案**：
```python
# 在 config.py 中增加超时时间
PLAYER_TIMEOUT = 600  # 10 分钟
```

### 4. 服务器崩溃或自动重启

**诊断**：
```bash
# 查看崩溃日志
sudo journalctl -u turngrid -n 100

# 查看内存使用
free -h

# 查看 Python 进程
ps aux | grep python
```

**常见原因**：
- 内存不足：减少地图大小或限制玩家数量
- Python 错误：检查日志中的错误堆栈

### 5. 状态文件损坏

**症状**：服务器启动后无法加载之前的状态

**解决方案**：
```bash
# 删除损坏的状态文件
rm ~/turngrid/data/game_state.json

# 重启服务
sudo systemctl restart turngrid
```

### 6. 修改配置后不生效

**解决方案**：
```bash
# 必须重启服务才能加载新配置
sudo systemctl restart turngrid

# 确认服务正常运行
sudo systemctl status turngrid
```

### 7. 获取树莓派 IP 地址

```bash
# 查看本机 IP
hostname -I

# 或使用
ip addr show
```

### 8. 局域网其他设备无法访问

**检查清单**：
1. 确认树莓派和其他设备在同一局域网
2. 确认 `config.py` 中 `HOST = '0.0.0.0'`
3. 检查防火墙设置
4. 尝试 ping 树莓派 IP
5. 确认端口 5000 没有被其他程序占用

## 📊 性能优化建议

### Raspberry Pi Zero W 优化

1. **减少地图尺寸**：15×15 比 20×20 性能更好
2. **增加冷却时间**：降低服务器压力
3. **限制玩家数量**：可以在代码中添加最大玩家数限制
4. **使用轻量级系统**：Raspberry Pi OS Lite（无桌面）

### 网络优化

1. **客户端缓存**：浏览器会自动缓存静态文件
2. **版本号机制**：已实现，减少不必要的数据传输
3. **轮询间隔**：可以在 `game.js` 中调整为 1000ms

### 代码优化

```python
# 在 game_state.py 中可以添加最大玩家数限制
MAX_PLAYERS = 20

def add_player(self, player_id, nickname):
    with self.lock:
        if len(self.players) >= MAX_PLAYERS:
            return {'error': 'Server is full'}
        # ... 其余代码
```

## 🛡️ 安全建议

1. **修改管理员令牌**：
   ```python
   # 在 config.py 中设置强密码
   ADMIN_TOKEN = 'your-very-strong-secret-token-here'
   ```

2. **防火墙配置**：
   ```bash
   # 只允许局域网访问
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

3. **昵称过滤**：当前已限制长度，可以添加更多验证

4. **速率限制**：移动冷却时间已实现基础防刷

## 📝 开发说明

### 添加新功能

1. **修改游戏规则**：编辑 `game_state.py`
2. **添加 API 端点**：编辑 `server.py`
3. **修改前端界面**：编辑 `static/` 目录下的文件
4. **添加测试**：编辑 `tests/test_game.py`

### 代码风格

- 关键规则处有中文注释
- 函数和类有文档字符串
- 代码可读性面向儿童可理解

### 贡献代码

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 发起 Pull Request

## 📜 许可证

MIT License

## 🙏 致谢

- Flask 框架
- HTML5 Canvas API
- Raspberry Pi 社区

---

**享受游戏！Have Fun! 🎮**

如有问题或建议，欢迎提出 Issue 或 Pull Request。
