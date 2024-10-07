# config.py
import os
SQLALCHEMY_DATABASE_URI = 'postgresql://ihor:1997@localhost/flowers_shop'
SQLALCHEMY_TRACK_MODIFICATIONS = False
secret_key = os.urandom(24)
SECRET_KEY = secret_key

