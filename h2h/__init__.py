from flask import Flask,url_for
from flask_sqlalchemy import SQLAlchemy   
from flask_bcrypt import Bcrypt    
from flask_login import LoginManager
from supabase import create_client
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from paynow import Paynow


load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
SERVER_NAME= os.getenv('SERVER_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')
INTEGRATION_ID = os.getenv('INTEGRATION_ID')
INTEGRATION_KEY = os.getenv('INTEGRATION_KEY')


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL   
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_NAME'] = SERVER_NAME

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
    return_url='https://3ce7807ff3b0.ngrok-free.app/payment/result',
    result_url='https://3ce7807ff3b0.ngrok-free.app/payment/webhook'
)

from h2h import routes

