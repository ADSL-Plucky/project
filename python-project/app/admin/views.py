# _*_ coding:utf-8 _*_
import os
import uuid
from datetime import datetime
from app import db
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, g, abort, make_response, current_app
from app.admin.forms import LoginForm, PwdForm, BooksForm, CategoryForm
from app.models import User ,Category,Books,Borrow,Suggestion,Userlog,Oplog,Admin,Adminlog
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from functools import wraps


def admin_login(f):
    """
    登录装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def addOplog(reason):
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason=reason
    )
    db.session.add(oplog)
    db.session.commit()


def gen_rnd_filename():
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex)


def change_filename(filename):
    """
    修改文件名称
    """
    fileinfo = os.path.splitext(filename)
    filename = gen_rnd_filename() + fileinfo[-1]
    return filename


@admin.route("/")
@admin_login
def index():
    '''
    后台登录
    '''
    return render_template("admin/index.html")


@admin.route("/login/", methods=["GET", "POST"])
def login():
    """
    登录功能
    """
    form = LoginForm()  # 实例化登录表单
    if form.validate_on_submit():  # 验证提交表单
        data = form.data  # 接收数据
        admin = Admin.query.filter_by(name=data["account"]).first()  # 查找Admin表数据
        # 密码错误时，check_pwd返回false,则此时not check_pwd(data["pwd"])为真。
        if not admin.check_pwd(data["pwd"]):
            flash("密码错误!", "err")  # 闪存错误信息
            return redirect(url_for("admin.login"))  # 跳转到后台登录页
        # 如果是正确的，就要定义session的会话进行保存。
        session["admin"] = data["account"]  # 存入session
        session["admin_id"] = admin.id  # 存入session
        # 创建数据
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr,
        )
        db.session.add(adminlog)  # 添加数据
        db.session.commit()  # 提交数据
        return redirect(url_for("admin.index"))  # 返回后台主页

    return render_template("admin/login.html", form=form)


@admin.route('/logout/')
@admin_login
def logout():
    """
    后台注销登录
    """
    session.pop("admin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@admin.route('/pwd/', methods=["GET", "POST"])
@admin_login
def pwd():
    """
    后台密码修改
    """
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功，请重新登录！", "ok")
        return redirect(url_for('admin.logout'))
    return render_template("admin/pwd.html", form=form)


@admin.route("/user/list/", methods=["GET"])
@admin_login
def user_list():
    """
    会员列表
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    keyword = request.args.get('keyword', '', type=str)

    if keyword:
        # 根据姓名或者邮箱查询
        filters = or_(User.username == keyword, User.email == keyword)
        page_data = User.query.filter(filters).paginate(page=page, per_page=5)
    else:
        page_data = User.query.paginate(page=page, per_page=5)

    return render_template("admin/user_list.html", page_data=page_data)


@admin.route("/user/view/<int:id>/", methods=["GET"])
@admin_login
def user_view(id=None):
    """
    查看会员详情
    """
    from_page = request.args.get('fp')
    if not from_page:
        from_page = 1
    user = User.query.get_or_404(int(id))
    return render_template("admin/user_view.html", user=user, from_page=from_page)


@admin.route("/user/del/<int:id>/", methods=["GET"])
@admin_login
def user_del(id=None):
    """
    删除会员
    """
    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    addOplog("删除会员" + user.username)  # 添加日志
    flash("删除会员成功！", "ok")
    return redirect(url_for('admin.user_list', page=page))


