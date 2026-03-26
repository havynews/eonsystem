from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import GiftCode, IncomeLog

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/")
@login_required
def profile():
    return render_template("profile/profile.html", user=current_user)


@profile_bp.route("/share")
@login_required
def share():
    return render_template("profile/share.html", user=current_user)


@profile_bp.route("/support")
@login_required
def support():
    return render_template("profile/support.html", user=current_user)


@profile_bp.route("/billing")
@login_required
def billing():
    return render_template("dashboard/billing.html", user=current_user)


@profile_bp.route('/bank', methods=['GET', 'POST'])
@login_required
def bank():
    user = current_user

    if request.method == 'POST':
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        name = request.form.get('name')
        bank_code = request.form.get('bank_code')

        # 🔒 Validation
        if not bank_name or not account_number or not name:
            flash('Please fill all required fields', 'error')
            return redirect(url_for('profile.bank'))

        try:
            # ✅ Save to database
            user.bank_name = bank_name
            user.account_number = account_number
            user.name = name
            user.bank_code = bank_code

            db.session.commit()

            flash('Bank details updated successfully!', 'success')

        except Exception as e:
            db.session.rollback()
            flash('Something went wrong', 'error')

        return redirect(url_for('profile.bank'))

    return render_template('profile/bank.html')



@profile_bp.route('/gift-code', methods=['GET', 'POST'])
@login_required
def gift_code():
    if request.method == 'POST':
        code_input = request.form.get('gift_code')

        if not code_input:
            flash('Please enter a gift code', 'error')
            return redirect(url_for('profile.gift_code'))

        # 🔍 Find code
        gift = GiftCode.query.filter_by(code=code_input.strip()).first()

        if not gift:
            flash('Invalid gift code', 'error')
            return redirect(url_for('profile.gift_code'))

        if gift.is_used:
            flash('This code has already been used', 'error')
            return redirect(url_for('profile.gift_code'))

        try:
            # 💰 Credit user
            current_user.balance += gift.amount
            current_user.total_income += gift.amount

            # 🔒 Mark as used
            gift.is_used = True
            gift.used_by = current_user.id
            gift.used_at = datetime.utcnow()

            db.session.commit()

            flash(f'Success! You received {gift.amount}', 'success')

        except Exception as e:
            db.session.rollback()
            flash('Something went wrong', 'error')

        return redirect(url_for('profile.gift_code'))

    return render_template('profile/gift_code.html')


@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = current_user

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 🔒 Validation
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('profile.change_password'))

        # Check old password
        if not user.check_password(old_password):
            flash('Old password is incorrect', 'error')
            return redirect(url_for('profile.change_password'))

        # Check match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('profile.change_password'))

        # Password strength (basic)
        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('profile.change_password'))

        try:
            # 🔐 Update password
            user.set_password(new_password)
            db.session.commit()

            flash('Password updated successfully!', 'success')

        except Exception:
            db.session.rollback()
            flash('Something went wrong', 'error')

        return redirect(url_for('profile.change_password'))

    return render_template('profile/change_password.html')



@profile_bp.route("/income")
@login_required
def income():
    from app.models import IncomeLog
    product_income = IncomeLog.get_product_income(current_user.id)
    commissions    = IncomeLog.get_commissions(current_user.id)
    return render_template(
        "profile/income.html",
        user           = current_user,
        product_income = product_income,
        commissions    = commissions,
    )