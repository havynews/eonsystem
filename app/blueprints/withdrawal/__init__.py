from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

withdrawal_bp = Blueprint("withdrawal", __name__)


@withdrawal_bp.route("/", methods=["GET", "POST"])
@login_required
def withdrawal():
    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        password = request.form.get("password", "").strip()
        try:
            amount_float = float(amount)
            if amount_float < 70:
                flash("Minimum withdrawal amount is K70.", "error")
            elif amount_float > current_user.balance:
                flash("Insufficient balance.", "error")
            else:
                flash(f"Withdrawal of K{amount_float} submitted successfully.", "success")
                return redirect(url_for("profile.profile"))
        except ValueError:
            flash("Please enter a valid amount.", "error")
    return render_template("withdrawal/withdrawal.html", user=current_user)
