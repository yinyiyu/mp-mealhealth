"""
学生信息管理模块
提供学生的增删改查功能（仅管理员和超级管理员）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models import User
from ..utils import require_roles, get_current_user

student_bp = Blueprint('student', __name__)


@student_bp.route('/', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def list_students():
    """
    获取学生列表
    查询参数：page=1&per_page=20&keyword=张三&department=计算机学院&grade=2022
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()  # 姓名或学号模糊搜索
    department = request.args.get('department')
    grade = request.args.get('grade')

    query = User.query.filter_by(role='student')

    # 关键词搜索（姓名 或 学号）
    if keyword:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{keyword}%'),
                User.student_id.ilike(f'%{keyword}%')
            )
        )
    if department:
        query = query.filter_by(department=department)
    if grade:
        query = query.filter_by(grade=grade)

    pagination = query.order_by(User.created_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        }
    })


@student_bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def get_student(student_id):
    """获取指定学生详情"""
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'code': 400, 'message': '该用户不是学生'}), 400
    return jsonify({'code': 200, 'data': student.to_dict()})


@student_bp.route('/', methods=['POST'])
@jwt_required()
@require_roles('admin', 'super_admin')
def create_student():
    """
    新增学生账号（管理员手动创建，通常用于批量导入场景）
    请求体：{"username": "20210001", "name": "张三", "student_id": "20210001",
             "department": "计算机学院", "grade": "2021", "password": "初始密码"}
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    required_fields = ['username', 'name', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'code': 400, 'message': f'{field} 不能为空'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    # 检查学号是否已存在
    if data.get('student_id') and User.query.filter_by(student_id=data['student_id']).first():
        return jsonify({'code': 400, 'message': '学号已存在'}), 400

    student = User(
        username=data['username'],
        role='student',
        name=data['name'],
        student_id=data.get('student_id'),
        department=data.get('department'),
        grade=data.get('grade'),
        phone=data.get('phone'),
        email=data.get('email'),
        is_active=True
    )
    student.set_password(data['password'])

    db.session.add(student)
    db.session.commit()
    return jsonify({'code': 200, 'message': '学生账号创建成功', 'data': student.to_dict()}), 201


@student_bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin')
def update_student(student_id):
    """
    更新学生信息
    可更新：姓名、学号、院系、年级、手机、邮箱、是否启用
    """
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'code': 400, 'message': '只能修改学生账号'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    # 检查学号唯一性
    if 'student_id' in data and data['student_id'] != student.student_id:
        if User.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'code': 400, 'message': '学号已被占用'}), 400

    allowed_fields = ['name', 'student_id', 'department', 'grade', 'phone', 'email', 'is_active']
    for field in allowed_fields:
        if field in data:
            setattr(student, field, data[field])

    # 允许重置密码
    if data.get('new_password'):
        student.set_password(data['new_password'])

    db.session.commit()
    return jsonify({'code': 200, 'message': '学生信息更新成功', 'data': student.to_dict()})


@student_bp.route('/<int:student_id>', methods=['DELETE'])
@jwt_required()
@require_roles('super_admin')
def delete_student(student_id):
    """
    删除学生账号（仅超级管理员）
    注意：有答题记录的学生不允许删除，只能禁用
    """
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'code': 400, 'message': '只能删除学生账号'}), 400

    # 有答题记录的不允许删除
    if student.submissions.count() > 0:
        return jsonify({'code': 400, 'message': '该学生有答题记录，只能禁用账号'}), 400

    db.session.delete(student)
    db.session.commit()
    return jsonify({'code': 200, 'message': '学生账号已删除'})


# ============ 系统用户管理（老师/管理员账号） ============

@student_bp.route('/staff', methods=['GET'])
@jwt_required()
@require_roles('super_admin')
def list_staff():
    """获取所有老师和管理员账号列表（仅超级管理员）"""
    users = User.query.filter(User.role.in_(['teacher', 'admin', 'super_admin'])).all()
    return jsonify({'code': 200, 'data': [u.to_dict() for u in users]})


@student_bp.route('/staff', methods=['POST'])
@jwt_required()
@require_roles('super_admin')
def create_staff():
    """
    创建老师或管理员账号
    请求体：{"username": "teacher01", "name": "李老师", "role": "teacher", "password": "..."}
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    allowed_roles = ['teacher', 'admin', 'super_admin']
    if data.get('role') not in allowed_roles:
        return jsonify({'code': 400, 'message': f'角色无效，允许：{allowed_roles}'}), 400

    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    user = User(
        username=data['username'],
        role=data['role'],
        name=data['name'],
        department=data.get('department'),
        phone=data.get('phone'),
        email=data.get('email'),
        is_active=True
    )
    user.set_password(data.get('password', '123456'))
    db.session.add(user)
    db.session.commit()
    return jsonify({'code': 200, 'message': '账号创建成功', 'data': user.to_dict()}), 201
