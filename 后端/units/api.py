import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chain import Chain
from flask import Flask, request, jsonify, send_from_directory
import asyncio

app = Flask(__name__)

def success_response(data=None, message='success'):
    return jsonify({'code': 0, 'data': data, 'message': message})

def error_response(message='error', code=1, http_status=400):
    return jsonify({'code': code, 'message': message}), http_status



@app.route('/api/connect', methods=['POST'])
def connect():
    try:
        data = request.get_json()
        if not data:
            return error_response('请求数据为空', code=400, http_status=400)
        openid = data.get('openid', '')
        content = data.get('content', '')
        if not openid or not content:
            return error_response('请求数据不全', code=409, http_status=409)

        # 关键修改：使用 asyncio.run() 执行异步函数
        chain = Chain()
        response = asyncio.run(chain.replyCustomersChain(session_id=openid, content=content))
        return success_response(data={'response': response})

    except Exception as e:
        app.logger.error(f'处理请求失败: {e}', exc_info=True)
        return error_response('内部错误', code=500, http_status=500)