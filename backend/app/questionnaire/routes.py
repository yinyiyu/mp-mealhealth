"""
问卷模板管理模块
提供问卷的增删改查、题目管理、上下架等功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models import QuestionnaireTemplate, Question
from ..utils import require_roles, get_current_user

questionnaire_bp = Blueprint('questionnaire', __name__)


@questionnaire_bp.route('/', methods=['GET'])
@jwt_required()
def list_questionnaires():
    """
    获取问卷模板列表
    支持按状态、分类筛选，支持分页
    查询参数：page=1&per_page=10&status=published&category=抑郁筛查
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')      # 按状态筛选
    category = request.args.get('category')  # 按分类筛选

    query = QuestionnaireTemplate.query

    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)

    # 分页查询
    pagination = query.order_by(QuestionnaireTemplate.created_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@questionnaire_bp.route('/<int:template_id>', methods=['GET'])
@jwt_required()
def get_questionnaire(template_id):
    """
    获取单个问卷模板详情（包含所有题目）
    """
    template = QuestionnaireTemplate.query.get_or_404(template_id)
    return jsonify({
        'code': 200,
        'data': template.to_dict(include_questions=True)
    })


@questionnaire_bp.route('/', methods=['POST'])
@jwt_required()
@require_roles('admin', 'super_admin')
def create_questionnaire():
    """
    创建问卷模板（仅管理员）
    请求体示例：
    {
        "title": "PHQ-9抑郁量表",
        "description": "用于筛查抑郁症状",
        "category": "抑郁筛查",
        "estimated_minutes": 5,
        "scoring_rules": {
            "总分": {
                "正常": "0-4",
                "轻度": "5-9",
                "中度": "10-19",
                "重度": "20-27"
            }
        },
        "dimensions": {
            "情绪症状": [1, 2, 3],
            "躯体症状": [4, 5, 6]
        },
        "questions": [
            {
                "content": "做事时提不起劲或没有兴趣",
                "question_type": "single_choice",
                "order_num": 1,
                "dimension": "情绪症状",
                "options": [
                    {"label": "A", "text": "完全不会", "score": 0},
                    {"label": "B", "text": "好几天", "score": 1},
                    {"label": "C", "text": "一半以上的天数", "score": 2},
                    {"label": "D", "text": "几乎每天", "score": 3}
                ]
            }
        ]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    if not data.get('title'):
        return jsonify({'code': 400, 'message': '问卷标题不能为空'}), 400

    current_user = get_current_user()

    # 创建问卷模板
    template = QuestionnaireTemplate(
        title=data['title'],
        description=data.get('description'),
        category=data.get('category'),
        scoring_rules=data.get('scoring_rules'),
        dimensions=data.get('dimensions'),
        estimated_minutes=data.get('estimated_minutes', 10),
        status='draft',  # 新建默认为草稿
        created_by=current_user.id
    )
    db.session.add(template)
    db.session.flush()  # 获取template.id

    # 批量创建题目
    questions_data = data.get('questions', [])
    for q_data in questions_data:
        if not q_data.get('content') or not q_data.get('options'):
            continue  # 跳过无效题目
        question = Question(
            template_id=template.id,
            content=q_data['content'],
            question_type=q_data.get('question_type', 'single_choice'),
            order_num=q_data.get('order_num', 0),
            dimension=q_data.get('dimension'),
            options=q_data['options'],
            is_required=q_data.get('is_required', True)
        )
        db.session.add(question)

    db.session.commit()
    return jsonify({
        'code': 200,
        'message': '问卷创建成功',
        'data': template.to_dict(include_questions=True)
    }), 201


@questionnaire_bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin')
def update_questionnaire(template_id):
    """
    更新问卷模板基本信息（仅管理员）
    注意：已发布的问卷不建议直接修改，建议先下架
    """
    template = QuestionnaireTemplate.query.get_or_404(template_id)
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    # 更新基本信息
    for field in ['title', 'description', 'category', 'scoring_rules',
                  'dimensions', 'estimated_minutes']:
        if field in data:
            setattr(template, field, data[field])

    db.session.commit()
    return jsonify({
        'code': 200,
        'message': '问卷更新成功',
        'data': template.to_dict()
    })


@questionnaire_bp.route('/<int:template_id>/status', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin')
def update_questionnaire_status(template_id):
    """
    更新问卷状态（上架/下架/归档）
    请求体：{"status": "published"} 或 {"status": "archived"}
    """
    template = QuestionnaireTemplate.query.get_or_404(template_id)
    data = request.get_json()

    new_status = data.get('status')
    allowed_statuses = ['draft', 'published', 'archived']
    if new_status not in allowed_statuses:
        return jsonify({'code': 400, 'message': f'状态值无效，允许的值：{allowed_statuses}'}), 400

    # 检查问卷是否有题目（发布前必须有题目）
    if new_status == 'published' and template.questions.count() == 0:
        return jsonify({'code': 400, 'message': '问卷没有题目，无法发布'}), 400

    template.status = new_status
    db.session.commit()
    return jsonify({'code': 200, 'message': '状态更新成功', 'data': {'status': new_status}})


@questionnaire_bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required()
@require_roles('super_admin')
def delete_questionnaire(template_id):
    """
    删除问卷模板（仅超级管理员，且只能删除草稿状态的问卷）
    """
    template = QuestionnaireTemplate.query.get_or_404(template_id)

    if template.status != 'draft':
        return jsonify({'code': 400, 'message': '只能删除草稿状态的问卷'}), 400

    # 先删除关联题目
    Question.query.filter_by(template_id=template_id).delete()
    db.session.delete(template)
    db.session.commit()
    return jsonify({'code': 200, 'message': '问卷删除成功'})


# ============ 题目管理接口 ============

@questionnaire_bp.route('/<int:template_id>/questions', methods=['POST'])
@jwt_required()
@require_roles('admin', 'super_admin')
def add_question(template_id):
    """
    向问卷添加题目
    请求体：{"content": "...", "question_type": "single_choice", "options": [...], "order_num": 1}
    """
    template = QuestionnaireTemplate.query.get_or_404(template_id)
    data = request.get_json()

    if not data.get('content'):
        return jsonify({'code': 400, 'message': '题目内容不能为空'}), 400
    if not data.get('options'):
        return jsonify({'code': 400, 'message': '题目选项不能为空'}), 400

    question = Question(
        template_id=template_id,
        content=data['content'],
        question_type=data.get('question_type', 'single_choice'),
        order_num=data.get('order_num', 0),
        dimension=data.get('dimension'),
        options=data['options'],
        is_required=data.get('is_required', True)
    )
    db.session.add(question)
    db.session.commit()
    return jsonify({'code': 200, 'message': '题目添加成功', 'data': question.to_dict()}), 201


@questionnaire_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin')
def update_question(question_id):
    """更新题目信息"""
    question = Question.query.get_or_404(question_id)
    data = request.get_json()

    for field in ['content', 'question_type', 'order_num', 'dimension', 'options', 'is_required']:
        if field in data:
            setattr(question, field, data[field])

    db.session.commit()
    return jsonify({'code': 200, 'message': '题目更新成功', 'data': question.to_dict()})


@questionnaire_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
@require_roles('admin', 'super_admin')
def delete_question(question_id):
    """删除题目"""
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    return jsonify({'code': 200, 'message': '题目删除成功'})
