"""
测评任务模块
处理测评发布、学生答题、答案提交等核心业务逻辑
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models import Assessment, QuestionnaireTemplate, AnswerSubmission, AssessmentReport, User
from ..utils import require_roles, get_current_user
from ..report.service import generate_report

assessment_bp = Blueprint('assessment', __name__)


@assessment_bp.route('/', methods=['GET'])
@jwt_required()
def list_assessments():
    """
    获取测评列表
    - 学生：只看到正在进行中的、面向自己的测评
    - 管理员/老师：可以看到所有测评
    查询参数：page=1&per_page=10&status=ongoing
    """
    current_user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')

    query = Assessment.query

    # 学生只能看到进行中的测评
    if current_user.role == 'student':
        now = datetime.utcnow()
        query = query.filter_by(status='ongoing')
        # 检查测评时间是否在有效范围
        query = query.filter(
            db.or_(Assessment.start_time == None, Assessment.start_time <= now)
        ).filter(
            db.or_(Assessment.end_time == None, Assessment.end_time >= now)
        )
    elif status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Assessment.created_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    # 如果是学生，同时返回已完成的测评ID列表（用于前端标记哪些已完成）
    completed_ids = []
    if current_user.role == 'student':
        completed_submissions = AnswerSubmission.query.filter_by(
            student_id=current_user.id,
            submit_status='submitted'
        ).with_entities(AnswerSubmission.assessment_id).all()
        completed_ids = [s.assessment_id for s in completed_submissions]

    return jsonify({
        'code': 200,
        'data': {
            'items': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages,
            'completed_ids': completed_ids  # 已完成的测评ID
        }
    })


@assessment_bp.route('/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment(assessment_id):
    """获取测评详情"""
    assessment = Assessment.query.get_or_404(assessment_id)
    data = assessment.to_dict()
    # 包含问卷题目（供答题用）
    if assessment.template:
        data['template'] = assessment.template.to_dict(include_questions=True)
    return jsonify({'code': 200, 'data': data})


@assessment_bp.route('/', methods=['POST'])
@jwt_required()
@require_roles('admin', 'super_admin')
def create_assessment():
    """
    发布测评任务（仅管理员）
    请求体示例：
    {
        "title": "2024年春季心理健康测评",
        "template_id": 1,
        "target_config": {"type": "all"},
        "start_time": "2024-03-01T08:00:00",
        "end_time": "2024-03-31T23:59:59",
        "max_duration_minutes": 30
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求数据格式错误'}), 400

    if not data.get('title') or not data.get('template_id'):
        return jsonify({'code': 400, 'message': '测评标题和问卷模板不能为空'}), 400

    # 检查问卷模板是否存在且已发布
    template = QuestionnaireTemplate.query.get(data['template_id'])
    if not template:
        return jsonify({'code': 404, 'message': '问卷模板不存在'}), 404
    if template.status != 'published':
        return jsonify({'code': 400, 'message': '只能使用已发布的问卷模板'}), 400

    current_user = get_current_user()

    # 解析时间字段
    start_time = None
    end_time = None
    if data.get('start_time'):
        try:
            start_time = datetime.fromisoformat(data['start_time'])
        except ValueError:
            return jsonify({'code': 400, 'message': '开始时间格式错误，请使用ISO格式'}), 400
    if data.get('end_time'):
        try:
            end_time = datetime.fromisoformat(data['end_time'])
        except ValueError:
            return jsonify({'code': 400, 'message': '结束时间格式错误，请使用ISO格式'}), 400

    assessment = Assessment(
        title=data['title'],
        template_id=data['template_id'],
        target_config=data.get('target_config', {'type': 'all'}),
        start_time=start_time,
        end_time=end_time,
        max_duration_minutes=data.get('max_duration_minutes'),
        status='draft',
        created_by=current_user.id
    )
    db.session.add(assessment)
    db.session.commit()
    return jsonify({'code': 200, 'message': '测评创建成功', 'data': assessment.to_dict()}), 201


@assessment_bp.route('/<int:assessment_id>/status', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'super_admin')
def update_assessment_status(assessment_id):
    """
    更新测评状态（发布/结束）
    请求体：{"status": "ongoing"} 发布测评
           {"status": "ended"}   结束测评
    """
    assessment = Assessment.query.get_or_404(assessment_id)
    data = request.get_json()
    new_status = data.get('status')

    allowed = ['draft', 'ongoing', 'ended', 'archived']
    if new_status not in allowed:
        return jsonify({'code': 400, 'message': f'状态无效，允许：{allowed}'}), 400

    assessment.status = new_status
    db.session.commit()
    return jsonify({'code': 200, 'message': '状态更新成功', 'data': assessment.to_dict()})


# ============ 答题接口（学生端） ============

@assessment_bp.route('/<int:assessment_id>/start', methods=['POST'])
@jwt_required()
def start_assessment(assessment_id):
    """
    学生开始答题
    - 创建答题记录，记录开始时间
    - 检查学生是否已经提交过该测评
    """
    current_user = get_current_user()

    # 只有学生才能答题
    if current_user.role not in ('student',):
        return jsonify({'code': 403, 'message': '只有学生才能参与测评'}), 403

    assessment = Assessment.query.get_or_404(assessment_id)

    # 检查测评是否进行中
    if not assessment.is_active():
        return jsonify({'code': 400, 'message': '测评未开始或已结束'}), 400

    # 检查是否已提交过
    existing = AnswerSubmission.query.filter_by(
        assessment_id=assessment_id,
        student_id=current_user.id,
        submit_status='submitted'
    ).first()
    if existing:
        return jsonify({'code': 400, 'message': '您已经完成了该测评，不能重复提交'}), 400

    # 检查是否有未完成的答题记录（继续作答）
    in_progress = AnswerSubmission.query.filter_by(
        assessment_id=assessment_id,
        student_id=current_user.id,
        submit_status='in_progress'
    ).first()

    if in_progress:
        # 检查是否超时
        if assessment.max_duration_minutes and in_progress.started_at:
            elapsed = (datetime.utcnow() - in_progress.started_at).total_seconds() / 60
            if elapsed > assessment.max_duration_minutes:
                return jsonify({'code': 400, 'message': '答题时间已超时，请重新参加测评'}), 400
        return jsonify({
            'code': 200,
            'message': '继续作答',
            'data': {
                'submission_id': in_progress.id,
                'started_at': in_progress.started_at.isoformat(),
                'answers_data': in_progress.answers_data or {}
            }
        })

    # 创建新的答题记录
    submission = AnswerSubmission(
        assessment_id=assessment_id,
        student_id=current_user.id,
        started_at=datetime.utcnow(),
        submit_status='in_progress',
        answers_data={},
        ip_address=request.remote_addr
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '开始答题',
        'data': {
            'submission_id': submission.id,
            'started_at': submission.started_at.isoformat(),
            'max_duration_minutes': assessment.max_duration_minutes
        }
    })


