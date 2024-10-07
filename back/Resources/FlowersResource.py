import logging
from flask_restful import Resource, reqparse
from models import Flower

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowerResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, help="Page number for pagination")
        parser.add_argument('per_page', type=int, default=10, help="Number of flowers per page")
        args = parser.parse_args()

        page = args['page']
        per_page = args['per_page']

        logger.info(f"Received GET request for flowers with pagination: page={page}, per_page={per_page}")

        try:
            # Пагінація і отримання даних
            flowers_query = Flower.query
            total_flowers = flowers_query.count()

            # Пагінація
            flowers = flowers_query.order_by(Flower.id).offset((page - 1) * per_page).limit(per_page).all()

            if flowers:
                result = [
                    {
                        'id': flower.id,
                        'name': flower.name,
                        'photo': flower.photo,
                        'quantity': flower.quantity,
                        'price': flower.price,
                        'description': flower.description
                    }
                    for flower in flowers
                ]
                total_pages = (total_flowers + per_page - 1) // per_page
                logger.info(f"Successfully fetched {len(result)} flowers for page {page}")
                return {
                    'flowers': result,
                    'total_flowers': total_flowers,
                    'total_pages': total_pages,
                    'page': page,
                    'per_page': per_page
                }, 200
            else:
                logger.warning("No flowers found")
                return {'message': 'No flowers found'}, 404

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {'message': 'An error occurred while processing the request'}, 500
