from flask_login import UserMixin

# Mock in-memory data store (replace with a real DB in production)
USERS = {
    "747430966": {
        "id": "747430966",
        "phone": "747430966",
        "password": "password123",
        "vip_level": "VIP-0",
        "balance": 6.36,
        "total_income": 3.9,
        "agent_privileges": True,
    }
}

PRODUCTS = [
    {
        "id": 1,
        "name": "Solar Panel Pro",
        "price": 50,
        "daily_income": 1.95,
        "rental_days": 30,
        "image": "solar.png",
        "description": "High-efficiency monocrystalline solar panel system.",
        "total_income": 58.5,
    },
    {
        "id": 2,
        "name": "Wind Turbine Mini",
        "price": 100,
        "daily_income": 3.5,
        "rental_days": 60,
        "image": "wind.png",
        "description": "Compact offshore wind turbine energy package.",
        "total_income": 210,
    },
    {
        "id": 3,
        "name": "Green Energy Bundle",
        "price": 200,
        "daily_income": 8.0,
        "rental_days": 90,
        "image": "bundle.png",
        "description": "Combined solar + wind energy rental bundle.",
        "total_income": 720,
    },
    {
        "id": 4,
        "name": "E.ON Starter Pack",
        "price": 30,
        "daily_income": 1.1,
        "rental_days": 20,
        "image": "starter.png",
        "description": "Entry-level E.ON energy investment product.",
        "total_income": 22,
    },
]

USER_PRODUCTS = [
    {
        "product_id": 1,
        "name": "Solar Panel Pro",
        "price": 50,
        "rental_date": "24/11/2025",
        "daily_income": 1.95,
        "current_total_income": 3.9,
        "remaining": "0d:00h:00m:00s",
    }
]

NEWS = [
    {
        "id": 1,
        "title": "What is solar technology? (E.ON)",
        "date": "06/11/25 17:15:11",
        "image": "solar_news.jpg",
    },
    {
        "id": 2,
        "title": "E.ON expands offshore wind into two new markets.",
        "date": "06/11/25 17:08:32",
        "image": "wind_news.jpg",
    },
    {
        "id": 3,
        "title": "About E.ON System",
        "date": "04/11/25 10:00:00",
        "image": "about_news.jpg",
    },
]


# class User(UserMixin):
#     def __init__(self, data):
#         self.id = data["id"]
#         self.phone = data["phone"]
#         self.vip_level = data["vip_level"]
#         self.balance = data["balance"]
#         self.total_income = data["total_income"]
#         self.agent_privileges = data["agent_privileges"]

#     @staticmethod
#     def get(user_id):
#         data = USERS.get(user_id)
#         return User(data) if data else None

#     @staticmethod
#     def authenticate(phone, password):
#         data = USERS.get(phone)
#         if data and data["password"] == password:
#             return User(data)
#         return None


from datetime import datetime, date
from flask_login import UserMixin
import bcrypt
from app.db import db


