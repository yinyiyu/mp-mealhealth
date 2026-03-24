"""
Flask应用工厂函数
负责初始化Flask应用及各扩展（数据库、JWT、跨域等）
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 创建扩展实例（不绑定应用，使用应用工厂模式）
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='default'):
    """
    应用工厂函数：创建并配置Flask应用
    :param config_name: 配置环境名称（development/production/default）
    """
    app = Flask(__name__)

    # 加载配置
    from config import config
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # 开发环境允许所有跨域请求

    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'code': 401, 'message': 'Token已过期，请重新登录'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'code': 401, 'message': 'Token无效'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 注册蓝图（路由模块）
    from .auth.routes import auth_bp
    from .questionnaire.routes import questionnaire_bp
    from .assessment.routes import assessment_bp
    from .report.routes import report_bp
    from .student.routes import student_bp
    from .followup.routes import followup_bp
    from .statistics.routes import statistics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(questionnaire_bp, url_prefix='/api/questionnaire')
    app.register_blueprint(assessment_bp, url_prefix='/api/assessment')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(followup_bp, url_prefix='/api/followup')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')

    # 健康检查接口
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok', 'message': '心理健康测评系统后端运行正常'})

    return app
