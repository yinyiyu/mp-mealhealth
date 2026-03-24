"""
报告生成服务
核心业务逻辑：根据学生答题数据计算得分、判定风险等级、生成解读
"""
from ..models import AssessmentReport, AnswerSubmission, FollowUp
from .. import db


def calculate_score(submission: AnswerSubmission) -> dict:
    """
    计算测评得分
    :param submission: 答题提交记录
    :return: {"total_score": 25, "dimension_scores": {"抑郁维度": 15, "焦虑维度": 10}}

    计分逻辑：
    1. 遍历所有题目，根据学生选择的选项查找对应分值
    2. 单选题：直接取选项分值
    3. 多选题：将所有选中选项的分值相加
    4. 按维度汇总各维度总分
    """
    template = submission.assessment.template
    if not template:
        return {'total_score': 0, 'dimension_scores': {}}

    answers = submission.answers_data or {}
    total_score = 0
    dimension_scores = {}

    for question in template.questions:
        question_id = str(question.id)
        student_answer = answers.get(question_id)

        if student_answer is None:
            continue  # 未作答，跳过（计0分）

        question_score = 0

        if question.question_type == 'single_choice':
            # 单选：找到对应选项的分值
            for option in question.options:
                if option.get('label') == student_answer:
                    question_score = option.get('score', 0)
                    break

        elif question.question_type == 'multiple_choice':
            # 多选：将所有选中选项的分值相加
            if isinstance(student_answer, list):
                for option in question.options:
                    if option.get('label') in student_answer:
                        question_score += option.get('score', 0)

        total_score += question_score

        # 按维度累加
        dimension = question.dimension or '总分'
        dimension_scores[dimension] = dimension_scores.get(dimension, 0) + question_score

    return {
        'total_score': round(total_score, 2),
        'dimension_scores': dimension_scores
    }


def determine_risk_level(total_score: float, scoring_rules: dict) -> str:
    """
    根据总分和计分规则判定风险等级
    :param total_score: 总分
    :param scoring_rules: 计分规则，格式如 {"总分": {"正常": "0-4", "轻度": "5-9", ...}}
    :return: 风险等级字符串

    映射关系（基于常见量表分级）：
    - "正常" / "低" / "轻度" -> normal
    - "轻度" / "中低" -> low_risk
    - "中度" / "中" -> medium_risk
    - "重度" / "高" / "严重" -> high_risk
    """
    if not scoring_rules:
        # 无计分规则，按通用阈值判定（总分制100分）
        if total_score < 25:
            return 'normal'
        elif total_score < 50:
            return 'low_risk'
        elif total_score < 75:
            return 'medium_risk'
        else:
            return 'high_risk'

    # 解析计分规则（取第一个维度的规则，通常为"总分"）
    rule_key = list(scoring_rules.keys())[0]
    rules = scoring_rules[rule_key]

    for level_name, score_range in rules.items():
        # 解析分数区间，格式："0-4" 或 "20+"
        try:
            if '+' in str(score_range):
                min_score = float(str(score_range).replace('+', ''))
                if total_score >= min_score:
                    return _map_level_name(level_name)
            elif '-' in str(score_range):
                parts = str(score_range).split('-')
                min_score = float(parts[0])
                max_score = float(parts[1])
                if min_score <= total_score <= max_score:
                    return _map_level_name(level_name)
        except (ValueError, IndexError):
            continue

    return 'normal'


def _map_level_name(level_name: str) -> str:
    """将中文等级名映射为系统风险等级"""
    level_name_lower = level_name.lower()
    high_keywords = ['重度', '高', '严重', 'severe', 'high', '极高']
    medium_keywords = ['中度', '中', 'moderate', 'medium', '中等']
    low_keywords = ['轻度', '低', 'mild', 'low', '轻微']

    for kw in high_keywords:
        if kw in level_name:
            return 'high_risk'
    for kw in medium_keywords:
        if kw in level_name:
            return 'medium_risk'
    for kw in low_keywords:
        if kw in level_name:
            return 'low_risk'
    return 'normal'


def generate_interpretation(total_score: float, risk_level: str,
                            dimension_scores: dict, scoring_rules: dict) -> dict:
    """
    生成结果解读文字
    :return: {"overall": "...", "dimensions": {"情绪症状": "..."}}
    """
    risk_text = {
        'normal': '您的心理健康状态良好，测评结果显示无明显心理健康问题。建议保持良好的生活习惯和心态。',
        'low_risk': '您的测评结果显示存在轻微心理健康风险。建议关注自身情绪变化，适当放松，如有需要可咨询学校心理健康中心。',
        'medium_risk': '您的测评结果显示存在中度心理健康风险。建议尽快预约心理咨询，与专业老师进行深入沟通，及时得到专业支持。',
        'high_risk': '您的测评结果显示存在较高心理健康风险。请立即联系学校心理健康中心或心理老师，寻求专业帮助。我们会有专业老师跟进关注您的情况。'
    }

    interpretation = {
        'overall': risk_text.get(risk_level, ''),
        'total_score': total_score,
        'dimensions': {}
    }

    # 为每个维度生成简短解读
    for dim_name, dim_score in dimension_scores.items():
        interpretation['dimensions'][dim_name] = f'{dim_name}得分：{dim_score}分'

    return interpretation


def generate_report(submission: AnswerSubmission) -> AssessmentReport:
    """
    根据答题记录生成完整的测评报告
    :param submission: 已提交的答题记录
    :return: 生成的 AssessmentReport 对象

    处理流程：
    1. 计算各题得分和维度得分
    2. 根据计分规则判定风险等级
    3. 生成结果解读文字
    4. 保存报告到数据库
    5. 高风险学生自动标记并创建跟进记录
    """
    # 计算得分
    score_data = calculate_score(submission)
    total_score = score_data['total_score']
    dimension_scores = score_data['dimension_scores']

    # 获取计分规则
    template = submission.assessment.template
    scoring_rules = template.scoring_rules if template else None

    # 判定风险等级
    risk_level = determine_risk_level(total_score, scoring_rules)

    # 生成解读
    interpretation = generate_interpretation(
        total_score, risk_level, dimension_scores, scoring_rules
    )

    # 创建或更新报告
    existing_report = AssessmentReport.query.filter_by(
        submission_id=submission.id
    ).first()

    if existing_report:
        # 更新已有报告
        existing_report.total_score = total_score
        existing_report.dimension_scores = dimension_scores
        existing_report.risk_level = risk_level
        existing_report.interpretation = interpretation
        report = existing_report
    else:
        # 创建新报告
        report = AssessmentReport(
            submission_id=submission.id,
            assessment_id=submission.assessment_id,
            student_id=submission.student_id,
            total_score=total_score,
            dimension_scores=dimension_scores,
            risk_level=risk_level,
            interpretation=interpretation,
            is_flagged=(risk_level == 'high_risk')  # 高风险自动标记
        )
        db.session.add(report)

    db.session.flush()  # 获取report.id

    # 高风险学生自动创建跟进记录
    if risk_level == 'high_risk':
        existing_followup = FollowUp.query.filter_by(
            student_id=submission.student_id,
            report_id=report.id
        ).first()
        if not existing_followup:
            followup = FollowUp(
                student_id=submission.student_id,
                report_id=report.id,
                follow_status='pending'  # 待沟通状态
            )
            db.session.add(followup)

    db.session.commit()
    return report
