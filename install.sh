#!/bin/bash
# TurnGrid 快速安装脚本
# 适用于 Raspberry Pi Zero W 和其他 Linux 系统

set -e  # 遇到错误立即退出

echo "========================================="
echo "  TurnGrid 游戏服务器安装脚本"
echo "========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then
    echo "警告：请不要使用 root 用户运行此脚本"
    echo "使用普通用户运行：./install.sh"
    exit 1
fi

# 获取当前目录
INSTALL_DIR=$(pwd)
echo "安装目录: $INSTALL_DIR"
echo ""

# 1. 检查 Python 3
echo "[1/6] 检查 Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python 3"
    echo "请先安装: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ 找到 $PYTHON_VERSION"
echo ""

# 2. 创建虚拟环境
echo "[2/6] 创建 Python 虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
fi
echo ""

# 3. 安装依赖
echo "[3/6] 安装 Python 依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ 依赖安装完成"
echo ""

# 4. 创建数据目录
echo "[4/6] 创建数据目录..."
mkdir -p data
echo "✓ 数据目录创建完成"
echo ""

# 5. 运行测试
echo "[5/6] 运行单元测试..."
python3 tests/test_game.py
echo "✓ 测试通过"
echo ""

# 6. 配置 systemd（可选）
echo "[6/6] 配置 systemd 服务（可选）"
read -p "是否配置 systemd 自启动服务？(y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 修改 systemd 文件中的路径
    TEMP_SERVICE=$(mktemp)
    sed "s|/home/pi/turngrid|$INSTALL_DIR|g" turngrid.service > "$TEMP_SERVICE"
    sed -i "s|User=pi|User=$USER|g" "$TEMP_SERVICE"

    # 安装服务
    sudo cp "$TEMP_SERVICE" /etc/systemd/system/turngrid.service
    rm "$TEMP_SERVICE"

    sudo systemctl daemon-reload
    sudo systemctl enable turngrid

    echo "✓ systemd 服务配置完成"
    echo ""
    echo "使用以下命令管理服务："
    echo "  启动服务: sudo systemctl start turngrid"
    echo "  停止服务: sudo systemctl stop turngrid"
    echo "  查看状态: sudo systemctl status turngrid"
    echo "  查看日志: sudo journalctl -u turngrid -f"
else
    echo "跳过 systemd 配置"
fi
echo ""

# 完成
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "下一步："
echo ""
echo "1. 修改配置文件（可选）："
echo "   nano config.py"
echo ""
echo "2. 启动游戏服务器："
echo "   方式一（直接运行）："
echo "     source venv/bin/activate"
echo "     python3 server.py"
echo ""
echo "   方式二（systemd 服务）："
echo "     sudo systemctl start turngrid"
echo ""
echo "3. 在浏览器中访问："
echo "   本地: http://localhost:5000"
echo "   局域网: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "祝你游戏愉快！🎮"
echo ""