@admin.route("/suggestion_list/list/", methods=["GET"])
@admin_login
def suggestion_list():
    """
    意见建议列表
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    page_data = Suggestion.query.order_by(
        Suggestion.addtime.desc()
    ).paginate(page=page, per_page=5)
    return render_template("admin/suggestion_list.html", page_data=page_data)


@admin.route("/suggestion/del/<int:id>/", methods=["GET"])
@admin_login
def suggestion_del(id=None):
    """
    删除会员
    """
    page = request.args.get('page', 1, type=int)
    suggestion = Suggestion.query.get_or_404(int(id))
    db.session.delete(suggestion)
    db.session.commit()
    addOplog("删除意见建议")  # 添加日志
    flash("删除成功！", "ok")
    return redirect(url_for('admin.suggestion_list', page=page))


@admin.route('/category/add/', methods=["GET", "POST"])
@admin_login
def category_add():
    """
    添加类别
    """
    form = CategoryForm()
    if form.validate_on_submit():
        data = form.data  # 接收数据
        category = Category.query.filter_by(name=data["name"]).count()
        # 说明已经有这个类别了
        if category == 1:
            flash("类别已存在", "err")
            return redirect(url_for("admin.category_add"))
        category = Category(
            name=data["name"],
        )
        db.session.add(category)
        db.session.commit()
        addOplog("添加类别" + data["name"])  # 添加日志
        flash("类别添加成功", "ok")
        return redirect(url_for("admin.category_add"))
    return render_template("admin/category_add.html", form=form)


@admin.route("/category/edit/<int:id>", methods=["GET", "POST"])
@admin_login
def category(id=None):
    """
    类别编辑
    """
    form = CategoryForm()
    form.submit.label.text = "修改"
    category = Category.query.get_or_404(id)
    if request.method == "GET":
        form.name.data = category.name
    if form.validate_on_submit():
        data = form.data
        category_count = Category.query.filter_by(name=data["name"]).count()
        if category.name != data["name"] and category_count == 1:
            flash("类别已存在", "err")
            return redirect(url_for("admin.category_edit", id=category.id))
        category.name = data["name"]
        db.session.add(category)
        db.session.commit()
        flash("类别修改成功", "ok")
        return redirect(url_for("admin.category_edit", id=category.id))
    return render_template("admin/category_edit.html", form=form, category=category)


@admin.route("/category/list/", methods=["GET"])
@admin_login
def category_list():
    """
    标签列表
    """
    name = request.args.get('name', type=str)  # 获取name参数值
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    if name:  # 搜索功能
        page_data = Category.query.filter_by(name=name).paginate(page=page, per_page=5)
    else:
        # 查找数据
        page_data = Category.query.paginate(page=page, per_page=5)
    return render_template("admin/category_list.html", page_data=page_data)  # 渲染模板


@admin.route("/category/del/<int:id>/", methods=["GET"])
@admin_login
def category_del(id=None):
    """
    标签删除
    """
    # filter_by在查不到或多个的时候并不会报错，get会报错。
    category = Category.query.filter_by(id=id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    addOplog("删除类别" + category.name)  # 添加日志
    flash("类别<<{0}>>删除成功".format(category.name), "ok")
    return redirect(url_for("admin.category_list"))


@admin.route("/oplog/list/", methods=["GET"])
@admin_login
def oplog_list():
    """
    操作日志管理
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id,
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/oplog_list.html", page_data=page_data)