# ─────────────────────────────────────────────────────────────────
#  User
# ─────────────────────────────────────────────────────────────────

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,      primary_key=True)
    phone         = db.Column(db.String(20),   nullable=False, unique=True)
    password_hash = db.Column(db.String(255),  nullable=False)
    bank_name = db.Column(db.String(255),  nullable=True)
    account_number = db.Column(db.String(255),  nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(255),  nullable=True)
    bank_code = db.Column(db.String(255),  nullable=True)
    vip_level     = db.Column(db.String(20),   nullable=False, default='VIP-0')
    balance       = db.Column(db.Numeric(12,2), nullable=False, default=0.00)
    total_income  = db.Column(db.Numeric(12,2), nullable=False, default=0.00)
    agent         = db.Column(db.Boolean,       nullable=False, default=False)
    created_at    = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)

    # ── Referral ──────────────────────────────────────────────────
    invitation_code = db.Column(db.String(10),  nullable=True, unique=True)
    referred_by     = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=True)

    # Relationships
    purchases     = db.relationship('UserProduct', backref='user',    lazy=True)
    withdrawals   = db.relationship('Withdrawal',  backref='user',    lazy=True)
    referrals     = db.relationship('User',        backref=db.backref('referrer', remote_side='User.id'), lazy=True, foreign_keys='User.referred_by')

    # ── Invitation code generator ─────────────────────────────────
    def generate_invitation_code(self):
        """Generate and save a unique 6-char invitation code for this user."""
        import random, string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            exists = User.query.filter_by(invitation_code=code).first()
            if not exists:
                self.invitation_code = code
                db.session.commit()
                break
        return self.invitation_code

    def get_invitation_code(self):
        """Return existing code or generate one if not set yet."""
        if not self.invitation_code:
            return self.generate_invitation_code()
        return self.invitation_code

    def get_valid_members(self):
        """Count how many users registered using this user's invitation code."""
        return User.query.filter_by(referred_by=self.id).count()

    def get_level_1(self):
        return self.referrals


    def get_level_2(self):
        level_2 = []
        for user in self.get_level_1():
            level_2.extend(user.referrals)
        return level_2


    def get_level_3(self):
        level_3 = []
        for user in self.get_level_2():
            level_3.extend(user.referrals)
        return level_3

    def get_level_stats(self, users):
        return {
            "subordinates": len(users),
            "active": sum(1 for u in users if float(u.balance) > 0),
            "lease": float(sum(u.balance for u in users)),
            "commission": float(sum(u.total_income for u in users))
        }
    # ── Password helpers ─────────────────────────────────────────

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()
        ).decode()

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode(), self.password_hash.encode()
        )

    # ── Auth ─────────────────────────────────────────────────────

    @staticmethod
    def authenticate(phone, password):
        """Return User if credentials are valid, else None."""
        user = User.query.filter_by(phone=phone).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def create(phone, password):
        """Create, persist, and return a new User."""
        try:
            user = User(phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    # ── Writes ───────────────────────────────────────────────────

    def update_balance(self, new_balance):
        try:
            self.balance = new_balance
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def __repr__(self):
        return f'<User {self.phone}>'


# ─────────────────────────────────────────────────────────────────
#  Product
# ─────────────────────────────────────────────────────────────────

class Product(db.Model):
    __tablename__ = 'products'

    id           = db.Column(db.Integer,       primary_key=True)
    name         = db.Column(db.String(100),   nullable=False)
    description  = db.Column(db.Text)
    price        = db.Column(db.Numeric(12,2), nullable=False)
    daily_income = db.Column(db.Numeric(12,2), nullable=False)
    total_income = db.Column(db.Numeric(12,2), nullable=False)
    rental_days  = db.Column(db.Integer,       nullable=False)
    image        = db.Column(db.String(255))
    vip_level = db.Column(db.Integer, nullable=True)  # 1, 2, 3, etc.
    is_active    = db.Column(db.Boolean,       nullable=False, default=True)
    created_at   = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)

    # Relationships
    purchases    = db.relationship('UserProduct', backref='product', lazy=True)

    @staticmethod
    def get_all():
        return Product.query.filter_by(is_active=True).order_by(Product.id).all()

    @staticmethod
    def get_by_id(product_id):
        return Product.query.filter_by(id=product_id, is_active=True).first()

    def __repr__(self):
        return f'<Product {self.name}>'


# ─────────────────────────────────────────────────────────────────
#  UserProduct  (purchases)
# ─────────────────────────────────────────────────────────────────

class UserProduct(db.Model):
    __tablename__ = 'user_products'

    id                   = db.Column(db.Integer,       primary_key=True)
    user_id              = db.Column(db.Integer,       db.ForeignKey('users.id'),    nullable=False)
    product_id           = db.Column(db.Integer,       db.ForeignKey('products.id'), nullable=False)
    rental_date          = db.Column(db.Date,          nullable=False, default=date.today)
    expiry_date          = db.Column(db.Date,          nullable=False)
    daily_income         = db.Column(db.Numeric(12,2), nullable=False)
    current_total_income = db.Column(db.Numeric(12,2), nullable=False, default=0.00)
    is_active            = db.Column(db.Boolean,       nullable=False, default=True)
    purchased_at         = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)

    @staticmethod
    def get_by_user(user_id):
        return (
            UserProduct.query
            .filter_by(user_id=user_id, is_active=True)
            .order_by(UserProduct.purchased_at.desc())
            .all()
        )

    @staticmethod
    def create(user_id, product_id, daily_income, rental_days):
        try:
            expiry = date.today().replace(day=date.today().day + rental_days)
            purchase = UserProduct(
                user_id      = user_id,
                product_id   = product_id,
                daily_income = daily_income,
                expiry_date  = expiry,
            )
            db.session.add(purchase)
            db.session.commit()
            return purchase
        except Exception as e:
            db.session.rollback()
            raise e

    def receive_income(self, amount):
        """Credit earned income to this purchase and the owning user."""
        try:
            self.current_total_income += amount
            self.user.balance          += amount
            self.user.total_income     += amount
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def __repr__(self):
        return f'<UserProduct user={self.user_id} product={self.product_id}>'


# ─────────────────────────────────────────────────────────────────
#  Withdrawal
# ─────────────────────────────────────────────────────────────────

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'

    id           = db.Column(db.Integer,       primary_key=True)
    user_id      = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    amount       = db.Column(db.Numeric(12,2), nullable=False)
    status       = db.Column(db.String(20),    nullable=False, default='pending')
    requested_at = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    @staticmethod
    def get_by_user(user_id):
        return (
            Withdrawal.query
            .filter_by(user_id=user_id)
            .order_by(Withdrawal.requested_at.desc())
            .all()
        )

    @staticmethod
    def create(user_id, amount):
        """Create a pending withdrawal and deduct from user balance."""
        try:
            user = User.query.get(user_id)
            withdrawal = Withdrawal(user_id=user_id, amount=amount)
            user.balance -= amount
            db.session.add(withdrawal)
            db.session.commit()
            return withdrawal
        except Exception as e:
            db.session.rollback()
            raise e

    def __repr__(self):
        return f'<Withdrawal user={self.user_id} amount={self.amount} status={self.status}>'


