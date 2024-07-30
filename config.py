from dotenv import load_dotenv
from app import app
from os import getenv
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = getenv('SQLALCHEMY_TRACK_MODIFICATION')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')

print('Configured')