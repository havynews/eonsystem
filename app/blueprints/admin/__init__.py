from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.db import db
from app.models import (
    User, Product, UserProduct, Withdrawal,
    News, RechargeMethod, RechargeOrder, IncomeLog, GiftCode
)
from datetime import datetime
import random, string

admin_bp = Blueprint("admin", __name__)


# ── Admin-only decorator ──────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_users":      User.query.count(),
        "total_products":   Product.query.filter_by(is_active=True).count(),
        "pending_recharge": RechargeOrder.query.filter_by(status="pending").count(),
        "pending_withdraw": Withdrawal.query.filter_by(status="pending").count(),
        "total_income":     db.session.query(db.func.sum(IncomeLog.amount)).scalar() or 0,
        "total_balance":    db.session.query(db.func.sum(User.balance)).scalar() or 0,
    }
    recent_recharges   = RechargeOrder.query.order_by(RechargeOrder.created_at.desc()).limit(5).all()
    recent_withdrawals = Withdrawal.query.order_by(Withdrawal.requested_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html",
                           stats=stats,
                           recent_recharges=recent_recharges,
                           recent_withdrawals=recent_withdrawals)


# ─────────────────────────────────────────────────────────────────
#  Users
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    search = request.args.get("q", "").strip()
    query  = User.query
    if search:
        query = query.filter(User.phone.ilike(f"%{search}%"))
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, search=search)


