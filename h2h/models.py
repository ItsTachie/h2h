from h2h import db ,login_manager
from datetime import datetime, timezone,timedelta
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    listings = db.relationship('Listing', backref='author', cascade='all,delete' ,lazy=True)
    transactions = db.relationship('Payment', backref='author')

    def __repr__(self):
        return f'User("{self.email}", "{self.number}")'

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(30), nullable=False)
    image_file = db.Column(db.String(30),nullable=False, default='default.jpg')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    uid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    boosted_until = db.Column(db.DateTime, nullable=True)

    @property
    def is_boosted(self):
        if self.boosted_until is None:
            return False
        if self.boosted_until.tzinfo is None:
            # Assume it's UTC if naive
            self.boosted_until = self.boosted_until.replace(tzinfo=timezone.utc)
        return self.boosted_until > datetime.now(timezone.utc)


    def boost(self, days=3):
        self.boosted_until = datetime.now(timezone.utc) + timedelta(days=days)


    def __repr__(self):
        return f'Listing("{self.title}", "{self.created_at}")'
    
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False)
    transaction_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # e.g. 'Pending', 'Paid', 'Failed'
    poll_url = db.Column(db.String(255))  # optional: for Paynow polling
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"<Payment {self.reference} - {self.status}>"