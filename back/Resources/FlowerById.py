import logging
from flask_restful import Resource, reqparse
from models import Flower

# Настройка логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowerByIdResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=True, help="ID of the flower is required")  # Параметр для ID
        args = parser.parse_args()

        flower_id = args['id']
        logger.info(f"Received GET request for flower with ID: {flower_id}")

        try:
            flower = Flower.query.get(flower_id)  # Пошук квітки за ID
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
                logger.warning(f"Flower with ID '{flower_id}' not found")
                return {'message': f'Flower with ID "{flower_id}" not found'}, 404

        except Exception as e:
            logger.error(f"An error occurred while retrieving flower by ID: {e}")
            return {'message': 'An error occurred while processing the request'}, 500
