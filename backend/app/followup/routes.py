"""
重点学生跟进模块
管理高风险学生的跟进记录（状态更新、备注记录）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models import FollowUp, User
from ..utils import require_roles, get_current_user

followup_bp = Blueprint('followup', __name__)


@followup_bp.route('/', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def list_followups():
    """
    获取跟进记录列表
    查询参数：status=pending&teacher_id=1&page=1&per_page=20
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')          # 按状态筛选
    teacher_id = request.args.get('teacher_id', type=int)

    current_user = get_current_user()
    query = FollowUp.query

    # 老师只能看自己负责的跟进记录
    if current_user.role == 'teacher':
        query = query.filter_by(teacher_id=current_user.id)
    elif teacher_id:
        query = query.filter_by(teacher_id=teacher_id)

    if status:
        query = query.filter_by(follow_status=status)

    pagination = query.order_by(FollowUp.updated_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [f.to_dict() for f in pagination.items],
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        }
    })


@followup_bp.route('/<int:followup_id>', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def get_followup(followup_id):
    """获取单条跟进记录详情"""
    followup = FollowUp.query.get_or_404(followup_id)
    return jsonify({'code': 200, 'data': followup.to_dict()})


@followup_bp.route('/', methods=['POST'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def create_followup():
    """
    手动创建跟进记录（针对特别关注的学生）
    请求体：{"student_id": 1, "report_id": 2, "notes": "需要重点关注"}
    """
    data = request.get_json()
    if not data or not data.get('student_id'):
        return jsonify({'code': 400, 'message': '学生ID不能为空'}), 400

    # 检查学生是否存在
    student = User.query.get(data['student_id'])
    if not student or student.role != 'student':
        return jsonify({'code': 404, 'message': '学生不存在'}), 404

    current_user = get_current_user()

    followup = FollowUp(
        student_id=data['student_id'],
        report_id=data.get('report_id'),
        teacher_id=data.get('teacher_id', current_user.id),
        follow_status='pending',
        notes=data.get('notes', '')
    )
    db.session.add(followup)
    db.session.commit()
    return jsonify({'code': 200, 'message': '跟进记录创建成功', 'data': followup.to_dict()}), 201


@followup_bp.route('/<int:followup_id>', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def update_followup(followup_id):
    """
    更新跟进记录（更新状态、追加备注、指派负责老师）
    请求体：{"follow_status": "in_progress", "notes": "已联系学生，安排本周面谈", "teacher_id": 2}

    跟进状态流转：
    pending（待沟通）-> in_progress（跟进中）-> closed（已结案）
    """
    followup = FollowUp.query.get_or_404(followup_id)
    current_user = get_current_user()

    # 老师只能修改自己负责的记录
    if current_user.role == 'teacher' and followup.teacher_id != current_user.id:
        return jsonify({'code': 403, 'message': '只能修改自己负责的跟进记录'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    # 更新状态
    if 'follow_status' in data:
        allowed_statuses = ['pending', 'in_progress', 'closed']
        if data['follow_status'] not in allowed_statuses:
            return jsonify({'code': 400, 'message': f'状态无效，允许：{allowed_statuses}'}), 400
        followup.follow_status = data['follow_status']

    # 追加备注（在原有备注后换行追加，保留历史记录）
    if 'notes' in data:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_note = f'[{timestamp} {current_user.name}] {data["notes"]}'
        if followup.notes:
            followup.notes = f'{followup.notes}\n{new_note}'
        else:
            followup.notes = new_note

    # 指派/更换负责老师（仅管理员可以指派）
    if 'teacher_id' in data and current_user.role in ('admin', 'super_admin'):
        teacher = User.query.get(data['teacher_id'])
        if not teacher or teacher.role not in ('teacher', 'admin'):
            return jsonify({'code': 400, 'message': '指派的老师不存在'}), 400
        followup.teacher_id = data['teacher_id']

    db.session.commit()
    return jsonify({'code': 200, 'message': '跟进记录更新成功', 'data': followup.to_dict()})
