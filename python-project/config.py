# -*- coding=utf-8 -*-
import os
class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    UP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "app/static/uploads/")  # 文件上传路径
    FC_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "app/static/uploads/users/")  # 用户头像上传路径

    # 将Config类作为参数传递到其他函数中,又希望在实例化Config类之前就能提供下列的功能,所以使用staticmethod.
    @staticmethod
    def init_app(app):
        pass

# 继承Config类,下列定义数据库地址,定义开发环境
# the config for development
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@127.0.0.1:3306/library'
    DEBUG = True

# define the config
config = {
    'default': DevelopmentConfig
}
