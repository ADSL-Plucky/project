from . import db
from datetime import datetime


# 会员数据模型
class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    username = db.Column(db.String(100))  # 用户名
    pwd = db.Column(db.String(100))  # 密码
    email = db.Column(db.String(100), unique=True)  # 邮箱
    phone = db.Column(db.String(11), unique=True)  # 手机号
    info = db.Column(db.Text)  # 个性简介
    face = db.Column(db.String(255), unique=True)  # 头像
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 注册时间


    userlogs = db.relationship('Userlog', backref='user')  # 会员日志外键关系关联
    borrow = db.relationship('Borrow', backref='user')  # 借阅外键关系关联

    def __repr__(self):
        return '<User %r>' % self.name

    def check_pwd(self, pwd):
        """
        检测密码是否正确
        :param pwd: 密码
        :return: 返回布尔值
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 管理员
class Admin(db.Model):
    __tablename__ = "admin"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 管理员账号
    pwd = db.Column(db.String(100))  # 管理员密码


    adminlogs = db.relationship("Adminlog", backref='admin')  # 管理员登录日志外键关系关联
    oplogs = db.relationship("Oplog", backref='admin')  # 管理员操作日志外键关系关联

    def __repr__(self):
        return "<Admin %r>" % self.name

    def check_pwd(self, pwd):
        """
        检测密码是否正确
        :param pwd: 密码
        :return: 返回布尔值
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 管理员登录日志
class Adminlog(db.Model):
    __tablename__ = "adminlog"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所属管理员
    ip = db.Column(db.String(100))  # 登录IP
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return "<Adminlog %r>" % self.id


# 操作日志
class Oplog(db.Model):
    __tablename__ = "oplog"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所属管理员
    ip = db.Column(db.String(100))  # 操作IP
    reason = db.Column(db.String(600))  # 操作原因
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return "<Oplog %r>" % self.id


# 类别
class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 标题

    books = db.relationship("Books", backref='category')  # 外键关系关联

    def __repr__(self):
        return "<Category %r>" % self.name


# 会员登录日志
class Userlog(db.Model):
    __tablename__ = "userlog"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    # 设置外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所属会员
    ip = db.Column(db.String(100))  # ip地址
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return '<User %r>' % self.id


# 书籍
class Books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    title = db.Column(db.String(255), unique=True)  # 标题
    star = db.Column(db.Integer)  # 星级
    logo = db.Column(db.String(255), unique=True)  # 封面
    introduction = db.Column(db.Text)  # 书籍简介
    content = db.Column(db.Text)  # 书籍内容
    author = db.Column(db.String(255))  # 作者
    is_hot = db.Column(db.Boolean(), default=0)  # 是否热门
    is_recommended = db.Column(db.Boolean(), default=0)  # 是否推荐

    # 设置外键
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # 所属类别
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  #书籍上传时间
    is_borrowed = db.relationship("Borrow", backref='books')  # 收藏外键关系关联

    def __repr__(self):
        return "<Books %r>" % self.title

# 书籍借阅
class Borrow(db.Model):
    __tablename__ = "borrow"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号

    books_id = db.Column(db.Integer, db.ForeignKey('books.id'))  # 书籍
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所属用户
    borrowedtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 借出时间

    def __repr__(self):
        return "<Borrow %r>" % self.id


# 意见建议
class Suggestion(db.Model):
    __tablename__ = "suggestion"
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(255))  # 昵称
    email = db.Column(db.String(100))  # 邮箱
    content = db.Column(db.Text)  # 意见内容
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 注册时间

    def __repr__(self):
        return "<Suggestion %r>" % self.id