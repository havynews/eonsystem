from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import NEWS, News, Product
from app.db import db
from datetime import date


dashboard_bp = Blueprint("dashboard", __name__)



def format_transactions(user):
    transactions = []

    # Recharge Orders
    for order in user.recharge_orders:
        transactions.append({
            "type": "recharge",
            "title": "Recharge balance",
            "amount": float(order.amount),
            "status": order.status,
            "created_at": order.created_at
        })

    # Withdrawals
    for withdrawal in user.withdrawals:
        transactions.append({
            "type": "withdrawal",
            "title": "Withdrawal",
            "amount": float(withdrawal.amount),
            "status": withdrawal.status,
            "created_at": withdrawal.requested_at
        })

    # Sort by newest first
    transactions.sort(key=lambda x: x["created_at"], reverse=True)

    return transactions


@dashboard_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/home")
@login_required
def home():
    news = News.get_latest(limit=6)
    products = Product.get_all()
    return render_template("dashboard/home.html", news=news, products=products, user=current_user)


from app.models import RechargeMethod, RechargeOrder
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_voucher_to_cloudinary(file, order_number):
    if not file or file.filename == '':
        raise ValueError("No file selected")

    if not allowed_file(file.filename):
        raise ValueError("Invalid file type")

    filename = secure_filename(file.filename)

    result = cloudinary.uploader.upload(
        file,
        folder=f"texting_app/vouchers/{order_number}",
        public_id=os.path.splitext(filename)[0],  # clean name
        overwrite=True  # replace if re-uploaded
    )

    return result.get("secure_url")


from app.cloudinary_helper import upload_voucher

@dashboard_bp.route("/recharge/order/<order_number>", methods=["GET", "POST"])
@login_required
def recharge_order(order_number):
    order  = RechargeOrder.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    method = RechargeMethod.get_by_key(order.method_key)

    qr_url = None
    if order.tab == 'usdt' and method:
        qr_url = url_for("share.generate_qr", code=method.method_key)

    if request.method == "POST":
        file = request.files.get("voucher")

        if not file or file.filename == "":
            flash("Please select a voucher image to upload.", "error")
            return render_template("dashboard/recharge_order.html", order=order, method=method, qr_url=qr_url, user=current_user)

        try:
            # Upload to Cloudinary eonsystem/vouchers folder
            result = upload_voucher(file, order.order_number)

            order.voucher_image = result["url"]       # store the Cloudinary URL
            order.status        = "submitted"
            db.session.commit()

            flash("Recharge submitted successfully! Awaiting confirmation.", "success")
            return redirect(url_for("dashboard.home"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Cloudinary upload error: {e}")
            flash("Failed to upload voucher. Please try again.", "error")

    return render_template("dashboard/recharge_order.html", order=order, method=method, qr_url=qr_url, user=current_user)



@dashboard_bp.route("/recharge", methods=["GET", "POST"])
@login_required
def recharge():
    if request.method == "POST":
        amount     = request.form.get("amount", "").strip()
        method_key = request.form.get("method", "").strip()
        tab        = request.form.get("tab", "bank").strip()

        if not amount:
            flash("Please select or enter an amount.", "error")
            return render_template("dashboard/recharge.html", user=current_user)

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid amount.", "error")
            return render_template("dashboard/recharge.html", user=current_user)

        if not method_key:
            flash("Please select a recharge method.", "error")
            return render_template("dashboard/recharge.html", user=current_user)

        method = RechargeMethod.get_by_key(method_key)
        if not method:
            flash("Invalid recharge method.", "error")
            return render_template("dashboard/recharge.html", user=current_user)

        # Create the order and redirect to confirmation page
        try:
            order = RechargeOrder.create(
                user_id    = current_user.id,
                amount     = amount_float,
                tab        = tab,
                method_key = method_key,
            )
            return redirect(url_for("dashboard.recharge_order", order_number=order.order_number))
        except Exception as e:
            flash("Something went wrong. Please try again.", "error")
            return render_template("dashboard/recharge.html", user=current_user)

    return render_template("dashboard/recharge.html", user=current_user)


# @dashboard_bp.route("/recharge/order/<order_number>", methods=["GET", "POST"])
# @login_required
# def recharge_order(order_number):
#     order  = RechargeOrder.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
#     method = RechargeMethod.get_by_key(order.method_key)

#     qr_url = None
#     if order.tab == 'usdt' and method:
#         qr_url = url_for("share.generate_qr", code=method.method_key)

#     if request.method == "POST":
#         # Handle voucher upload
#         file = request.files.get("voucher")
#         if file and allowed_file(file.filename):
#             filename  = secure_filename(f"{order.order_number}_{file.filename}")
#             save_path = os.path.join("app", "static", "uploads", filename)
#             os.makedirs(os.path.dirname(save_path), exist_ok=True)
#             file.save(save_path)
#             try:
#                 order.voucher_image = filename
#                 order.status        = "submitted"
#                 db.session.commit()
#                 flash("Recharge submitted successfully! Awaiting confirmation.", "success")
#                 return redirect(url_for("dashboard.home"))
#             except Exception as e:
#                 db.session.rollback()
#                 flash("Error uploading voucher. Please try again.", "error")
#         else:
#             flash("Please upload a valid image (PNG or JPG).", "error")

#     return render_template(
#         "dashboard/recharge_order.html",
#         order  = order,
#         method = method,
#         user   = current_user,
#         qr_url = qr_url
#     )




@dashboard_bp.route('/members')
@login_required
def members():
    user = current_user

    level1_users = user.get_level_1()
    level2_users = user.get_level_2()
    level3_users = user.get_level_3()

    level1 = user.get_level_stats(level1_users)
    level2 = user.get_level_stats(level2_users)
    level3 = user.get_level_stats(level3_users)

    total_members = (
        len(level1_users) +
        len(level2_users) +
        len(level3_users)
    )

    return render_template(
        'dashboard/members.html',
        total_members=total_members,
        total_income=float(user.total_income),
        level1=level1,
        level2=level2,
        level3=level3
    )


@dashboard_bp.route('/billing')
@login_required
def billing():
    user = current_user

    transactions = format_transactions(user)

    # Separate tabs
    recharge_tx = [t for t in transactions if t["type"] == "recharge"]
    withdrawal_tx = [t for t in transactions if t["type"] == "withdrawal"]

    return render_template(
        'dashboard/billing.html',
        recharge_tx=recharge_tx,
        withdrawal_tx=withdrawal_tx
    )