@assessment_bp.route('/submissions/<int:submission_id>/save', methods=['PUT'])
@jwt_required()
def save_progress(submission_id):
    """
    暂存答题进度（学生可多次调用，最终提交前保存进度）
    请求体：{"answers": {"1": "A", "2": ["A", "C"]}}  题目ID -> 选项
    """
    current_user = get_current_user()
    submission = AnswerSubmission.query.get_or_404(submission_id)

    # 验证是本人的答题记录
    if submission.student_id != current_user.id:
        return jsonify({'code': 403, 'message': '无权操作'}), 403

    if submission.submit_status != 'in_progress':
        return jsonify({'code': 400, 'message': '该答题记录已提交，无法修改'}), 400

    data = request.get_json()
    submission.answers_data = data.get('answers', {})
    db.session.commit()
    return jsonify({'code': 200, 'message': '进度已保存'})


@assessment_bp.route('/submissions/<int:submission_id>/submit', methods=['POST'])
@jwt_required()
def submit_assessment(submission_id):
    """
    提交答题（最终提交）
    系统自动计算得分、生成测评报告
    请求体：{"answers": {"1": "A", "2": "B", ...}}
    """
    current_user = get_current_user()
    submission = AnswerSubmission.query.get_or_404(submission_id)

    # 验证是本人的记录
    if submission.student_id != current_user.id:
        return jsonify({'code': 403, 'message': '无权操作'}), 403

    if submission.submit_status == 'submitted':
        return jsonify({'code': 400, 'message': '该测评已提交，不能重复提交'}), 400

    data = request.get_json()
    answers = data.get('answers', {})

    # 校验答题时长（防止作弊，过快提交视为无效）
    assessment = submission.assessment
    if submission.started_at:
        duration_seconds = (datetime.utcnow() - submission.started_at).total_seconds()

        # 超时处理
        if assessment.max_duration_minutes:
            max_seconds = assessment.max_duration_minutes * 60
            if duration_seconds > max_seconds + 60:  # 允许60秒网络延迟
                submission.submit_status = 'timeout'
                submission.submitted_at = datetime.utcnow()
                db.session.commit()
                return jsonify({'code': 400, 'message': '答题超时，本次提交无效'}), 400

    # 更新答题记录
    submission.answers_data = answers
    submission.submit_status = 'submitted'
    submission.submitted_at = datetime.utcnow()
    db.session.commit()

    # 自动生成测评报告（计算得分、判定风险等级）
    report = generate_report(submission)

    return jsonify({
        'code': 200,
        'message': '提交成功',
        'data': {
            'report_id': report.id,
            'total_score': report.total_score,
            'risk_level': report.risk_level,
            'risk_level_text': _get_risk_level_text(report.risk_level)
        }
    })


def _get_risk_level_text(risk_level):
    """风险等级中文描述"""
    mapping = {
        'normal': '正常',
        'low_risk': '低风险',
        'medium_risk': '中风险',
        'high_risk': '高风险'
    }
    return mapping.get(risk_level, '未知')
