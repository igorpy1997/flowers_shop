import os
import uuid
import logging
from werkzeug.datastructures import FileStorage
from flask_admin.form import ImageUploadField
from wtforms.fields.simple import TextAreaField
from flask_admin.contrib.sqla import ModelView


class FlowerView(ModelView):
    form_columns = ['name', 'photo', 'description', 'quantity', 'price']
    column_list = ['name', 'quantity']

    form_extra_fields = {
        'photo': ImageUploadField('Фото квітки',
                                  base_path='media/flowers',
                                  url_relative_path='flowers/',
                                  endpoint="media_files",
                                  allowed_extensions=['jpg', 'png']),
        'description': TextAreaField('Опис квітки', render_kw={
            "style": "width: 100%; height: 200px; overflow-y: scroll;",
            "rows": 10,  # Кількість видимих рядків до появи прокрутки
            "placeholder": "Введіть детальний опис квітки..."
        }),
    }

    form_args = {
        'name': {"label": "Назва квітки"},
        'description': {"label": "Опис квітки"},
        'quantity': {"label": "Кількість"},
        'price': {'label': 'Ціна'}
    }
    column_labels = {
        'name': 'Назва',
        'quantity': 'Кількість',
        'price': 'Ціна'
    }

    def on_model_change(self, form, model, is_created):
        if isinstance(form.photo.data, FileStorage):
            file_extension = os.path.splitext(form.photo.data.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = os.path.join('media/flowers', unique_filename)
            file_data = form.photo.data.read()

            if len(file_data) > 0:
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                model.photo = file_path
                logging.info(f"File saved successfully at {file_path}, size: {len(file_data)} bytes")
            else:
                logging.error("File is empty, not saved.")

    def on_model_delete(self, model):
        if model.photo:
            file_path = os.path.join('media/flowers', model.photo)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"File {file_path} deleted successfully.")
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")
