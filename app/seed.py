from app.db import db
from app.models import Product, News, User, RechargeMethod
from datetime import datetime
import os


def upload_seed_image(filename: str, folder: str, public_id: str) -> str | None:
    """
    Upload a local static image to Cloudinary during seeding.
    Returns the Cloudinary URL or None if file not found or upload fails.

    Args:
        filename:  The image filename (e.g. 'solar.png')
        folder:    Cloudinary folder (e.g. 'eonsystem/products')
        public_id: Cloudinary public_id (e.g. 'product_solar_panel_pro')
    """
    import cloudinary
    import cloudinary.uploader
    from flask import current_app

    # Configure Cloudinary
    cloudinary.config(
        cloud_name = current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key    = current_app.config["CLOUDINARY_API_KEY"],
        api_secret = current_app.config["CLOUDINARY_API_SECRET"],
        secure     = True,
    )

    # Resolve local file path
    base_dir   = os.path.abspath(os.path.dirname(__file__))
    local_path = os.path.join(base_dir, "static", "images", filename)

    if not os.path.exists(local_path):
        print(f"[seed] Warning: Image not found locally, skipping upload: {local_path}")
        return None

    try:
        result = cloudinary.uploader.upload(
            local_path,
            folder          = folder,
            public_id       = public_id,
            overwrite       = True,
            resource_type   = "image",
            allowed_formats = ["jpg", "jpeg", "png", "webp"],
            transformation  = [
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )
        url = result["secure_url"]
        print(f"[seed] Uploaded '{filename}' → {url}")
        return url
    except Exception as e:
        print(f"[seed] Cloudinary upload failed for '{filename}': {e}")
        return None


def seed_invitation_codes():
    """Generate invitation codes for all users that don't have one yet."""
    users_without_code = User.query.filter(
        (User.invitation_code == None) | (User.invitation_code == '')
    ).all()

    if not users_without_code:
        print("[seed] All users already have invitation codes.")
        return

    updated = 0
    for user in users_without_code:
        try:
            user.get_invitation_code()
            updated += 1
            print(f"[seed] Generated invitation code '{user.invitation_code}' for user {user.phone}")
        except Exception as e:
            db.session.rollback()
            print(f"[seed] Error generating code for user {user.phone}: {e}")

    print(f"[seed] Invitation codes generated for {updated} user(s).")


def run_seeds():
    """Insert or update default products, news, and recharge methods."""

    import re
    def slugify(text):
        return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:60]

    # ── Products ──────────────────────────────────────────────────
    default_products = [
        dict(name='Solar Panel Pro',     description='High-efficiency monocrystalline solar panel system.',                    price=50,  daily_income=1.95, total_income=58.5,   rental_days=30,  image='solar.png',        vip_level=None),
        dict(name='Wind Turbine Mini',   description='Compact offshore wind turbine energy package.',                          price=100, daily_income=3.50, total_income=210.0,  rental_days=60,  image='wind_news.jpg',    vip_level=None),
        dict(name='Green Energy Bundle', description='Combined solar + wind energy rental bundle.',                            price=200, daily_income=8.00, total_income=720.0,  rental_days=90,  image='bundle.jpg',       vip_level=None),
        dict(name='E.ON Starter Pack',   description='Entry-level E.ON energy investment product.',                            price=30,  daily_income=1.10, total_income=22.0,   rental_days=20,  image='starter.jpg',      vip_level=None),
        dict(name='SYMN144TBD A1',       description='High-capacity solar panel with advanced photovoltaic technology.',       price=100, daily_income=12.0, total_income=180.0,  rental_days=15,  image='solar_panel.jpg',  vip_level=1),
        dict(name='Lithium-ion N100',    description='Advanced lithium-ion battery storage system for renewable energy.',      price=200, daily_income=3.9,  total_income=1423.5, rental_days=365, image='lithium_n100.jpg', vip_level=1),
        dict(name='Medium',              description='Medium-scale solar energy solution for residential and commercial use.', price=250, daily_income=9.25, total_income=5087.5, rental_days=550, image='medium_solar.jpg', vip_level=2),
    ]

    for data in default_products:
        product = Product.query.filter_by(name=data['name']).first()

        # Upload image to Cloudinary (always attempt so URL stays fresh)
        image_url = None
        if data.get('image'):
            image_url = upload_seed_image(
                filename  = data['image'],
                folder    = "eonsystem/products",
                public_id = f"product_{slugify(data['name'])}",
            )

        if not product:
            new_product = Product(
                name         = data['name'],
                description  = data['description'],
                price        = data['price'],
                daily_income = data['daily_income'],
                total_income = data['total_income'],
                rental_days  = data['rental_days'],
                image        = image_url,
                vip_level    = data.get('vip_level'),
                is_active    = True,
            )
            db.session.add(new_product)
            print(f"[seed] Created product: {data['name']}")

        else:
            # Update fields
            product.description  = data['description']
            product.price        = data['price']
            product.daily_income = data['daily_income']
            product.total_income = data['total_income']
            product.rental_days  = data['rental_days']
            product.vip_level    = data.get('vip_level')
            product.is_active    = True

            # Only replace image if Cloudinary upload succeeded
            if image_url:
                product.image = image_url

            print(f"[seed] Updated product: {data['name']}")

    # ── News ──────────────────────────────────────────────────────
    default_news = [
        dict(title='What is solar technology? (E.ON)',                  image='solar_panel.jpg', published_at=datetime(2025, 11, 6, 17, 15, 11)),
        dict(title='E.ON expands offshore wind into two new markets.',  image='wind_news.jpg',   published_at=datetime(2025, 11, 6, 17,  8, 32)),
        dict(title='About E.ON System',                                 image='eonimage.png',    published_at=datetime(2025, 11, 4, 10,  0,  0)),
    ]

    for data in default_news:
        news = News.query.filter_by(title=data['title']).first()

        # Upload news image to Cloudinary
        image_url = None
        if data.get('image'):
            image_url = upload_seed_image(
                filename  = data['image'],
                folder    = "eonsystem/news",
                public_id = f"news_{slugify(data['title'])}",
            )

        if not news:
            news_data = {
                'title':        data['title'],
                'image':        image_url,
                'published_at': data['published_at'],
                'body':         f"Article about {data['title']}",
            }
            db.session.add(News(**news_data))
            print(f"[seed] Created news: {data['title']}")

        else:
            news.published_at = data['published_at']
            if image_url:
                news.image = image_url
            print(f"[seed] Updated news: {data['title']}")

    # ── Invitation Codes ──────────────────────────────────────────
    seed_invitation_codes()

    # ── Recharge Methods ──────────────────────────────────────────
    default_methods = [
        dict(tab='bank', method_key='bsp',   display_name='BSP Bank',
             operator='BSP',  account_name='E.ON BSP',
             account_number='0001057366', code='088-342'),
        dict(tab='bank', method_key='kina',  display_name='Kina Bank',
             operator='Kina', account_name='E.ON Kina',
             account_number='0009876543', code='055-119'),
        dict(tab='usdt', method_key='trc20', display_name='TRC20',
             wallet_address='TJaFARRXYuWCtK4VaLg8fAfMWRCyRna...'),
        dict(tab='usdt', method_key='erc20', display_name='ERC20',
             wallet_address='0x1234abcd5678efgh...'),
    ]

    for data in default_methods:
        exists = RechargeMethod.query.filter_by(method_key=data['method_key']).first()
        if not exists:
            db.session.add(RechargeMethod(**data))
            print(f"[seed] Created recharge method: {data['display_name']}")

    # ── Commit ────────────────────────────────────────────────────
    try:
        db.session.commit()
        print("[seed] Seeding completed successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"[seed] Error: {e}")
        raise