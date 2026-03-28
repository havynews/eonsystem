from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import PRODUCTS, USER_PRODUCTS, Product
from app.models import Product, UserProduct, IncomeLog
from app.db import db
from decimal import Decimal
from sqlalchemy import text
from datetime import datetime, date, timedelta



products_bp = Blueprint("products", __name__)



@products_bp.route("/")
@login_required
def products():
    all_products = Product.query.order_by(Product.id).all()
    return render_template("products/products.html", products=all_products, user=current_user)


@products_bp.route("/my-products")
@login_required
def my_products():
    user_products = UserProduct.get_by_user(current_user.id)

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    return render_template(
        "products/my_products.html",
        user_products=user_products,
        user=current_user,
        today=today,
        today_start=today_start
    )


@products_bp.route("/<int:product_id>")
@login_required
def product_detail(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        return redirect(url_for("products.products"))
    return render_template("products/detail.html", product=product, user=current_user)


@products_bp.route("/buy/<int:product_id>", methods=["POST"])
@login_required
def buy_product(product_id):
    product = Product.get_by_id(product_id)

    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products.products"))

    if float(current_user.balance) < float(product.price):
        flash("Insufficient balance to purchase this product.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

    try:
        # Deduct balance
        current_user.balance = Decimal(current_user.balance) - Decimal(product.price)

        # Correct expiry calculation
        expiry = date.today() + timedelta(days=product.rental_days)

        purchase = UserProduct(
            user_id=current_user.id,
            product_id=product.id,
            daily_income=product.daily_income,
            expiry_date=expiry,
        )

        db.session.add(purchase)
        db.session.commit()

        flash(f"Successfully purchased {product.name}!", "success")
        return redirect(url_for("products.my_products"))

    except Exception as e:
        db.session.rollback()
        print(e)  # 👈 ADD THIS for debugging
        flash("Purchase failed. Please try again.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

@products_bp.route("/receive/<int:user_product_id>", methods=["POST"])
@login_required
def receive_income(user_product_id):
    purchase = UserProduct.query.filter_by(
        id      = user_product_id,
        user_id = current_user.id,
    ).first_or_404()

    today = date.today()

    # ── Already received today? ───────────────────────────────────
    already_received = IncomeLog.query.filter(
        IncomeLog.user_id     == current_user.id,
        IncomeLog.income_type == 'product',
        db.func.date(IncomeLog.created_at) == today,
        IncomeLog.product_name == purchase.product.name,
    ).first()

    if already_received:
        flash("You have already received income for this product today.", "error")
        return redirect(url_for("products.my_products"))

    # ── Product expired? ──────────────────────────────────────────
    if purchase.expiry_date < today:
        flash("This product has expired.", "error")
        return redirect(url_for("products.my_products"))

    # ── Credit income ─────────────────────────────────────────────
    try:
        amount = float(purchase.daily_income)

        # Update purchase running total
        purchase.current_total_income = float(purchase.current_total_income) + amount

        # Credit user balance and total income
        current_user.balance      = float(current_user.balance) + amount
        current_user.total_income = float(current_user.total_income) + amount

        # Log it
        IncomeLog.create(
            user_id      = current_user.id,
            product_name = purchase.product.name,
            amount       = amount,
            income_type  = 'product',
        )

        db.session.commit()
        flash(f"K{amount:.2f} received successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash("Failed to receive income. Please try again.", "error")

    return redirect(url_for("products.my_products"))


