from flask import Flask
from flask_sqlalchemy import SQLAlchemy   
from flask_bcrypt import Bcrypt    
from flask_login import LoginManager
from supabase import create_client
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
supabase= create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_KEY)



app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = '7127d241054c4d188bc7d349c68f7c57'
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///./site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

bcrypt=Bcrypt()
login_manager=LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from h2h import routes
