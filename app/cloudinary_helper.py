import cloudinary
import cloudinary.uploader
from flask import current_app


def init_cloudinary():
    """Configure Cloudinary using app config values."""
    cloudinary.config(
        cloud_name = current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key    = current_app.config["CLOUDINARY_API_KEY"],
        api_secret = current_app.config["CLOUDINARY_API_SECRET"],
        secure     = True,
    )


def upload_voucher(file, order_number: str) -> dict:
    """
    Upload a transfer voucher image to Cloudinary under the
    'eonsystem/vouchers' folder.

    Args:
        file:         A Flask FileStorage object (from request.files).
        order_number: The recharge order number — used as the public_id
                      so each upload is uniquely named and overwritable.

    Returns:
        dict with keys:
            url        — secure HTTPS URL of the uploaded image
            public_id  — Cloudinary public_id for future reference/deletion
    
    Raises:
        Exception if the upload fails.
    """
    init_cloudinary()

    result = cloudinary.uploader.upload(
        file,
        folder            = "eonsystem/vouchers",   # separate folder in Cloudinary
        public_id         = f"voucher_{order_number}",
        overwrite         = True,                   # replace if resubmitted
        resource_type     = "image",
        allowed_formats   = ["jpg", "jpeg", "png", "webp"],
        transformation    = [
            {"quality": "auto"},                    # auto-compress
            {"fetch_format": "auto"},               # serve best format per browser
        ],
    )

    return {
        "url":       result["secure_url"],
        "public_id": result["public_id"],
    }


def upload_news_image(file, title: str) -> dict:
    """
    Upload a news article image to Cloudinary under the
    'eonsystem/news' folder.

    Args:
        file:  A Flask FileStorage object (from request.files).
        title: The article title — used to build a clean public_id.

    Returns:
        dict with keys:
            url        — secure HTTPS URL of the uploaded image
            public_id  — Cloudinary public_id for future reference/deletion

    Raises:
        Exception if the upload fails.
    """
    import re
    init_cloudinary()

    # Build a slug from the title e.g. "E.ON Expands Wind" -> "eon_expands_wind"
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:60]

    result = cloudinary.uploader.upload(
        file,
        folder          = "eonsystem/news",
        public_id       = f"news_{slug}",
        overwrite       = True,
        resource_type   = "image",
        allowed_formats = ["jpg", "jpeg", "png", "webp"],
        transformation  = [
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )

    return {
        "url":       result["secure_url"],
        "public_id": result["public_id"],
    }


def upload_product_image(file, product_name: str) -> dict:
    """
    Upload a product image to Cloudinary under the 'eonsystem/products' folder.
    """
    import re
    init_cloudinary()

    slug = re.sub(r'[^a-z0-9]+', '_', product_name.lower()).strip('_')[:60]

    result = cloudinary.uploader.upload(
        file,
        folder          = "eonsystem/products",
        public_id       = f"product_{slug}",
        overwrite       = True,
        resource_type   = "image",
        allowed_formats = ["jpg", "jpeg", "png", "webp"],
        transformation  = [
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )
    return {
        "url":       result["secure_url"],
        "public_id": result["public_id"],
    }