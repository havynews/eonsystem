from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Product, Withdrawal

withdrawal_bp = Blueprint("withdrawal", __name__)



from decimal import Decimal, InvalidOperation

@withdrawal_bp.route("/", methods=["GET", "POST"])
@login_required
def withdrawal():
    if request.method == "POST":
        print(request.form)

        amount = request.form.get("amount", "").strip()
        password = request.form.get("password", "").strip()

        print("RAW amount:", repr(amount))  # DEBUG

        try:
            amount_decimal = Decimal(str(float(amount)))

            if amount_decimal < Decimal("70"):
                flash("Minimum withdrawal amount is K70.", "error")

            elif amount_decimal > current_user.balance:
                flash("Insufficient balance.", "error")

            else:
                Withdrawal.create(current_user.id, amount_decimal)

                flash(f"Withdrawal of K{amount_decimal} submitted and pending approval.", "success")
                return redirect(url_for("profile.profile"))

        except (InvalidOperation, ValueError):
            flash("Please enter a valid amount.", "error")

    return render_template("withdrawal/withdrawal.html", user=current_user)