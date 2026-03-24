"""
数据库模型定义
使用 Flask-SQLAlchemy ORM 定义各数据表结构
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    """
    用户表：存储所有系统用户（学生、心理老师、管理员）
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(64), unique=True, nullable=False, comment='登录用户名')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希值')
    role = db.Column(
        db.Enum('student', 'teacher', 'admin', 'super_admin'),
        nullable=False,
        default='student',
        comment='角色：student=学生, teacher=心理老师, admin=管理员, super_admin=超级管理员'
    )
    name = db.Column(db.String(64), nullable=False, comment='真实姓名')
    student_id = db.Column(db.String(32), unique=True, nullable=True, comment='学号（学生专用）')
    department = db.Column(db.String(128), nullable=True, comment='院系')
    grade = db.Column(db.String(16), nullable=True, comment='年级，如2022')
    phone = db.Column(db.String(16), nullable=True, comment='手机号')
    email = db.Column(db.String(128), nullable=True, comment='邮箱')
    openid = db.Column(db.String(128), unique=True, nullable=True, comment='微信OpenID（小程序登录用）')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联：一个用户可以有多个跟进记录
    follow_ups = db.relationship('FollowUp', foreign_keys='FollowUp.student_id', backref='student', lazy='dynamic')

    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        """转换为字典（用于JSON序列化）"""
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'name': self.name,
            'student_id': self.student_id,
            'department': self.department,
            'grade': self.grade,
            'phone': self.phone,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        return data

    def __repr__(self):
        return f'<User {self.username}>'


class QuestionnaireTemplate(db.Model):
    """
    问卷模板表：存储心理健康测评问卷模板
    """
    __tablename__ = 'questionnaire_templates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='模板ID')
    title = db.Column(db.String(256), nullable=False, comment='问卷标题')
    description = db.Column(db.Text, nullable=True, comment='问卷说明')
    category = db.Column(db.String(64), nullable=True, comment='问卷分类，如：抑郁筛查、焦虑筛查')
    # 计分说明（JSON格式）：如 {"总分": {"低风险": "0-9", "中风险": "10-19", "高风险": "20+"}}
    scoring_rules = db.Column(db.JSON, nullable=True, comment='计分规则（JSON格式）')
    # 维度定义（JSON格式）：定义问卷包含哪些维度，每个维度包含哪些题目
    dimensions = db.Column(db.JSON, nullable=True, comment='维度定义（JSON格式）')
    status = db.Column(
        db.Enum('draft', 'published', 'archived'),
        default='draft',
        comment='状态：draft=草稿, published=已发布, archived=已下架'
    )
    estimated_minutes = db.Column(db.Integer, default=10, comment='预计完成时长（分钟）')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联问题列表
    questions = db.relationship('Question', backref='template', lazy='dynamic',
                                order_by='Question.order_num')

    def to_dict(self, include_questions=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'scoring_rules': self.scoring_rules,
            'dimensions': self.dimensions,
            'status': self.status,
            'estimated_minutes': self.estimated_minutes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'question_count': self.questions.count()
        }
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions]
        return data


class Question(db.Model):
    """
    题目表：存储问卷中的具体题目
    """
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='题目ID')
    template_id = db.Column(db.Integer, db.ForeignKey('questionnaire_templates.id'),
                            nullable=False, comment='所属问卷模板ID')
    content = db.Column(db.Text, nullable=False, comment='题目内容')
    question_type = db.Column(
        db.Enum('single_choice', 'multiple_choice'),
        nullable=False,
        default='single_choice',
        comment='题目类型：single_choice=单选, multiple_choice=多选'
    )
    order_num = db.Column(db.Integer, default=0, comment='题目排序序号')
    dimension = db.Column(db.String(64), nullable=True, comment='所属维度，对应模板dimensions字段')
    # 选项格式（JSON数组）：[{"label": "A", "text": "从不", "score": 0}, ...]
    options = db.Column(db.JSON, nullable=False, comment='选项列表（JSON格式）')
    is_required = db.Column(db.Boolean, default=True, comment='是否必填')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'content': self.content,
            'question_type': self.question_type,
            'order_num': self.order_num,
            'dimension': self.dimension,
            'options': self.options,
            'is_required': self.is_required
        }


