"""Менеджер для работы с голосовым синтезом через ElevenLabs API."""

import os
import requests
import json
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

class ElevenLabsVoiceManager:
    def __init__(self, api_key: Optional[str] = None):
        """Инициализация менеджера голосового синтеза.
        
        Args:
            api_key (str, optional): API ключ ElevenLabs. Если не указан, берется из переменных окружения.
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY не найден в переменных окружения")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_ids = {
            "rick": "21m00Tcm4TlvDq8ikWAM",  # ID голоса Рика
            "morty": "AZnzlk1XvdvUeBnXmlld"   # ID голоса Морти
        }
        self.setup_directories()
    
    def setup_directories(self):
        """Создание необходимых директорий для хранения аудио файлов."""
        os.makedirs("temp/audio", exist_ok=True)
        os.makedirs("metadata/audio", exist_ok=True)
    
    def generate_audio(self, text: str, is_rick: bool = True, max_retries: int = 3) -> str:
        """Генерация аудио для текста с помощью ElevenLabs API.
        
        Args:
            text (str): Текст для преобразования в речь
            is_rick (bool): True для голоса Рика, False для голоса Морти
            max_retries (int): Максимальное количество попыток генерации
            
        Returns:
            str: Путь к сгенерированному аудио файлу
        """
        voice_id = self.voice_ids["rick"] if is_rick else self.voice_ids["morty"]
        character = "Rick" if is_rick else "Morty"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        for attempt in range(max_retries):
            try:
                print(f"\nПопытка генерации аудио {attempt + 1} из {max_retries}")
                print(f"Текст: {text}")
                print(f"Персонаж: {character}")
                
                response = requests.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                # Создание уникального имени файла
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"temp/audio/{character.lower()}_{timestamp}.mp3"
                
                # Сохранение аудио файла
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"Аудио сохранено в {filename}")
                
                # Сохранение метаданных
                metadata = {
                    "character": character,
                    "text": text,
                    "audio_path": filename,
                    "timestamp": timestamp,
                    "voice_id": voice_id
                }
                
                metadata_filename = f"metadata/audio/{character.lower()}_{timestamp}.json"
                with open(metadata_filename, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                
                return filename
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Не удалось сгенерировать аудио после {max_retries} попыток: {str(e)}")
                print(f"Попытка {attempt + 1} не удалась, повторяем через 2 секунды...")
                import time
                time.sleep(2)
        
        raise Exception("Не удалось сгенерировать аудио") 