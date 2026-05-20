#!/bin/bash
# 基金监控系统启动脚本 - 修复Qt平台插件问题

# 清除错误的Qt平台设置，使用标准的XCB平台
export QT_QPA_PLATFORM="xcb"

# 设置Matplotlib缓存目录（解决之前的警告）
export MPLCONFIGDIR="/tmp/matplotlib_cache_$$"
mkdir -p "$MPLCONFIGDIR" 2>/dev/null || true

# 设置Qt插件路径（确保能找到platforms目录）
PYTHON_SITE_PACKAGES=$(python3 -c "import PySide6, os; print(os.path.dirname(PySide6.__file__))")
export QT_PLUGIN_PATH="${PYTHON_SITE_PACKAGES}/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="${QT_PLUGIN_PATH}/platforms"

echo "✅ Qt平台设置为: $QT_QPA_PLATFORM"
echo "✅ Qt插件路径: $QT_PLUGIN_PATH"
echo "🚀 正在启动基金监控系统..."
echo ""

# 启动程序
python3 main.py "$@"
