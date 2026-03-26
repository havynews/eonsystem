from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import qrcode
import io


share_bp = Blueprint("share", __name__)


@share_bp.route("/")
@login_required
def share():
    invitation_code  = current_user.get_invitation_code()
    valid_members    = current_user.get_valid_members()
    members_required = 3

    return render_template(
        "share/share.html",
        user             = current_user,
        invitation_code  = invitation_code,
        valid_members    = valid_members,
        members_required = members_required,
    )



@share_bp.route("/qrcode/<code>")
@login_required
def generate_qr(code):
    """Generate a QR code image for the given invitation code and return it as PNG."""
    # Build the registration URL with the code pre-filled
    invite_url = url_for("auth.register", referral_code=code, _external=True)

    qr = qrcode.QRCode(
        version      = 1,
        error_correction = qrcode.constants.ERROR_CORRECT_H,
        box_size     = 10,
        border       = 2,
    )
    qr.add_data(invite_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png")