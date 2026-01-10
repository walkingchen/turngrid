/**
 * TurnGrid 游戏客户端
 * 负责游戏渲染、输入处理、网络同步
 */

// 游戏状态
const GameClient = {
    playerId: null,           // 当前玩家 ID
    nickname: '',             // 当前玩家昵称
    worldState: null,         // 世界状态
    clientRevision: 0,        // 客户端版本号
    canvas: null,             // Canvas 元素
    ctx: null,                // Canvas 绘图上下文
    cellSize: 25,             // 每个格子的像素大小
    updateInterval: null,     // 轮询定时器
    lastMoveTime: 0,          // 上次移动时间（用于显示冷却）
    moveCooldown: 300,        // 移动冷却时间（毫秒）
    longPressInterval: null,  // 长按定时器
    longPressDelay: 150,      // 长按重复间隔（毫秒）

    // 颜色配置
    colors: {
        grid: '#e0e0e0',
        player: '#667eea',
        currentPlayer: '#e74c3c',
        treasure: '#f1c40f',
        text: '#333'
    },

    // 初始化游戏
    init() {
        // 绑定加入按钮
        document.getElementById('join-button').addEventListener('click', () => this.joinGame());
        document.getElementById('nickname-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });

        // 绑定离开按钮
        document.getElementById('leave-button').addEventListener('click', () => this.leaveGame());

        // 绑定键盘事件
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));

        // 初始化虚拟控制器（触摸设备）
        this.initVirtualControls();
    },

    // 检测是否为触摸设备
    isTouchDevice() {
        return (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0));
    },

    // 初始化虚拟控制器
    initVirtualControls() {
        // 只在触摸设备上显示虚拟控制器
        if (!this.isTouchDevice()) {
            return;
        }

        const virtualControls = document.getElementById('virtual-controls');
        const dpadButtons = virtualControls.querySelectorAll('.dpad-btn');

        // 为每个方向按钮绑定触摸事件
        dpadButtons.forEach(button => {
            const direction = button.getAttribute('data-direction');

            // 触摸开始 - 立即移动一次，然后开始长按
            button.addEventListener('touchstart', (e) => {
                e.preventDefault(); // 防止触发点击事件和其他默认行为

                // 立即执行一次移动
                this.move(direction);

                // 清除之前的长按定时器（如果有）
                if (this.longPressInterval) {
                    clearInterval(this.longPressInterval);
                }

                // 启动长按定时器，持续移动
                this.longPressInterval = setInterval(() => {
                    this.move(direction);
                }, this.longPressDelay);
            });

            // 触摸结束 - 停止长按
            button.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.stopLongPress();
            });

            // 触摸取消 - 停止长按（手指移出按钮区域）
            button.addEventListener('touchcancel', (e) => {
                e.preventDefault();
                this.stopLongPress();
            });

            // 也保留 click 事件作为备选（某些设备可能需要）
            button.addEventListener('click', (e) => {
                e.preventDefault();
            });
        });

        // 显示虚拟控制器
        virtualControls.style.display = 'block';
    },

    // 停止长按
    stopLongPress() {
        if (this.longPressInterval) {
            clearInterval(this.longPressInterval);
            this.longPressInterval = null;
        }
    },

    // 加入游戏
    async joinGame() {
        const nicknameInput = document.getElementById('nickname-input');
        const nickname = nicknameInput.value.trim();

        if (!nickname) {
            alert('请输入昵称！');
            return;
        }

        try {
            // 发送加入请求
            const response = await fetch('/api/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nickname })
            });

            if (!response.ok) {
                const error = await response.json();
                alert(error.error || '加入失败');
                return;
            }

            const data = await response.json();
            this.playerId = data.player_id;
            this.nickname = nickname;

            // 切换到游戏界面
            document.getElementById('join-screen').style.display = 'none';
            document.getElementById('game-screen').style.display = 'block';
            document.getElementById('player-nickname').textContent = nickname;

            // 初始化 Canvas
            this.initCanvas();

            // 开始轮询更新
            this.startPolling();

            console.log('Joined game with ID:', this.playerId);
        } catch (error) {
            console.error('Join error:', error);
            alert('网络错误，请重试');
        }
    },

    // 离开游戏
    leaveGame() {
        // 停止轮询
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        // 停止长按
        this.stopLongPress();

        // 重置状态
        this.playerId = null;
        this.nickname = '';
        this.worldState = null;
        this.clientRevision = 0;

        // 切换回加入界面
        document.getElementById('game-screen').style.display = 'none';
        document.getElementById('join-screen').style.display = 'block';
        document.getElementById('nickname-input').value = '';
    },

    // 初始化 Canvas
    initCanvas() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');

        // 等待第一次获取世界状态后再设置 Canvas 尺寸
        // 暂时设置一个默认尺寸
        this.canvas.width = 20 * this.cellSize;
        this.canvas.height = 20 * this.cellSize;
    },

    // 调整 Canvas 尺寸
    resizeCanvas(width, height) {
        this.canvas.width = width * this.cellSize;
        this.canvas.height = height * this.cellSize;
    },

    // 开始轮询更新
    startPolling() {
        // 立即获取一次状态
        this.updateWorld();

        // 每500ms轮询一次
        this.updateInterval = setInterval(() => {
            this.updateWorld();
        }, 500);
    },

    // 更新世界状态
    async updateWorld() {
        try {
            const response = await fetch(
                `/api/world?player_id=${this.playerId}&revision=${this.clientRevision}`
            );

            if (!response.ok) {
                console.error('Failed to fetch world state');
                return;
            }

            const data = await response.json();

            // 如果服务器返回 unchanged，说明状态没有变化，不需要重绘
            if (data.unchanged) {
                return;
            }

            // 更新状态
            this.worldState = data;
            this.clientRevision = data.revision;

            // 第一次获取状态时调整 Canvas 尺寸
            if (this.canvas.width !== data.grid_width * this.cellSize) {
                this.resizeCanvas(data.grid_width, data.grid_height);
            }

            // 重绘游戏
            this.render();

            // 更新 UI
            this.updateUI();
        } catch (error) {
            console.error('Update error:', error);
        }
    },

    // 渲染游戏
    render() {
        if (!this.worldState) return;

        const { grid_width, grid_height, players, treasures } = this.worldState;

        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制网格
        this.drawGrid(grid_width, grid_height);

        // 绘制宝藏
        treasures.forEach(([x, y]) => {
            this.drawTreasure(x, y);
        });

        // 绘制玩家
        Object.entries(players).forEach(([id, player]) => {
            const isCurrentPlayer = id === this.playerId;
            this.drawPlayer(player.x, player.y, player.nickname, isCurrentPlayer);
        });
    },

    // 绘制网格
    drawGrid(width, height) {
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;

        // 绘制垂直线
        for (let x = 0; x <= width; x++) {
            this.ctx.beginPath();
            this.ctx.moveTo(x * this.cellSize, 0);
            this.ctx.lineTo(x * this.cellSize, height * this.cellSize);
            this.ctx.stroke();
        }

        // 绘制水平线
        for (let y = 0; y <= height; y++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y * this.cellSize);
            this.ctx.lineTo(width * this.cellSize, y * this.cellSize);
            this.ctx.stroke();
        }
    },

    // 绘制宝藏
    drawTreasure(x, y) {
        const centerX = x * this.cellSize + this.cellSize / 2;
        const centerY = y * this.cellSize + this.cellSize / 2;

        // 绘制一个钻石形状
        this.ctx.fillStyle = this.colors.treasure;
        this.ctx.strokeStyle = '#f39c12';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - 8);
        this.ctx.lineTo(centerX + 6, centerY);
        this.ctx.lineTo(centerX, centerY + 8);
        this.ctx.lineTo(centerX - 6, centerY);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
    },

    // 绘制玩家
    drawPlayer(x, y, nickname, isCurrentPlayer) {
        const centerX = x * this.cellSize + this.cellSize / 2;
        const centerY = y * this.cellSize + this.cellSize / 2;

        // 绘制圆形玩家
        this.ctx.fillStyle = isCurrentPlayer ? this.colors.currentPlayer : this.colors.player;
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;

        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, 10, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // 绘制昵称
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        this.ctx.fillText(nickname, centerX, centerY + 12);
    },

    // 更新 UI
    updateUI() {
        if (!this.worldState) return;

        const { players } = this.worldState;

        // 更新当前玩家分数
        if (players[this.playerId]) {
            document.getElementById('player-score').textContent = players[this.playerId].score;
        }

        // 更新在线玩家数
        document.getElementById('player-count').textContent = Object.keys(players).length;

        // 更新宝藏数
        document.getElementById('treasure-count').textContent = this.worldState.treasures.length;

        // 更新排行榜
        this.updateLeaderboard();
    },

    // 更新排行榜
    updateLeaderboard() {
        if (!this.worldState) return;

        const { players } = this.worldState;

        // 转换为数组并排序
        const leaderboard = Object.entries(players)
            .map(([id, player]) => ({
                id,
                nickname: player.nickname,
                score: player.score
            }))
            .sort((a, b) => b.score - a.score)
            .slice(0, 10); // 只显示前10名

        // 渲染排行榜
        const leaderboardList = document.getElementById('leaderboard-list');
        leaderboardList.innerHTML = '';

        leaderboard.forEach((player, index) => {
            const item = document.createElement('div');
            item.className = `leaderboard-item rank-${index + 1}`;

            const rank = index + 1;
            const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `${rank}.`;

            item.innerHTML = `
                <span class="player-name">${medal} ${player.nickname}</span>
                <span class="player-score">${player.score} 分</span>
            `;

            leaderboardList.appendChild(item);
        });
    },

    // 处理键盘按键
    handleKeyPress(e) {
        // 只在游戏界面时处理
        if (!this.playerId) return;

        // 获取方向
        let direction = null;
        switch (e.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                direction = 'up';
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                direction = 'down';
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                direction = 'left';
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                direction = 'right';
                break;
        }

        if (direction) {
            e.preventDefault(); // 阻止默认滚动行为
            this.move(direction);
        }
    },

    // 移动
    async move(direction) {
        // 检查冷却时间
        const now = Date.now();
        if (now - this.lastMoveTime < this.moveCooldown) {
            const remaining = ((this.moveCooldown - (now - this.lastMoveTime)) / 1000).toFixed(1);
            this.showMessage(`移动冷却中... ${remaining}秒`);
            return;
        }

        try {
            const response = await fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: this.playerId,
                    direction: direction
                })
            });

            const data = await response.json();

            if (response.ok) {
                // 移动成功，记录时间
                this.lastMoveTime = now;
                this.showMessage('', 'success');

                // 立即更新世界状态
                this.updateWorld();
            } else {
                // 移动失败，显示错误信息
                this.showMessage(data.message || '移动失败', 'error');
            }
        } catch (error) {
            console.error('Move error:', error);
            this.showMessage('网络错误', 'error');
        }
    },

    // 显示消息
    showMessage(text, type = 'error') {
        const messageEl = document.getElementById('message');
        messageEl.textContent = text;
        messageEl.style.color = type === 'error' ? '#e74c3c' : '#27ae60';

        // 3秒后清除消息
        if (text) {
            setTimeout(() => {
                if (messageEl.textContent === text) {
                    messageEl.textContent = '';
                }
            }, 3000);
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    GameClient.init();
});
