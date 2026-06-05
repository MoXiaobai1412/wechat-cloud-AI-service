import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from units.api import app
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    config_path = os.path.join(BASE_DIR, 'config', 'config.json')
    with(open(config_path, 'r')) as config_file:
        port = json.load(config_file)["port"]
    print("🚀 正在启动API")
    print(f"📍 Port: {port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    main()