# ─────────────────────────────────────────────────────────────────
#  News
# ─────────────────────────────────────────────────────────────────

class News(db.Model):
    __tablename__ = 'news'

    id           = db.Column(db.Integer,      primary_key=True)
    title        = db.Column(db.String(255),  nullable=False)
    body         = db.Column(db.Text)
    image        = db.Column(db.String(255))
    published_at = db.Column(db.DateTime,     nullable=False, default=datetime.utcnow)

    @staticmethod
    def get_latest(limit=6):
        return (
            News.query
            .order_by(News.published_at.desc())
            .limit(limit)
            .all()
        )

    def __repr__(self):
        return f'<News {self.title}>'


import uuid

class RechargeMethod(db.Model):
    __tablename__ = 'recharge_methods'

    id           = db.Column(db.Integer,     primary_key=True)
    tab          = db.Column(db.String(10),  nullable=False)           # 'bank' or 'usdt'
    method_key   = db.Column(db.String(20),  nullable=False, unique=True)  # 'bsp', 'kina', 'trc20', 'erc20'
    display_name = db.Column(db.String(50),  nullable=False)
    # Bank fields
    operator     = db.Column(db.String(100), nullable=True)
    account_name = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(100), nullable=True)
    code         = db.Column(db.String(50),  nullable=True)
    # USDT fields
    wallet_address = db.Column(db.String(255), nullable=True)
    qr_image     = db.Column(db.String(255), nullable=True)
    is_active    = db.Column(db.Boolean,     nullable=False, default=True)

    @staticmethod
    def get_by_key(method_key):
        return RechargeMethod.query.filter_by(method_key=method_key, is_active=True).first()


class RechargeOrder(db.Model):
    __tablename__ = 'recharge_orders'

    id           = db.Column(db.Integer,       primary_key=True)
    order_number = db.Column(db.String(30),    nullable=False, unique=True)
    user_id      = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    amount       = db.Column(db.Numeric(12,2), nullable=False)
    tab          = db.Column(db.String(10),    nullable=False)
    method_key   = db.Column(db.String(20),    nullable=False)
    status       = db.Column(db.String(20),    nullable=False, default='pending')
    voucher_image = db.Column(db.String(500), nullable=True)  
    created_at   = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='recharge_orders', lazy=True)

    @staticmethod
    def generate_order_number(method_key):
        """Generate order number like PNO260320124YE3VE."""
        from datetime import datetime
        import random, string
        now     = datetime.utcnow()
        date    = now.strftime('%d%m%y')
        hour    = now.strftime('%H')
        suffix  = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"PNO{date}{hour}{suffix}"

    @staticmethod
    def create(user_id, amount, tab, method_key):
        try:
            order = RechargeOrder(
                order_number = RechargeOrder.generate_order_number(method_key),
                user_id      = user_id,
                amount       = amount,
                tab          = tab,
                method_key   = method_key,
            )
            db.session.add(order)
            db.session.commit()
            return order
        except Exception as e:
            db.session.rollback()
            raise e



class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True)
    
    # Add this
    voucher_url = db.Column(db.String(500))



class GiftCode(db.Model):
    __tablename__ = 'gift_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Numeric(12,2), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    used_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GiftCode {self.code}>'



# ─────────────────────────────────────────────────────────────────
#  IncomeLog  — records every income credit to a user
# ─────────────────────────────────────────────────────────────────

class IncomeLog(db.Model):
    __tablename__ = 'income_logs'

    id           = db.Column(db.Integer,       primary_key=True)
    user_id      = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(100),   nullable=False)
    amount       = db.Column(db.Numeric(12,2), nullable=False)
    income_type  = db.Column(db.String(20),    nullable=False, default='product')  # 'product' | 'commission'
    from_phone   = db.Column(db.String(20),    nullable=True)   # filled for commissions only
    created_at   = db.Column(db.DateTime,      nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='income_logs', lazy=True)

    @staticmethod
    def get_product_income(user_id):
        return (
            IncomeLog.query
            .filter_by(user_id=user_id, income_type='product')
            .order_by(IncomeLog.created_at.desc())
            .all()
        )

    @staticmethod
    def get_commissions(user_id):
        return (
            IncomeLog.query
            .filter_by(user_id=user_id, income_type='commission')
            .order_by(IncomeLog.created_at.desc())
            .all()
        )

    @staticmethod
    def create(user_id, product_name, amount, income_type='product', from_phone=None):
        try:
            log = IncomeLog(
                user_id      = user_id,
                product_name = product_name,
                amount       = amount,
                income_type  = income_type,
                from_phone   = from_phone,
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            raise e

    def __repr__(self):
        return f'<IncomeLog user={self.user_id} type={self.income_type} amount={self.amount}>'