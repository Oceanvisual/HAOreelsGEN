"""Генератор диалогов и видео для Rick and Morty."""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from ..managers.voice_manager import ElevenLabsVoiceManager
from ..managers.image_manager import ImageManager
from ..managers.video_manager import VideoManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DialogueGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Инициализация генератора диалогов.
        
        Args:
            api_key (str, optional): API ключ OpenAI. Если не указан, берется из переменных окружения.
        """
        try:
            # Загрузка переменных окружения
            load_dotenv("config/.env")
            
            # Проверка наличия API ключей
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
            
            # Инициализация клиента OpenAI
            self.client = OpenAI(
                base_url="https://proxy.merkulov.ai",
                api_key=self.api_key
            )
            
            # Инициализация менеджеров
            self.voice_manager = ElevenLabsVoiceManager()
            self.image_manager = ImageManager(self.api_key)
            self.video_manager = VideoManager()
            
            self.last_generated_dialogue = None
            self.dialogue_images = {}
            self.dialogue_prompts = {}
            self.setup_directories()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации DialogueGenerator: {str(e)}")
            raise
    
    def setup_directories(self):
        """Создание необходимых директорий."""
        os.makedirs("dialogues", exist_ok=True)
        os.makedirs("metadata/dialogues", exist_ok=True)
    
    def generate_dialogue(self, topic: str, num_lines: int) -> str:
        """Генерация диалога на основе заданной темы.
        
        Args:
            topic (str): Тема диалога
            num_lines (int): Количество строк диалога
            
        Returns:
            str: Сгенерированный диалог
        """
        prompt = f"""Сгенерируй естественный диалог на русском языке о {topic} с ТОЧНО {num_lines} репликами.
        Формат диалога должен быть следующим:
        Персонаж 1: [реплика]
        Персонаж 2: [реплика]
        ...и так далее.
        
        Сделай диалог интересным и естественным. Каждая реплика должна быть краткой и подходящей для короткого видео.
        ВАЖНО: Должно быть ТОЧНО {num_lines} реплик, не больше и не меньше."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты креативный писатель диалогов на русском языке. Ты всегда генерируешь ТОЧНО указанное количество реплик."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            dialogue = response.choices[0].message.content.strip()
            
            # Проверка количества строк
            lines = [line for line in dialogue.split("\n") if line.strip()]
            if len(lines) != num_lines:
                # Если количество строк не совпадает, пробуем еще раз
                return self.generate_dialogue(topic, num_lines)
            
            self.last_generated_dialogue = dialogue
            self.dialogue_images = {}  # Сброс изображений для нового диалога
            self.dialogue_prompts = {}  # Сброс промптов для нового диалога
            
            # Сохранение метаданных
            metadata = {
                "topic": topic,
                "num_lines": num_lines,
                "dialogue": dialogue,
                "timestamp": datetime.now().isoformat()
            }
            
            metadata_filename = f"metadata/dialogues/dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metadata_filename, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            return dialogue
            
        except Exception as e:
            error_msg = f"Ошибка генерации диалога: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def edit_dialogue_manually(self, dialogue: str) -> str:
        """Ручное редактирование диалога.
        
        Args:
            dialogue (str): Диалог для редактирования
            
        Returns:
            str: Отредактированный диалог
        """
        print("\n=== Редактирование диалога ===")
        print("Текущий диалог:")
        print(dialogue)
        print("\nВведите 'сохранить' чтобы сохранить изменения")
        print("Введите 'отмена' чтобы отменить редактирование")
        
        edited_lines = []
        lines = dialogue.split("\n")
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            print(f"\nСтрока {i + 1}:")
            print(f"Текущая: {line}")
            new_line = input("Новая (Enter чтобы оставить без изменений): ").strip()
            
            if new_line.lower() == "сохранить":
                break
            elif new_line.lower() == "отмена":
                return dialogue
            elif new_line:
                edited_lines.append(new_line)
            else:
                edited_lines.append(line)
        
        edited_dialogue = "\n".join(edited_lines)
        
        # Сохранение метаданных
        metadata = {
            "original_dialogue": dialogue,
            "edited_dialogue": edited_dialogue,
            "timestamp": datetime.now().isoformat()
        }
        
        metadata_filename = f"metadata/dialogues/edited_dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        return edited_dialogue
    
    def save_dialogue_to_file(self, dialogue: str, topic: str) -> str:
        """Сохранение диалога в файл.
        
        Args:
            dialogue (str): Диалог для сохранения
            topic (str): Тема диалога
            
        Returns:
            str: Путь к сохраненному файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dialogues/dialogue_{topic}_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(dialogue)
        
        return filename

def main():
    """Основная функция для запуска генератора."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Генератор диалогов и видео для Rick and Morty")
    parser.add_argument("--api-key", help="API ключ ElevenLabs")
    args = parser.parse_args()
    
    try:
        generator = DialogueGenerator()
        
        while True:
            print("\n=== Генератор диалогов и видео для Rick and Morty ===")
            print("1. Сгенерировать новый диалог")
            print("2. Редактировать существующий диалог")
            print("3. Создать видео")
            print("4. Выход")
            
            choice = input("\nВыберите действие (1-4): ")
            
            if choice == "1":
                topic = input("\nВведите тему диалога: ")
                num_lines = int(input("Введите количество строк диалога: "))
                
                print("\nГенерация диалога...")
                dialogue = generator.generate_dialogue(topic, num_lines)
                print("\nСгенерированный диалог:")
                print(dialogue)
                
                # Предложение редактирования
                edit = input("\nХотите отредактировать диалог? (да/нет): ").lower()
                if edit == "да":
                    dialogue = generator.edit_dialogue_manually(dialogue)
                    print("\nОтредактированный диалог:")
                    print(dialogue)
                
                # Сохранение диалога
                filename = generator.save_dialogue_to_file(dialogue, topic)
                print(f"\nДиалог сохранен в файл: {filename}")
                
                # Предложение создания видео
                create_video = input("\nХотите создать видео с этим диалогом? (да/нет): ").lower()
                if create_video == "да":
                    print("\nСоздание видео...")
                    # Генерация изображений
                    dialogue_lines = [line.strip() for line in dialogue.split("\n") if line.strip()]
                    generator.dialogue_images = generator.image_manager.generate_images_for_dialogue(dialogue)
                    
                    # Создание видео
                    generator.video_manager.create_audio_with_timestamps(dialogue_lines, generator.dialogue_images)
                    generator.video_manager.process_video()
                    print("\nВидео успешно создано!")
            
            elif choice == "2":
                if generator.last_generated_dialogue:
                    print("\nРедактирование последнего диалога...")
                    dialogue = generator.edit_dialogue_manually(generator.last_generated_dialogue)
                    print("\nОтредактированный диалог:")
                    print(dialogue)
                    
                    # Сохранение отредактированного диалога
                    filename = generator.save_dialogue_to_file(dialogue, "отредактированный_диалог")
                    print(f"\nОтредактированный диалог сохранен в файл: {filename}")
                    
                    # Предложение создания видео
                    create_video = input("\nХотите создать видео с этим диалогом? (да/нет): ").lower()
                    if create_video == "да":
                        print("\nСоздание видео...")
                        dialogue_lines = [line.strip() for line in dialogue.split("\n") if line.strip()]
                        generator.dialogue_images = generator.image_manager.generate_images_for_dialogue(dialogue)
                        generator.video_manager.create_audio_with_timestamps(dialogue_lines, generator.dialogue_images)
                        generator.video_manager.process_video()
                        print("\nВидео успешно создано!")
                else:
                    print("\nНет сохраненного диалога для редактирования.")
            
            elif choice == "3":
                if generator.last_generated_dialogue:
                    print("\nСоздание видео из последнего диалога...")
                    dialogue_lines = [line.strip() for line in generator.last_generated_dialogue.split("\n") if line.strip()]
                    generator.dialogue_images = generator.image_manager.generate_images_for_dialogue(generator.last_generated_dialogue)
                    generator.video_manager.create_audio_with_timestamps(dialogue_lines, generator.dialogue_images)
                    generator.video_manager.process_video()
                    print("\nВидео успешно создано!")
                else:
                    print("\nНет сохраненного диалога для создания видео.")
            
            elif choice == "4":
                print("\nДо свидания!")
                break
            
            else:
                print("\nНеверный выбор. Пожалуйста, выберите действие от 1 до 4.")
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()