class Assessment(db.Model):
    """
    测评任务表：管理员发布的具体测评任务
    """
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='测评ID')
    title = db.Column(db.String(256), nullable=False, comment='测评标题')
    template_id = db.Column(db.Integer, db.ForeignKey('questionnaire_templates.id'),
                            nullable=False, comment='使用的问卷模板ID')
    # 测评对象（JSON格式）：{"type": "all"} 或 {"type": "department", "departments": ["计算机学院"]}
    target_config = db.Column(db.JSON, nullable=True, comment='测评对象配置')
    start_time = db.Column(db.DateTime, nullable=True, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    max_duration_minutes = db.Column(db.Integer, nullable=True, comment='最大答题时长（分钟），超时自动提交')
    status = db.Column(
        db.Enum('draft', 'ongoing', 'ended', 'archived'),
        default='draft',
        comment='状态：draft=草稿, ongoing=进行中, ended=已结束, archived=已归档'
    )
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联
    template = db.relationship('QuestionnaireTemplate', backref='assessments')
    submissions = db.relationship('AnswerSubmission', backref='assessment', lazy='dynamic')

    def is_active(self):
        """判断测评是否正在进行"""
        now = datetime.utcnow()
        if self.status != 'ongoing':
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'template_id': self.template_id,
            'template_title': self.template.title if self.template else None,
            'target_config': self.target_config,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'max_duration_minutes': self.max_duration_minutes,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active()
        }


class AnswerSubmission(db.Model):
    """
    答题提交记录表：存储学生的答题数据
    """
    __tablename__ = 'answer_submissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='提交记录ID')
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'),
                              nullable=False, comment='所属测评ID')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                           nullable=False, comment='学生用户ID')
    started_at = db.Column(db.DateTime, nullable=True, comment='开始答题时间')
    submitted_at = db.Column(db.DateTime, nullable=True, comment='提交时间')
    # 答案数据（JSON格式）：{"题目ID": "选项label" 或 ["选项label1", "选项label2"]}
    answers_data = db.Column(db.JSON, nullable=True, comment='答案数据（JSON格式）')
    submit_status = db.Column(
        db.Enum('in_progress', 'submitted', 'timeout'),
        default='in_progress',
        comment='提交状态：in_progress=答题中, submitted=已提交, timeout=超时提交'
    )
    ip_address = db.Column(db.String(64), nullable=True, comment='提交IP地址')

    # 关联
    student = db.relationship('User', backref='submissions')
    report = db.relationship('AssessmentReport', backref='submission', uselist=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'student_id': self.student_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'submit_status': self.submit_status,
            'answers_data': self.answers_data
        }


class AssessmentReport(db.Model):
    """
    测评报告表：存储系统自动生成的个人测评报告
    """
    __tablename__ = 'assessment_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='报告ID')
    submission_id = db.Column(db.Integer, db.ForeignKey('answer_submissions.id'),
                              nullable=False, unique=True, comment='关联的答题提交记录ID')
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'),
                              nullable=False, comment='所属测评ID')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                           nullable=False, comment='学生ID')
    total_score = db.Column(db.Float, nullable=False, default=0, comment='总分')
    # 各维度得分（JSON格式）：{"抑郁维度": 15, "焦虑维度": 8}
    dimension_scores = db.Column(db.JSON, nullable=True, comment='各维度得分')
    risk_level = db.Column(
        db.Enum('normal', 'low_risk', 'medium_risk', 'high_risk'),
        nullable=False,
        default='normal',
        comment='风险等级：normal=正常, low_risk=低风险, medium_risk=中风险, high_risk=高风险'
    )
    # 结果解读（JSON格式）：{"overall": "...", "dimensions": {"抑郁维度": "..."}}
    interpretation = db.Column(db.JSON, nullable=True, comment='结果解读')
    is_flagged = db.Column(db.Boolean, default=False, comment='是否被标记为重点关注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='报告生成时间')

    # 关联
    student = db.relationship('User', backref='reports')

    def to_dict(self, include_answers=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'submission_id': self.submission_id,
            'assessment_id': self.assessment_id,
            'student_id': self.student_id,
            'total_score': self.total_score,
            'dimension_scores': self.dimension_scores,
            'risk_level': self.risk_level,
            'interpretation': self.interpretation,
            'is_flagged': self.is_flagged,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_answers and self.submission:
            data['answers_data'] = self.submission.answers_data
        return data


class FollowUp(db.Model):
    """
    重点学生跟进记录表：心理老师对高风险学生的跟进情况
    """
    __tablename__ = 'follow_ups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='跟进记录ID')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    report_id = db.Column(db.Integer, db.ForeignKey('assessment_reports.id'),
                          nullable=True, comment='关联的测评报告ID')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='负责老师ID')
    follow_status = db.Column(
        db.Enum('pending', 'in_progress', 'closed'),
        default='pending',
        comment='跟进状态：pending=待沟通, in_progress=跟进中, closed=已结案'
    )
    notes = db.Column(db.Text, nullable=True, comment='跟进备注记录')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='assigned_followups')
    report = db.relationship('AssessmentReport', backref='follow_up')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_number': self.student.student_id if self.student else None,
            'department': self.student.department if self.student else None,
            'report_id': self.report_id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'follow_status': self.follow_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
