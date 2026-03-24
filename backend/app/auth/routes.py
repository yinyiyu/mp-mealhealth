"""
认证模块路由
处理用户登录、微信小程序授权登录、Token刷新等
"""
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from .. import db
from ..models import User
from ..utils import get_current_user

auth_bp = Blueprint('auth', __name__)

# 微信小程序配置（实际部署时从环境变量读取）
WECHAT_APP_ID = 'your_wechat_app_id'
WECHAT_APP_SECRET = 'your_wechat_app_secret'


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    管理员/老师账号密码登录
    请求体：{"username": "admin", "password": "123456"}
    响应：{"code": 200, "data": {"access_token": "...", "user": {...}}}
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    # 查找用户
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    if not user.is_active:
        return jsonify({'code': 403, 'message': '账号已被禁用，请联系管理员'}), 403

    # 生成JWT Token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    })


@auth_bp.route('/wechat-login', methods=['POST'])
def wechat_login():
    """
    微信小程序登录接口
    前端通过 wx.login() 获取临时code，传给本接口换取用户信息和Token
    请求体：{"code": "wechat_temp_code", "user_info": {"nickName": "...", ...}}
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    code = data.get('code')
    if not code:
        return jsonify({'code': 400, 'message': '缺少微信授权code'}), 400

    # 调用微信接口获取openid
    # 实际项目中需要替换真实的AppID和AppSecret
    wx_api_url = (
        f'https://api.weixin.qq.com/sns/jscode2session'
        f'?appid={WECHAT_APP_ID}'
        f'&secret={WECHAT_APP_SECRET}'
        f'&js_code={code}'
        f'&grant_type=authorization_code'
    )

    try:
        wx_response = requests.get(wx_api_url, timeout=5).json()
    except Exception:
        return jsonify({'code': 500, 'message': '微信服务请求失败，请稍后重试'}), 500

    if 'errcode' in wx_response:
        return jsonify({
            'code': 400,
            'message': f'微信授权失败：{wx_response.get("errmsg", "未知错误")}'
        }), 400

    openid = wx_response.get('openid')
    if not openid:
        return jsonify({'code': 400, 'message': '获取微信用户信息失败'}), 400

    # 根据openid查找或创建用户
    user = User.query.filter_by(openid=openid).first()
    if not user:
        # 新用户，创建账号（初始为学生角色，可后续完善信息）
        user_info = data.get('user_info', {})
        user = User(
            username=f'wx_{openid[:16]}',  # 临时用户名
            role='student',
            name=user_info.get('nickName', '微信用户'),
            openid=openid
        )
        user.set_password(openid)  # 微信登录用户密码设为openid
        db.session.add(user)
        db.session.commit()

    if not user.is_active:
        return jsonify({'code': 403, 'message': '账号已被禁用'}), 403

    # 生成Token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'is_new_user': user.student_id is None  # 是否需要完善信息
        }
    })


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """刷新Token（使用refresh_token换取新的access_token）"""
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({
        'code': 200,
        'data': {'access_token': new_access_token}
    })


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前登录用户信息"""
    user = get_current_user()
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    return jsonify({'code': 200, 'data': user.to_dict()})


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    更新用户个人信息（学生完善学号、院系等信息）
    请求体：{"name": "张三", "student_id": "20210001", "department": "计算机学院", ...}
    """
    user = get_current_user()
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    # 允许更新的字段
    allowed_fields = ['name', 'student_id', 'department', 'grade', 'phone', 'email']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({'code': 200, 'message': '信息更新成功', 'data': user.to_dict()})