@admin.route("/adminloginlog/list/", methods=["GET"])
@admin_login
def adminloginlog_list(page=None):
    """
    管理员登录日志
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id,
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


@admin.route("/userloginlog/list/", methods=["GET"])
@admin_login
def userloginlog_list(page=None):
    """
    会员登录日志列表
    """
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id,
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=5)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


@admin.route("/books/add/", methods=["GET", "POST"])
@admin_login
def books_add():
    """
    添加书籍页面
    """
    form = BooksForm()  # 实例化form表单
    form.category_id.choices = [(v.id, v.name) for v in Category.query.all()]  # 为category_id添加属性
    if form.validate_on_submit():
        data = form.data
        # 判断书籍是否存在
        books_count = Books.query.filter_by(title=data["title"]).count()
        # 判断是否有重复数据。
        if books_count == 1:
            flash("书籍已经存在！", "err")
            return redirect(url_for('admin.books_add'))

        file_logo = secure_filename(form.logo.data.filename)  # 确保文件名
        if not os.path.exists(current_app.config["UP_DIR"]):
            # 创建一个多级目录
            os.makedirs(current_app.config["UP_DIR"])  # 创建文件夹
            os.chmod(current_app.config["UP_DIR"], "rw")  # 设置权限
        logo = change_filename(file_logo)  # 更改名称
        form.logo.data.save(current_app.config["UP_DIR"] + logo)  # 保存文件
        # 为books类属性赋值
        books = Books(
            title=data["title"],
            logo=logo,
            star=int(data["star"]),
            author=data["author"],
            is_hot=int(data["is_hot"]),
            is_recommended=int(data["is_recommended"]),
            category_id=data["category_id"],
            introduction=data["introduction"],
            content=data["content"],
        )
        db.session.add(books)  # 添加数据
        db.session.commit()  # 提交数据
        addOplog("添加书籍" + data["title"])  # 添加日志
        flash("添加书籍成功！", "ok")  # 使用flash保存添加成功信息
        return redirect(url_for('admin.books_add'))  # 页面跳转
    return render_template("admin/books_add.html", form=form)  # 渲染模板


@admin.route("/books/list/", methods=["GET"])
@admin_login
def books_list():
    """
    书籍列表页面
    """
    title = request.args.get('title', '', type=str)  # 获取查询标题
    page = request.args.get('page', 1, type=int)  # 获取page参数值
    if title:  # 根据标题搜索书籍
        page_data = Books.query.filter_by(title=title).paginate(page=page, per_page=5)  # 分页
    else:  # 显示全部书籍
        page_data = Books.query.paginate(page=page, per_page=5)  # 分页
    return render_template("admin/books_list.html", page_data=page_data)  # 渲染模板


@admin.route("/books/edit/<int:id>/", methods=["GET", "POST"])
@admin_login
def books_edit(id=None):
    """
    编辑书籍页面
    """
    form = BooksForm()  # 实例化booksForm类
    form.category_id.choices = [(v.id, v.name) for v in Category.query.all()]  # 为category_id添加属性
    form.submit.label.text = "修改"  # 修改提交按钮的文字
    form.logo.validators = []  # 初始化为空
    books = Books.query.get_or_404(int(id))  # 根据ID查找书籍是否存在
    if request.method == "GET":  # 如果以GET方式提交，获取所有书籍信息
        form.is_recommended.data = books.is_recommended
        form.is_hot.data = books.is_hot
        form.category_id.data = books.category_id
        form.star.data = books.star
        form.content.data = books.content
        form.introduction.data = books.introduction
    if form.validate_on_submit():  # 如果提交表单
        data = form.data  # 获取表单数据
        books_count = Books.query.filter_by(title=data["title"]).count()  # 判断标题是否重复
        # 判断是否有重复数据
        if books_count == 1 and books.title != data["title"]:
            flash("书籍已经存在！", "err")
            return redirect(url_for('admin.books_edit', id=id))
        if not os.path.exists(current_app.config["UP_DIR"]):  # 判断目录是否存在
            os.makedirs(current_app.config["UP_DIR"])  # 创建目录
            os.chmod(current_app.config["UP_DIR"], "rw")  # 设置读写权限
        # 上传图片
        if form.logo.data != "":
            file_logo = secure_filename(form.logo.data.filename)  # 确保文件名安全
            books.logo = change_filename(file_logo)  # 更改文件名
            form.logo.data.save(current_app.config["UP_DIR"] + books.logo)  # 保存文件

        # 属性赋值
        books.title = data["title"]
        books.address = data["address"]
        books.category_id = data["category_id"]
        books.star = int(data["star"])
        books.is_hot = int(data["is_hot"])
        books.is_recommended = int(data["is_recommended"])
        books.introduction = data["introduction"]
        books.content = data["content"]

        db.session.add(books)  # 添加数据
        db.session.commit()  # 提交数据
        flash("修改书籍成功！", "ok")
        return redirect(url_for('admin.books_edit', id=id))  # 跳转到编辑页面
    return render_template("admin/books_edit.html", form=form, books=books)  # 渲染模板，传递变量


@admin.route("/books/del/<int:id>/", methods=["GET"])
@admin_login
def books_del(id=None):
    """
    书籍删除
    """
    books = Books.query.get_or_404(id)  # 根据书籍ID查找数据
    db.session.delete(books)  # 删除数据
    db.session.commit()  # 提交数据
    flash("书籍删除成功", "ok")  # 使用flash存储成功信息
    addOplog("删除书籍" + books.title)  # 添加日志
    return redirect(url_for('admin.books_list', page=1))  # 渲染模板


@admin.route('/ckupload/', methods=['POST', 'OPTIONS'])
@admin_login
def ckupload():
    """CKEditor 文件上传"""
    error = ''
    url = ''
    callback = request.args.get("CKEditorFuncNum")

    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        fname, fext = os.path.splitext(fileobj.filename)
        rnd_name = '%s%s' % (gen_rnd_filename(), fext)

        filepath = os.path.join(current_app.static_folder, 'uploads/ckeditor', rnd_name)
        print(filepath)
        # 检查路径是否存在，不存在则创建
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                error = 'ERROR_CREATE_DIR'
        elif not os.access(dirname, os.W_OK):
            error = 'ERROR_DIR_NOT_WRITEABLE'

        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename='%s/%s' % ('uploads/ckeditor', rnd_name))
    else:
        error = 'post error'

    res = """<script type="text/javascript">
  window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
</script>""" % (callback, url, error)

    response = make_response(res)
    response.headers["Content-Type"] = "text/html"
    return response
