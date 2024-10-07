import logging
from flask_restful import Resource, reqparse
from models import Flower

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowerByNameResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Name of the flower is required")  # Параметр для назви
        args = parser.parse_args()

        name = args['name']
        logger.info(f"Received GET request for flower with name: {name}")

        try:
            flower = Flower.query.filter_by(name=name).first()  # Пошук квітки за назвою
            if flower:
                return {
                    'id': flower.id,
                    'name': flower.name,
                    'photo': flower.photo,
                    'quantity': flower.quantity,
                    'price': flower.price,
                    'description': flower.description
                }, 200
            else:
                logger.warning(f"Flower with name '{name}' not found")
                return {'message': f'Flower with name "{name}" not found'}, 404

        except Exception as e:
            logger.error(f"An error occurred while retrieving flower by name: {e}")
            return {'message': 'An error occurred while processing the request'}, 500
