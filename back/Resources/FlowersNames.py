import logging
from flask_restful import Resource
from models import Flower

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowerNamesResource(Resource):
    def get(self):
        logger.info("Received GET request for all flower names")

        try:
            # Отримання списку всіх квітів
            flowers = Flower.query.all()

            if flowers:
                # Створення списку з імен квітів
                result = [flower.name for flower in flowers]
                logger.info(f"Successfully fetched {len(result)} flower names")
                return {'flower_names': result}, 200
            else:
                logger.warning("No flower names found")
                return {'message': 'No flower names found'}, 404

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {'message': 'An error occurred while processing the request'}, 500
