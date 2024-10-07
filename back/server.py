
from flask import Flask, redirect, url_for, render_template, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_restful import Api
import config
from Resources.FlowerById import FlowerByIdResource
from Resources.FlowerByName import FlowerByNameResource
from Resources.FlowerPriceCalculator import FlowerPriceCalculatorResource
from Resources.FlowersNames import FlowerNamesResource
from Resources.FlowersResource import FlowerResource
from models import db
from admin import setup_admin
from models.User import User

# Flask application
app = Flask(__name__, static_folder='static')
app.config.from_object(config)

# SQLAlchemy
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
setup_admin(app, db)

api = Api(app)
api.add_resource(FlowerResource, '/api/resources/all_flowers')
api.add_resource(FlowerByNameResource, '/api/resources/flower_by_name')
api.add_resource(FlowerByIdResource, '/api/resources/flower_by_id')
api.add_resource(FlowerNamesResource, '/api/resources/flower_names')
api.add_resource(FlowerPriceCalculatorResource, '/api/resources/flower_parse_calculator')


# Flask Routes
@app.route('/media/<path:filename>')
def media_files(filename):
    return send_from_directory('media', filename)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    return "Welcome to the Study Bot Server!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from models import UserModel
        user = UserModel.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('admin.index'))
        flash('Invalid credentials')
    return render_template('login.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Запускаємо Flask додаток
