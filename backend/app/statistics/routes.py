"""
数据统计模块
提供测评完成率、得分分布、风险等级占比等统计数据
用于管理后台的数据可视化图表
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from .. import db
from ..models import Assessment, AnswerSubmission, AssessmentReport, User, FollowUp
from ..utils import require_roles

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/overview', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def overview():
    """
    系统概览统计（首页看板数据）
    返回：学生总数、测评总数、已完成提交数、高风险学生数
    """
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_assessments = Assessment.query.count()
    total_submissions = AnswerSubmission.query.filter_by(submit_status='submitted').count()
    high_risk_count = AssessmentReport.query.filter_by(risk_level='high_risk').count()
    pending_followups = FollowUp.query.filter_by(follow_status='pending').count()

    return jsonify({
        'code': 200,
        'data': {
            'total_students': total_students,
            'total_assessments': total_assessments,
            'total_submissions': total_submissions,
            'high_risk_count': high_risk_count,
            'pending_followups': pending_followups
        }
    })


@statistics_bp.route('/assessment/<int:assessment_id>', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def assessment_statistics(assessment_id):
    """
    指定测评的统计数据
    返回：参与人数、完成率、各风险等级占比、平均分、得分分布
    """
    assessment = Assessment.query.get_or_404(assessment_id)

    # 参与该测评的学生总数（按target_config计算应参与人数）
    target_config = assessment.target_config or {'type': 'all'}

    if target_config.get('type') == 'all':
        expected_count = User.query.filter_by(role='student', is_active=True).count()
    elif target_config.get('type') == 'department':
        departments = target_config.get('departments', [])
        expected_count = User.query.filter(
            User.role == 'student',
            User.is_active == True,
            User.department.in_(departments)
        ).count()
    else:
        expected_count = User.query.filter_by(role='student', is_active=True).count()

    # 实际提交人数
    submitted_count = AnswerSubmission.query.filter_by(
        assessment_id=assessment_id,
        submit_status='submitted'
    ).count()

    # 完成率
    completion_rate = round(submitted_count / expected_count * 100, 2) if expected_count > 0 else 0

    # 风险等级分布
    risk_distribution = db.session.query(
        AssessmentReport.risk_level,
        func.count(AssessmentReport.id).label('count')
    ).filter_by(assessment_id=assessment_id).group_by(AssessmentReport.risk_level).all()

    risk_data = {row.risk_level: row.count for row in risk_distribution}

    # 平均分和分数区间分布
    score_stats = db.session.query(
        func.avg(AssessmentReport.total_score).label('avg_score'),
        func.min(AssessmentReport.total_score).label('min_score'),
        func.max(AssessmentReport.total_score).label('max_score')
    ).filter_by(assessment_id=assessment_id).first()

    avg_score = round(float(score_stats.avg_score), 2) if score_stats.avg_score else 0
    min_score = float(score_stats.min_score) if score_stats.min_score else 0
    max_score = float(score_stats.max_score) if score_stats.max_score else 0

    # 按院系分组的完成情况
    department_stats = db.session.query(
        User.department,
        func.count(AnswerSubmission.id).label('completed')
    ).join(
        AnswerSubmission, AnswerSubmission.student_id == User.id
    ).filter(
        AnswerSubmission.assessment_id == assessment_id,
        AnswerSubmission.submit_status == 'submitted'
    ).group_by(User.department).all()

    dept_data = [{'department': row.department or '未知', 'completed': row.completed}
                 for row in department_stats]

    return jsonify({
        'code': 200,
        'data': {
            'assessment_id': assessment_id,
            'assessment_title': assessment.title,
            'expected_count': expected_count,
            'submitted_count': submitted_count,
            'completion_rate': completion_rate,
            'risk_distribution': {
                'normal': risk_data.get('normal', 0),
                'low_risk': risk_data.get('low_risk', 0),
                'medium_risk': risk_data.get('medium_risk', 0),
                'high_risk': risk_data.get('high_risk', 0)
            },
            'score_stats': {
                'avg': avg_score,
                'min': min_score,
                'max': max_score
            },
            'department_stats': dept_data
        }
    })


@statistics_bp.route('/risk-trend', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def risk_trend():
    """
    风险等级趋势统计（按时间维度展示高风险人数变化）
    查询参数：months=6（最近N个月）
    """
    from datetime import datetime, timedelta
    months = request.args.get('months', 6, type=int)

    result = []
    now = datetime.utcnow()

    for i in range(months - 1, -1, -1):
        # 计算每月的时间范围
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(
            day=1, hour=0, minute=0, second=0
        )
        # 计算当月结束日
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        high_risk = AssessmentReport.query.filter(
            AssessmentReport.risk_level == 'high_risk',
            AssessmentReport.created_at >= month_start,
            AssessmentReport.created_at < month_end
        ).count()

        medium_risk = AssessmentReport.query.filter(
            AssessmentReport.risk_level == 'medium_risk',
            AssessmentReport.created_at >= month_start,
            AssessmentReport.created_at < month_end
        ).count()

        result.append({
            'month': month_start.strftime('%Y-%m'),
            'high_risk': high_risk,
            'medium_risk': medium_risk
        })

    return jsonify({'code': 200, 'data': result})


@statistics_bp.route('/followup-summary', methods=['GET'])
@jwt_required()
@require_roles('admin', 'super_admin', 'teacher')
def followup_summary():
    """跟进状态汇总统计"""
    status_counts = db.session.query(
        FollowUp.follow_status,
        func.count(FollowUp.id).label('count')
    ).group_by(FollowUp.follow_status).all()

    data = {row.follow_status: row.count for row in status_counts}

    return jsonify({
        'code': 200,
        'data': {
            'pending': data.get('pending', 0),
            'in_progress': data.get('in_progress', 0),
            'closed': data.get('closed', 0)
        }
    })
