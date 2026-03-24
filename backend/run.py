"""
Flask应用启动入口
运行方式：python run.py
"""
import os
from app import create_app, db
from app.models import User

# 从环境变量读取配置，默认使用开发环境
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)


@app.cli.command('init-db')
def init_db():
    """
    初始化数据库命令
    使用：flask init-db
    会创建所有数据表，并初始化一个超级管理员账号
    """
    db.create_all()
    print('数据库表创建完成')

    # 检查是否已有超级管理员
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            role='super_admin',
            name='系统管理员',
            is_active=True
        )
        admin.set_password('Admin@123')  # 默认密码，首次登录后请修改
        db.session.add(admin)
        db.session.commit()
        print('超级管理员账号已创建：admin / Admin@123')
    else:
        print('超级管理员账号已存在，跳过创建')


if __name__ == '__main__':
    # 开发环境直接运行
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=True
    )
