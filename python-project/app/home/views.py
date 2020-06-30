# _*_ coding: utf-8 _*_
from . import home
from app import db
from app.home.forms import LoginForm, RegisterForm, SuggetionForm
from app.models import User ,Category,Books,Borrow,Suggestion,Userlog
from flask import render_template, url_for, redirect, flash, session, request
from werkzeug.security import generate_password_hash
from sqlalchemy import and_
from functools import wraps


@home.route("/")
def index():
    """
    首页
    """
    category = Category.query.all()  # 获取所有类别
    books = Books.query.filter_by(is_hot=1).all()  # 热门书籍
    return render_template('home/index.html', category=category, books=books)  # 渲染模板


def user_login(f):
    """
    登录装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("home.login"))
        return f(*args, **kwargs)

    return decorated_function


@home.route("/login/", methods=["GET", "POST"])
def login():
    """
    登录
    """
    form = LoginForm()  # 实例化LoginForm类
    if form.validate_on_submit():  # 如果提交
        data = form.data  # 接收表单数据
        # 判断用户名和密码是否匹配
        user = User.query.filter_by(email=data["email"]).first()  # 获取用户信息
        if not user:
            flash("邮箱不存在！", "err")  # 输出错误信息
            return redirect(url_for("home.login"))  # 调回登录页
        if not user.check_pwd(data["pwd"]):  # 调用check_pwd()方法，检测用户名密码是否匹配
            flash("密码错误！", "err")  # 输出错误信息
            return redirect(url_for("home.login"))  # 调回登录页

        session["user_id"] = user.id  # 将user_id写入session, 后面用户判断用户是否登录
        # 将用户登录信息写入Userlog表
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)  # 存入数据
        db.session.commit()  # 提交数据
        return redirect(url_for("home.index"))  # 登录成功，跳转到首页
    return render_template("home/login.html", form=form)  # 渲染登录页面模板


@home.route("/register/", methods=["GET", "POST"])
def register():
    """
    注册功能
    """
    form = RegisterForm()  # 导入注册表单
    if form.validate_on_submit():  # 提交注册表单
        data = form.data  # 接收表单数据
        # 为User类属性赋值
        user = User(
            username=data["username"],  # 用户名
            email=data["email"],  # 邮箱
            pwd=generate_password_hash(data["pwd"]),  # 对密码加密
        )
        db.session.add(user)  # 添加数据
        db.session.commit()  # 提交数据
        flash("注册成功！", "ok")  # 使用flask存储成功信息
    return render_template("home/register.html", form=form)  # 渲染模板


@home.route("/logout/")
def logout():
    """
    退出登录
    """
    # 重定向到home模块下的登录。
    session.pop("user_id", None)
    return redirect(url_for('home.login'))


@home.route("/info/<int:id>/")
def info(id=None):  # id 为书籍ID
    """
    详情页
    """
    books = Books.query.get_or_404(int(id))  # 根据景区ID获取书籍数据，如果不存在返回404
    user_id = session.get('user_id', None)  # 获取用户ID,判断用户是否登录
    if user_id:  # 如果已经登录
        borrow = Borrow.query.filter_by(  # 根据用户ID和书籍ID判断用户是否已经借阅该书籍
            user_id=int(user_id),
            books_id=int(id)
        ).count()
    else:  # 用户未登录状态
        user_id = 0
        borrow = 0
    return render_template('home/info.html', books=books, user_id=user_id, borrow=borrow)  # 渲染模板


@home.route("/borrow_add/")
@user_login
def borrow_add():
    """
    借阅书籍
    """
    books_id = request.args.get("books_id", "")  # 接收传递的参数books_id
    user_id = session['user_id']  # 获取当前用户的ID
    borrow = Borrow.query.filter_by(  # 根据用户ID和书籍ID判断是否借阅
        user_id=int(user_id),
        books_id=int(books_id)
    ).count()
    # 已订阅
    if borrow == 1:
        data = dict(ok=0)  # 写入字典
    # 未订阅进行订阅
    if borrow == 0:
        borrow = Borrow(
            user_id=int(user_id),
            books_id=int(books_id)
        )
        db.session.add(borrow)  # 添加数据
        db.session.commit()  # 提交数据
        data = dict(ok=1)  # 写入字典
    import json  # 导入模块
    return json.dumps(data)  # 返回json数据


@home.route("/borrow_cancel/")
@user_login
def borrow_cancel():
    """
    还书籍
    """
    id = request.args.get("id", "")  # 获取景区ID
    user_id = session["user_id"]  # 获取当前用户ID
    borrow = Borrow.query.filter_by(id=id, user_id=user_id).first()  # 查找Borrow表，查看记录是否存在
    if borrow:  # 如果存在
        db.session.delete(borrow)  # 删除数据
        db.session.commit()  # 提交数据
        data = dict(ok=1)  # 写入字典
    else:
        data = dict(ok=-1)  # 写入字典
    import json  # 引入json模块
    return json.dumps(data)  # 输出json格式


@home.route("/borrow_list/")
@user_login
def borrow_list():
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    # 根据user_id删选Borrow表数据
    page_data = Borrow.query.filter_by(user_id=session['user_id']).order_by(
        Borrow.borrowedtime.desc()
    ).paginate(page=page, per_page=3)  # 使用分页方法
    return render_template('home/borrow_list.html', page_data=page_data)  # 渲染模板

@home.route("/search/")
def search():
    """
    搜素功能
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    category = Category.query.all()  # 获取所有书籍
    category_id = request.args.get('category_id', type=int)  #类别
    star = request.args.get('star', type=int)  # 星级

    if category_id or star:  # 根据星级搜索书籍
        filters = and_(Books.category_id == category_id, Books.star == star)
        page_data = Books.query.filter(filters).paginate(page=page, per_page=6)
    else:  # 搜索全部书籍
        page_data = Books.query.paginate(page=page, per_page=3)
    return render_template('home/search.html', page_data=page_data, category=category, category_id=category_id, star=star)


@home.route("/contact/", methods=["GET", "POST"])
def contact():
    """
    联系我们
    """
    form = SuggetionForm()  # 实例化SuggestionForm类
    if form.validate_on_submit():  # 判断用户是否提交表单
        data = form.data  # 接收用户提交的数据
        # 为属性赋值
        suggestion = Suggestion(
            name=data["name"],
            email=data["email"],
            content=data["content"],
        )
        db.session.add(suggestion)  # 添加数据
        db.session.commit()  # 提交数据
        flash("发送成功！", "ok")  # 用flask存储发送成功消息
    return render_template('home/contact.html', form=form)  # 渲染模板，并传递表单数据