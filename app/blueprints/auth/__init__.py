from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.db import db
from app import login_manager

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # Already logged-in admin goes straight to dashboard
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
 
    if request.method == "POST":
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
 
        if not phone or not password:
            flash("Phone number and password are required.", "error")
            return render_template("auth/admin_login.html")
 
        user = User.authenticate(phone, password)
 
        if not user:
            flash("Invalid phone number or password.", "error")
            return render_template("auth/admin_login.html")
 
        if not user.is_admin:
            flash("You do not have admin access.", "error")
            return render_template("auth/admin_login.html")
 
        login_user(user)
        flash(f"Welcome back, {user.phone}.", "success")
        return redirect(url_for("admin.dashboard"))
 
    return render_template("auth/admin_login.html")



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()

        if not phone or not password:
            flash("Phone number and password are required.", "error")
            return render_template("auth/login.html")

        user = User.authenticate(phone, password)
        if user:
            login_user(user)
            return redirect(url_for("dashboard.home"))

        flash("Invalid phone number or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        phone            = request.form.get("phone", "").strip()
        password         = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # ── Validation ────────────────────────────────────────────
        if not phone or not password:
            flash("Phone number and password are required.", "error")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(phone=phone).first():
            flash("An account with this phone number already exists.", "error")
            return render_template("auth/register.html")

        # ── Store to database ─────────────────────────────────────
        try:
            user = User(phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            flash("Something went wrong. Please try again.", "error")
            return render_template("auth/register.html")

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))