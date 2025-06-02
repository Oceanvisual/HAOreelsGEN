"""Менеджер для работы с генерацией изображений через DALL-E API."""

import os
import json
import time
from datetime import datetime
from typing import Optional
from io import BytesIO
import requests
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from requests.exceptions import RequestException, ConnectionError, Timeout

class ImageManager:
    def __init__(self, api_key: Optional[str] = None):
        """Инициализация менеджера изображений.
        
        Args:
            api_key (str, optional): API ключ OpenAI. Если не указан, берется из переменных окружения.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        self.client = OpenAI(
            base_url="https://proxy.merkulov.ai",
            api_key=self.api_key
        )
        self.setup_directories()
    
    def setup_directories(self):
        """Создание необходимых директорий для хранения изображений и метаданных."""
        os.makedirs("images", exist_ok=True)
        os.makedirs("metadata/images", exist_ok=True)
    
    def download_image_with_retry(self, image_url: str, max_retries: int = 3, timeout: int = 30) -> Image.Image:
        """Загрузка изображения с повторными попытками.
        
        Args:
            image_url (str): URL изображения для загрузки
            max_retries (int): Максимальное количество попыток
            timeout (int): Таймаут запроса в секундах
            
        Returns:
            Image.Image: Загруженное изображение
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(image_url, timeout=timeout, stream=True)
                response.raise_for_status()
                
                # Чтение данных изображения по частям
                image_data = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        image_data.write(chunk)
                
                image_data.seek(0)
                return Image.open(image_data)
                
            except (RequestException, ConnectionError, Timeout) as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Не удалось загрузить изображение после {max_retries} попыток: {str(e)}")
                print(f"Попытка {attempt + 1} не удалась, повторяем через 2 секунды...")
                time.sleep(2)
        
        raise Exception("Не удалось загрузить изображение")
    
    def generate_image(self, prompt: str, line_number: int, custom_prompt: Optional[str] = None) -> str:
        """Генерация изображения для строки диалога.
        
        Args:
            prompt (str): Строка диалога для генерации изображения
            line_number (int): Номер строки в диалоге
            custom_prompt (str, optional): Пользовательский промпт для генерации изображения
            
        Returns:
            str: Путь к сгенерированному изображению
        """
        try:
            # Использование пользовательского промпта, если он предоставлен
            image_prompt = custom_prompt if custom_prompt else f"Создай изображение для диалога: {prompt}. Изображение должно быть в стиле мультфильма, яркое и подходящее для короткого видео."
            
            # Генерация изображения с retry логикой
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"\nПопытка генерации изображения {attempt + 1} из {max_retries}")
                    print(f"Промпт: {image_prompt}")
                    
                    response = self.client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        n=1,
                        size="1024x1024",
                        quality="standard",
                        style="vivid"
                    )
                    
                    # Получение URL изображения
                    image_url = response.data[0].url
                    print(f"Получен URL изображения: {image_url}")
                    
                    # Загрузка и сохранение изображения
                    image = self.download_image_with_retry(image_url)
                    
                    # Создание уникального имени файла
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"images/dialogue_line_{line_number}_{timestamp}.png"
                    
                    # Сохранение изображения
                    image.save(filename)
                    print(f"Изображение сохранено в {filename}")
                    
                    # Сохранение метаданных
                    metadata = {
                        "line_number": line_number,
                        "dialogue_line": prompt,
                        "image_prompt": image_prompt,
                        "image_path": filename,
                        "timestamp": timestamp
                    }
                    
                    metadata_filename = f"metadata/images/dialogue_line_{line_number}_{timestamp}.json"
                    with open(metadata_filename, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=4)
                    
                    return filename
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Не удалось сгенерировать изображение после {max_retries} попыток: {str(e)}")
                    print(f"Попытка генерации {attempt + 1} не удалась, повторяем через 2 секунды...")
                    time.sleep(2)
            
        except Exception as e:
            return f"Ошибка генерации изображения: {str(e)}"
    
    def generate_images_for_dialogue(self, dialogue: str, custom_prompts: Optional[dict] = None) -> dict:
        """Генерация изображений для всего диалога.
        
        Args:
            dialogue (str): Диалог для генерации изображений
            custom_prompts (dict, optional): Словарь с пользовательскими промптами для каждой строки
            
        Returns:
            dict: Словарь с путями к сгенерированным изображениям
        """
        lines = [line.strip() for line in dialogue.split("\n") if line.strip()]
        images = {}
        
        for i, line in enumerate(lines):
            custom_prompt = custom_prompts.get(i) if custom_prompts else None
            image_path = self.generate_image(line, i, custom_prompt)
            images[i] = image_path
        
        return images 