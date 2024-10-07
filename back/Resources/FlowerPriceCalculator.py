import logging
from flask_restful import Resource, reqparse
from models import Flower

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowerPriceCalculatorResource(Resource):
    def get(self):
        # Парсер для прийому словника з квітами та кількістю
        parser = reqparse.RequestParser()
        parser.add_argument('flowers', type=dict, required=True, help="Flowers data is required")  # Словник квітів
        args = parser.parse_args()

        flowers_data = args['flowers']
        logger.info(f"Received GET request for flowers: {flowers_data}")

        total_price = 0.0
        response = {}

        try:
            # Перевірка наявності кожної квітки у базі та підрахунок вартості
            for flower_name, quantity in flowers_data.items():
                flower = Flower.query.filter_by(name=flower_name).first()

                if flower:
                    if flower.quantity >= quantity:  # Перевірка, чи достатньо квітів на складі
                        flower_cost = flower.price * quantity
                        total_price += flower_cost
                        response[flower_name] = {
                            'quantity': quantity,
                            'unit_price': flower.price,
                            'total_price': flower_cost
                        }
                    else:
                        logger.warning(f"Not enough quantity for flower '{flower_name}'")
                        return {
                            'message': f'Not enough quantity for flower "{flower_name}". Available: {flower.quantity}'
                        }, 400
                else:
                    logger.warning(f"Flower '{flower_name}' not found")
                    return {'message': f'Flower "{flower_name}" not found'}, 404

            return {
                'total_price': total_price,
                'flowers': response
            }, 200

        except Exception as e:
            logger.error(f"An error occurred while calculating flower prices: {e}")
            return {'message': 'An error occurred while processing the request'}, 500