@admin_bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        try:
            user.phone      = request.form.get("phone", user.phone).strip()
            user.vip_level  = request.form.get("vip_level", user.vip_level).strip()
            user.balance    = float(request.form.get("balance", user.balance))
            user.total_income = float(request.form.get("total_income", user.total_income))
            user.agent      = "agent" in request.form
            user.is_admin   = "is_admin" in request.form
            new_password    = request.form.get("new_password", "").strip()
            if new_password:
                user.set_password(new_password)
            db.session.commit()
            flash(f"User {user.phone} updated.", "success")
            return redirect(url_for("admin.users"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
    return render_template("admin/edit_user.html", user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.users"))


# ─────────────────────────────────────────────────────────────────
#  Products
# ─────────────────────────────────────────────────────────────────

from app.cloudinary_helper import upload_product_image


@admin_bp.route("/products")
@login_required
@admin_required
def products():
    all_products = Product.query.order_by(Product.id).all()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_product():
    if request.method == "POST":
        try:
            name      = request.form["name"].strip()
            image_url = None

            file = request.files.get("image")
            if file and file.filename:
                result    = upload_product_image(file, name)
                image_url = result["url"]

            product = Product(
                name         = name,
                description  = request.form.get("description", "").strip(),
                price        = float(request.form["price"]),
                daily_income = float(request.form["daily_income"]),
                total_income = float(request.form["total_income"]),
                rental_days  = int(request.form["rental_days"]),
                image        = image_url,
                vip_level    = int(request.form["vip_level"]) if request.form.get("vip_level") else None,
                is_active    = "is_active" in request.form,
            )
            db.session.add(product)
            db.session.commit()
            flash(f"Product '{product.name}' created.", "success")
            return redirect(url_for("admin.products"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")

    return render_template("admin/product_form.html", product=None)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        try:
            product.name         = request.form["name"].strip()
            product.description  = request.form.get("description", "").strip()
            product.price        = float(request.form["price"])
            product.daily_income = float(request.form["daily_income"])
            product.total_income = float(request.form["total_income"])
            product.rental_days  = int(request.form["rental_days"])
            product.vip_level    = int(request.form["vip_level"]) if request.form.get("vip_level") else None
            product.is_active    = "is_active" in request.form

            # Only replace image if a new file was uploaded
            file = request.files.get("image")
            if file and file.filename:
                result        = upload_product_image(file, product.name)
                product.image = result["url"]

            db.session.commit()
            flash(f"Product '{product.name}' updated.", "success")
            return redirect(url_for("admin.products"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")

    return render_template("admin/product_form.html", product=product)

@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        product.is_active = False
        db.session.commit()
        flash(f"Product '{product.name}' deactivated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.products"))


# ─────────────────────────────────────────────────────────────────
#  Recharge Orders (Payments)
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/recharges")
@login_required
@admin_required
def recharges():
    status = request.args.get("status", "")
    query  = RechargeOrder.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(RechargeOrder.created_at.desc()).all()
    return render_template("admin/recharges.html", orders=orders, status=status)


@admin_bp.route("/recharges/<int:order_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_recharge(order_id):
    order = RechargeOrder.query.get_or_404(order_id)
    try:
        order.user.balance = float(order.user.balance) + float(order.amount)
        order.status       = "approved"
        db.session.commit()
        flash(f"Recharge {order.order_number} approved. K{order.amount} credited to {order.user.phone}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.recharges"))


@admin_bp.route("/recharges/<int:order_id>/decline", methods=["POST"])
@login_required
@admin_required
def decline_recharge(order_id):
    order = RechargeOrder.query.get_or_404(order_id)
    try:
        order.status = "declined"
        db.session.commit()
        flash(f"Recharge {order.order_number} declined.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.recharges"))


# ─────────────────────────────────────────────────────────────────
#  Withdrawals
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/withdrawals")
@login_required
@admin_required
def withdrawals():
    status = request.args.get("status", "")
    query  = Withdrawal.query
    if status:
        query = query.filter_by(status=status)
    all_withdrawals = query.order_by(Withdrawal.requested_at.desc()).all()
    return render_template("admin/withdrawals.html", withdrawals=all_withdrawals, status=status)


@admin_bp.route("/withdrawals/<int:withdrawal_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    w = Withdrawal.query.get_or_404(withdrawal_id)
    try:
        w.status       = "approved"
        w.processed_at = datetime.utcnow()
        db.session.commit()
        flash(f"Withdrawal of K{w.amount} for {w.user.phone} approved.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.withdrawals"))


@admin_bp.route("/withdrawals/<int:withdrawal_id>/decline", methods=["POST"])
@login_required
@admin_required
def decline_withdrawal(withdrawal_id):
    w = Withdrawal.query.get_or_404(withdrawal_id)
    try:
        # Refund balance
        w.user.balance = float(w.user.balance) + float(w.amount)
        w.status       = "declined"
        w.processed_at = datetime.utcnow()
        db.session.commit()
        flash(f"Withdrawal declined. K{w.amount} refunded to {w.user.phone}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.withdrawals"))


# ─────────────────────────────────────────────────────────────────
#  Recharge Methods (Payment Details)
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/payment-methods")
@login_required
@admin_required
def payment_methods():
    methods = RechargeMethod.query.order_by(RechargeMethod.id).all()
    return render_template("admin/payment_methods.html", methods=methods)


@admin_bp.route("/payment-methods/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_payment_method():
    if request.method == "POST":
        try:
            method = RechargeMethod(
                tab            = request.form["tab"].strip(),
                method_key     = request.form["method_key"].strip().lower(),
                display_name   = request.form["display_name"].strip(),
                operator       = request.form.get("operator", "").strip() or None,
                account_name   = request.form.get("account_name", "").strip() or None,
                account_number = request.form.get("account_number", "").strip() or None,
                code           = request.form.get("code", "").strip() or None,
                wallet_address = request.form.get("wallet_address", "").strip() or None,
                is_active      = "is_active" in request.form,
            )
            db.session.add(method)
            db.session.commit()
            flash(f"Payment method '{method.display_name}' created.", "success")
            return redirect(url_for("admin.payment_methods"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
    return render_template("admin/payment_method_form.html", method=None)


@admin_bp.route("/payment-methods/<int:method_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_payment_method(method_id):
    method = RechargeMethod.query.get_or_404(method_id)
    if request.method == "POST":
        try:
            method.tab            = request.form["tab"].strip()
            method.display_name   = request.form["display_name"].strip()
            method.operator       = request.form.get("operator", "").strip() or None
            method.account_name   = request.form.get("account_name", "").strip() or None
            method.account_number = request.form.get("account_number", "").strip() or None
            method.code           = request.form.get("code", "").strip() or None
            method.wallet_address = request.form.get("wallet_address", "").strip() or None
            method.is_active      = "is_active" in request.form
            db.session.commit()
            flash(f"Payment method '{method.display_name}' updated.", "success")
            return redirect(url_for("admin.payment_methods"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
    return render_template("admin/payment_method_form.html", method=method)


# ─────────────────────────────────────────────────────────────────
#  Income Logs
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/income")
@login_required
@admin_required
def income():
    income_type = request.args.get("type", "")
    query       = IncomeLog.query
    if income_type:
        query = query.filter_by(income_type=income_type)
    logs = query.order_by(IncomeLog.created_at.desc()).all()
    return render_template("admin/income.html", logs=logs, income_type=income_type)


@admin_bp.route("/income/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_income():
    if request.method == "POST":
        try:
            user = User.query.filter_by(phone=request.form["phone"].strip()).first()
            if not user:
                flash("User not found.", "error")
                return render_template("admin/add_income.html", users=User.query.all())
            amount = float(request.form["amount"])
            IncomeLog.create(
                user_id      = user.id,
                product_name = request.form.get("product_name", "Manual").strip(),
                amount       = amount,
                income_type  = request.form.get("income_type", "product"),
            )
            user.balance      = float(user.balance) + amount
            user.total_income = float(user.total_income) + amount
            db.session.commit()
            flash(f"K{amount} income added to {user.phone}.", "success")
            return redirect(url_for("admin.income"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
    return render_template("admin/add_income.html", users=User.query.all())


# ─────────────────────────────────────────────────────────────────
#  Gift Codes
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/gift-codes")
@login_required
@admin_required
def gift_codes():
    codes = GiftCode.query.order_by(GiftCode.created_at.desc()).all()
    return render_template("admin/gift_codes.html", codes=codes)


@admin_bp.route("/gift-codes/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_gift_code():
    if request.method == "POST":
        try:
            count  = int(request.form.get("count", 1))
            amount = float(request.form["amount"])
            for _ in range(count):
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
                db.session.add(GiftCode(code=code, amount=amount))
            db.session.commit()
            flash(f"{count} gift code(s) of K{amount} generated.", "success")
            return redirect(url_for("admin.gift_codes"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
    return render_template("admin/new_gift_code.html")


@admin_bp.route("/gift-codes/<int:code_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_gift_code(code_id):
    code = GiftCode.query.get_or_404(code_id)
    try:
        db.session.delete(code)
        db.session.commit()
        flash("Gift code deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.gift_codes"))


# ─────────────────────────────────────────────────────────────────
#  News
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/news")
@login_required
@admin_required
def news():
    all_news = News.query.order_by(News.published_at.desc()).all()
    return render_template("admin/news.html", news=all_news)


from app.cloudinary_helper import upload_news_image

@admin_bp.route("/news/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_news():
    if request.method == "POST":
        try:
            title = request.form["title"].strip()
            body  = request.form.get("body", "").strip()
            image_url = None

            # Handle image upload
            file = request.files.get("image")
            if file and file.filename:
                result    = upload_news_image(file, title)
                image_url = result["url"]

            item = News(
                title        = title,
                body         = body,
                image        = image_url,
                published_at = datetime.utcnow(),
            )
            db.session.add(item)
            db.session.commit()
            flash("News article created.", "success")
            return redirect(url_for("admin.news"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")

    return render_template("admin/news_form.html", item=None)


@admin_bp.route("/news/<int:news_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_news(news_id):
    item = News.query.get_or_404(news_id)
    if request.method == "POST":
        try:
            item.title = request.form["title"].strip()
            item.body  = request.form.get("body", "").strip()

            # Only replace image if a new file was uploaded
            file = request.files.get("image")
            if file and file.filename:
                result     = upload_news_image(file, item.title)
                item.image = result["url"]

            db.session.commit()
            flash("News article updated.", "success")
            return redirect(url_for("admin.news"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")

    return render_template("admin/news_form.html", item=item)

@admin_bp.route("/news/<int:news_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_news(news_id):
    item = News.query.get_or_404(news_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("News article deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin.news"))


# ─────────────────────────────────────────────────────────────────
#  Members / Referrals
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/members")
@login_required
@admin_required
def members():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/members.html", users=all_users)
