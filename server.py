"""
TurnGrid Flask 服务器
提供 RESTful API 和静态文件服务
"""

from flask import Flask, request, jsonify, send_from_directory
import uuid
import threading
import time
import config
from game_state import game


app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    """主页面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/join', methods=['POST'])
def join():
    """
    玩家加入游戏
    POST JSON: {"nickname": "玩家昵称"}
    返回: {"player_id": "...", "player": {...}}
    """
    data = request.get_json()

    if not data or 'nickname' not in data:
        return jsonify({'error': 'Nickname required'}), 400

    nickname = str(data['nickname']).strip()
    if not nickname:
        return jsonify({'error': 'Nickname cannot be empty'}), 400

    # 生成唯一玩家 ID
    player_id = str(uuid.uuid4())

    # 添加玩家到游戏
    player = game.add_player(player_id, nickname)

    return jsonify({
        'player_id': player_id,
        'player': player
    })


@app.route('/api/world', methods=['GET'])
def get_world():
    """
    获取世界状态
    GET 参数: player_id (可选，用于更新活跃时间)
              revision (可选，用于判断是否需要更新)
    返回: 完整的世界状态
    """
    player_id = request.args.get('player_id')
    client_revision = request.args.get('revision', type=int, default=0)

    # 如果提供了 player_id，更新玩家活跃时间
    if player_id:
        game.update_player_activity(player_id)

    # 获取世界状态
    world = game.get_world_state()

    # 如果客户端版本号与服务器一致，说明没有变化
    # 为了减少流量，可以返回一个简化的响应
    if client_revision == world['revision']:
        return jsonify({
            'revision': world['revision'],
            'unchanged': True
        })

    return jsonify(world)


@app.route('/api/move', methods=['POST'])
def move():
    """
    移动玩家
    POST JSON: {"player_id": "...", "direction": "up/down/left/right"}
    返回: {"success": bool, "message": str, "player": {...}}
    """
    data = request.get_json()

    if not data or 'player_id' not in data or 'direction' not in data:
        return jsonify({'error': 'player_id and direction required'}), 400

    player_id = data['player_id']
    direction = data['direction']

    # 验证方向
    if direction not in ['up', 'down', 'left', 'right']:
        return jsonify({'error': 'Invalid direction'}), 400

    # 移动玩家
    result = game.move_player(player_id, direction)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """
    开始游戏
    POST JSON: {"duration": 5}  # 游戏时长（分钟），1-10
    返回: {"success": bool, "message": str}
    """
    data = request.get_json()

    if not data or 'duration' not in data:
        return jsonify({'error': 'Duration required'}), 400

    duration = data['duration']

    # 验证时长范围
    if not isinstance(duration, int) or duration < 1 or duration > 10:
        return jsonify({'error': 'Duration must be between 1 and 10 minutes'}), 400

    # 开始游戏
    result = game.start_game(duration)

    return jsonify(result)


@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    """
    管理员重置游戏
    POST JSON: {"admin_token": "..."}
    """
    data = request.get_json()

    if not data or 'admin_token' not in data:
        return jsonify({'error': 'Admin token required'}), 401

    if data['admin_token'] != config.ADMIN_TOKEN:
        return jsonify({'error': 'Invalid admin token'}), 403

    # 重置游戏
    game.reset()

    return jsonify({'success': True, 'message': 'Game reset successfully'})


def cleanup_inactive_players():
    """
    后台线程：定期清理超时玩家
    """
    while True:
        time.sleep(30)  # 每30秒检查一次
        removed = game.remove_inactive_players()
        if removed > 0:
            print(f"Removed {removed} inactive players")


def auto_save():
    """
    后台线程：定期保存游戏状态
    """
    while True:
        time.sleep(config.AUTO_SAVE_INTERVAL)
        game.save_state()
        print("Game state saved")


if __name__ == '__main__':
    # 启动后台清理线程
    cleanup_thread = threading.Thread(target=cleanup_inactive_players, daemon=True)
    cleanup_thread.start()

    # 启动自动保存线程
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()

    print(f"Starting TurnGrid server on {config.HOST}:{config.PORT}")
    print(f"Grid size: {config.GRID_WIDTH}x{config.GRID_HEIGHT}")
    print(f"Move cooldown: {config.MOVE_COOLDOWN}s")

    # 启动 Flask 服务器
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
