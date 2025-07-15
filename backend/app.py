import os
import json
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Загружаем переменные окружения (API_KEY, SECRET_KEY) из .env файла
load_dotenv()

# Создаем Flask приложение
app = Flask(__name__)
# Разрешаем CORS, чтобы frontend мог отправлять запросы на этот сервер
CORS(app)

class FusionBrainAPI:
    def __init__(self, url="https://api-key.fusionbrain.ai/"):
        self.URL = url
        # Получаем ключи из переменных окружения
        self.API_KEY = os.getenv("API_KEY")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        if not self.API_KEY or not self.SECRET_KEY:
            raise ValueError("API_KEY и SECRET_KEY должны быть установлены в .env файле")
            
        self.AUTH_HEADERS = {
            'X-Key': f'Key {self.API_KEY}',
            'X-Secret': f'Secret {self.SECRET_KEY}',
        }

    def get_model(self):
        """Получение ID модели Kandinsky"""
        try:
            response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
            response.raise_for_status() # Проверка на ошибки HTTP
            data = response.json()
            # Ищем модель Kandinsky 3.1, если нет, берем первую доступную
            model_id = next((item['id'] for item in data if '3.1' in item.get('version', '')), data[0]['id'])
            return model_id
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения модели: {e}")
            return None

    def generate(self, prompt, model_id, width=1024, height=1024, style="", negative_prompt=""):
        """Отправка запроса на генерацию"""
        params = {
            "type": "GENERATE",
            "style": style,
            "width": width,
            "height": height,
            "numImages": 1,
            "negativePromptDecoder": negative_prompt,
            "generateParams": {
                "query": prompt
            }
        }
        
        # Используем multipart/form-data для отправки данных
        files = {
            'model_id': (None, str(model_id)),
            'params': (None, json.dumps(params), 'application/json')
        }
        
        try:
            response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=files)
            response.raise_for_status()
            data = response.json()
            return data['uuid']
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке запроса на генерацию: {e}")
            return None

    def check_generation(self, request_id, attempts=20, delay=10):
        """Проверка статуса генерации"""
        while attempts > 0:
            try:
                response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'DONE':
                    # Возвращаем изображение в формате Base64
                    return data['images'][0] if data.get('images') else None
                elif data['status'] == 'FAIL':
                    print(f"Ошибка генерации: {data.get('error', 'Неизвестная ошибка')}")
                    return None

                time.sleep(delay)
                attempts -= 1
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при проверке статуса: {e}")
                attempts -= 1
                time.sleep(delay)
        return None

# Создаем эндпоинт /api/generate, который будет принимать запросы
@app.route('/api/generate', methods=['POST'])
def handle_generate():
    data = request.json
    prompt = data.get('prompt')
    style = data.get('style', '')
    
    if not prompt:
        return jsonify({"error": "Текстовый промпт не может быть пустым"}), 400

    api = FusionBrainAPI()
    model_id = api.get_model()
    
    if not model_id:
        return jsonify({"error": "Не удалось получить ID модели"}), 500
        
    uuid = api.generate(prompt, model_id, style=style)
    
    if not uuid:
        return jsonify({"error": "Не удалось запустить генерацию"}), 500

    image_base64 = api.check_generation(uuid)
    
    if image_base64:
        return jsonify({"image_base64": image_base64})
    else:
        return jsonify({"error": "Не удалось сгенерировать изображение или истекло время ожидания"}), 500

if __name__ == '__main__':
    # Запуск сервера для локального тестирования
    app.run(host='0.0.0.0', port=5001, debug=True)
