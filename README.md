# E.ON System — Flask Blueprint App

A multi-page web app built from the E.ON-System mobile screenshots, using Python Flask (blueprints), Tailwind CSS, and vanilla JS.

---

## Project Structure

```
eonsystem/
├── run.py                          # App entry point
├── requirements.txt
└── app/
    ├── __init__.py                 # App factory (create_app)
    ├── models.py                   # Mock data + User model (replace with DB)
    ├── templates/
    │   ├── base.html               # Shared layout + bottom nav
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── register.html
    │   ├── dashboard/
    │   │   └── home.html
    │   ├── products/
    │   │   ├── products.html
    │   │   ├── detail.html
    │   │   └── my_products.html
    │   ├── profile/
    │   │   ├── profile.html
    │   │   ├── share.html
    │   │   ├── support.html
    │   │   └── billing.html
    │   └── withdrawal/
    │       └── withdrawal.html
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── images/
    └── blueprints/
        ├── auth/__init__.py        # /auth/login, /auth/register, /auth/logout
        ├── dashboard/__init__.py   # / and /home
        ├── products/__init__.py    # /products/, /products/<id>, /products/my-products
        ├── profile/__init__.py     # /profile/, /profile/share, /profile/support
        └── withdrawal/__init__.py  # /withdrawal/
```

---

## Setup & Run

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# mac os
source venv/bin/activate        

# Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python run.py
```

Visit: http://localhost:5000

---

## Demo Login

| Field    | Value       |
|----------|-------------|
| Phone    | 747430966   |
| Password | password123 |

---

## Pages & Routes

| Route                      | Blueprint    | Description              |
|----------------------------|--------------|--------------------------|
| `/auth/login`              | auth         | Login page               |
| `/auth/register`           | auth         | Registration page        |
| `/auth/logout`             | auth         | Logout                   |
| `/home`                    | dashboard    | Home with news feed      |
| `/products/`               | products     | Product listings         |
| `/products/<id>`           | products     | Product detail + buy     |
| `/products/my-products`    | products     | User's purchased products|
| `/profile/`                | profile      | Profile / Me page        |
| `/profile/share`           | profile      | Share via WhatsApp/TG    |
| `/profile/support`         | profile      | Customer service         |
| `/profile/billing`         | profile      | Billing history          |
| `/withdrawal/`             | withdrawal   | Withdrawal form          |

---

## Next Steps (Production Upgrades)

- Replace mock `USERS`/`PRODUCTS` in `models.py` with SQLAlchemy + a real database
- Add Flask-WTF for CSRF-protected forms
- Add Flask-Bcrypt for password hashing
- Add a real captcha integration (e.g. hCaptcha)
- Connect a payment/recharge gateway
- Deploy behind Gunicorn + Nginx

# eonsystem
simple eonsystem clone
