"""
测评报告模块路由
提供报告查询接口（学生查个人报告、管理员查所有报告）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import AssessmentReport, Assessment, AnswerSubmission
from ..utils import require_roles, get_current_user

report_bp = Blueprint('report', __name__)


@report_bp.route('/my', methods=['GET'])
@jwt_required()
def my_reports():
    """
    学生查询本人的历史测评报告列表
    查询参数：page=1&per_page=10
    """
    current_user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = AssessmentReport.query.filter_by(student_id=current_user.id) \
        .order_by(AssessmentReport.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    reports = []
    for r in pagination.items:
        report_data = r.to_dict()
        # 附加测评标题信息
        if r.submission and r.submission.assessment:
            report_data['assessment_title'] = r.submission.assessment.title
        reports.append(report_data)

    return jsonify({
        'code': 200,
        'data': {
            'items': reports,
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        }
    })


@report_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """
    获取指定报告详情
    - 学生只能查看本人报告
    - 老师和管理员可以查看所有学生报告（含详细信息）
    """
    current_user = get_current_user()
    report = AssessmentReport.query.get_or_404(report_id)

    # 权限控制：学生只能看本人报告
    if current_user.role == 'student' and report.student_id != current_user.id:
        return jsonify({'code': 403, 'message': '无权查看该报告'}), 403

    # 构建报告详情
    data = report.to_dict(include_answers=True)

    # 附加关联信息
    if report.student:
        data['student_info'] = {
            'name': report.student.name,
            'student_id': report.student.student_id,
            'department': report.student.department,
            'grade': report.student.grade
        }
    if report.submission and report.submission.assessment:
        data['assessment_title'] = report.submission.assessment.title

    return jsonify({'code': 200, 'data': data})


@report_bp.route('/list', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def list_all_reports():
    """
    管理员/老师查询所有测评报告列表（群体数据视图）
    支持按测评、风险等级、院系筛选，支持分页
    查询参数：assessment_id=1&risk_level=high_risk&department=计算机学院&page=1
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    assessment_id = request.args.get('assessment_id', type=int)
    risk_level = request.args.get('risk_level')
    department = request.args.get('department')

    from .. import db
    from ..models import User

    query = AssessmentReport.query

    if assessment_id:
        query = query.filter_by(assessment_id=assessment_id)
    if risk_level:
        query = query.filter_by(risk_level=risk_level)

    # 按院系筛选（需要关联User表）
    if department:
        query = query.join(User, AssessmentReport.student_id == User.id) \
                     .filter(User.department == department)

    pagination = query.order_by(AssessmentReport.created_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    reports = []
    for r in pagination.items:
        report_data = r.to_dict()
        if r.student:
            report_data['student_name'] = r.student.name
            report_data['student_number'] = r.student.student_id
            report_data['department'] = r.student.department
        reports.append(report_data)

    return jsonify({
        'code': 200,
        'data': {
            'items': reports,
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        }
    })


@report_bp.route('/high-risk', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def high_risk_students():
    """
    获取高风险学生列表（重点关注名单）
    返回最新一次测评为高风险的学生列表
    """
    current_user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    assessment_id = request.args.get('assessment_id', type=int)

    query = AssessmentReport.query.filter_by(risk_level='high_risk', is_flagged=True)

    if assessment_id:
        query = query.filter_by(assessment_id=assessment_id)

    # 老师只能看自己负责的学生（通过follow_up的teacher_id关联）
    # 简化处理：超级管理员和管理员可以看所有，老师看所有（实际项目可按部门限制）

    pagination = query.order_by(AssessmentReport.created_at.desc()) \
                      .paginate(page=page, per_page=per_page, error_out=False)

    students = []
    for r in pagination.items:
        item = {
            'report_id': r.id,
            'assessment_id': r.assessment_id,
            'total_score': r.total_score,
            'created_at': r.created_at.isoformat() if r.created_at else None
        }
        if r.student:
            item.update({
                'student_id': r.student_id,
                'student_name': r.student.name,
                'student_number': r.student.student_id,
                'department': r.student.department,
                'grade': r.student.grade,
                'phone': r.student.phone
            })
        # 附加跟进状态
        if r.follow_up:
            item['follow_status'] = r.follow_up.follow_status
            item['follow_up_id'] = r.follow_up.id
        else:
            item['follow_status'] = None
        students.append(item)

    return jsonify({
        'code': 200,
        'data': {
            'items': students,
            'total': pagination.total,
            'page': page,
            'pages': pagination.pages
        }
    })
