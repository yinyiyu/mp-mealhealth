"""
权限工具函数
提供角色权限校验装饰器，用于保护需要特定权限的接口
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from .models import User


def require_roles(*roles):
    """
    角色权限校验装饰器
    用法：@require_roles('admin', 'super_admin')
    只有拥有指定角色的用户才能访问被装饰的接口
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取当前登录用户ID（由JWT提供）
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user:
                return jsonify({'code': 401, 'message': '用户不存在'}), 401

            if not user.is_active:
                return jsonify({'code': 403, 'message': '账号已被禁用'}), 403

            # 检查角色权限
            if user.role not in roles:
                return jsonify({'code': 403, 'message': '权限不足，无法执行此操作'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """获取当前登录用户对象"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)
