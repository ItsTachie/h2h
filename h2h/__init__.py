from flask import Flask,url_for,redirect
from flask_sqlalchemy import SQLAlchemy 
from flask_admin import Admin , AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt    
from flask_login import LoginManager,current_user
from supabase import create_client
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from paynow import Paynow
from flask_mail import Mail



load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
SERVER_NAME= os.getenv('SERVER_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')
SALT = os.getenv('SALT')
INTEGRATION_ID = os.getenv('INTEGRATION_ID')
INTEGRATION_KEY = os.getenv('INTEGRATION_KEY')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SALT'] = SALT
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
app.config['SQLALCHEMY_POOL_SIZE'] = 5
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 10
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800

db = SQLAlchemy(app)

migrate = Migrate(app,db)

bcrypt=Bcrypt()

supabase= create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_KEY)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

paynow = Paynow(
    integration_id=INTEGRATION_ID,
    integration_key=INTEGRATION_KEY,
    return_url=os.getenv('PAYNOW_RETURN_URL'),
    result_url=os.getenv('PAYNOW_RESULT_URL')
)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('HandToHand Support', 'support@handtohand.site')

mail = Mail(app)

class MyAdminIndexView(AdminIndexView):
     def is_accessible(self):
        return current_user.is_authenticated and current_user.email.lower() == ADMIN_EMAIL
    
     def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('dashboard'))
    

class Hand2HandView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.email.lower() == ADMIN_EMAIL

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('dashboard'))
    
class ListingAdminView(Hand2HandView):
    column_searchable_list = ['title']
    column_filters = ['category', 'price']

admin = Admin(app,index_view=MyAdminIndexView() ,name="Hand2Hand Admin", template_mode="bootstrap4")
from h2h.models import User,Listing,Payment
admin.add_view(Hand2HandView(User, db.session))
admin.add_view(ListingAdminView(Listing, db.session))
admin.add_view(Hand2HandView(Payment, db.session))

from h2h import routes
