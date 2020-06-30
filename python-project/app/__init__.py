# _*_ Coding:utf-8 _*_

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

# 创建数据库
db = SQLAlchemy()

def create_app(config_name):
    # 初始化
    app = Flask(__name__)

    # 导致指定的配置对象:创建app时，传入环境的名称
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展（数据库）
    db.init_app(app)

    # 注册蓝图
    from app.home import home as home_blueprint
    from app.admin import admin as admin_blueprint
    app.register_blueprint(home_blueprint)
    app.register_blueprint(admin_blueprint,url_prefix="/admin")

    return app
