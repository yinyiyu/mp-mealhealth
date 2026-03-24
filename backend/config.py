"""
应用配置文件
包含开发环境、生产环境的配置信息
"""
import os
from datetime import timedelta


class Config:
    """基础配置"""
    # Flask密钥，用于Session加密
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库配置（MySQL）
    # 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost:3306/mental_health_db?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭对象修改追踪，节省内存

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)   # 访问Token有效期8小时
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 刷新Token有效期30天

    # 允许跨域的来源（开发环境放开所有来源）
    CORS_ORIGINS = ['http://localhost:8080', 'http://localhost:3000']


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
