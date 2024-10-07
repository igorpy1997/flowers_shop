from flask_admin import Admin, AdminIndexView
from sqlalchemy.orm import configure_mappers

from admin.flowers import FlowerView
from models.flower import Flower


def setup_admin(app, db):
    with app.app_context():
        configure_mappers()
        admin = Admin(
            app, name='Flower Shop', template_mode='bootstrap3',
            index_view=AdminIndexView()
        )

        # Реєстрація унікальних view з різними іменами
        admin.add_view(FlowerView(Flower, db.session, name='Квітки', endpoint='Квітки'))


