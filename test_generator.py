"""Тестовый скрипт для проверки работы генератора диалогов."""

from src.core.dialogue_generator import DialogueGenerator

def main():
    # Инициализация генератора
    generator = DialogueGenerator()
    
    # Генерация тестового диалога
    print("\nГенерация тестового диалога...")
    dialogue = generator.generate_dialogue(
        topic="Рик и Морти обсуждают путешествие в параллельную вселенную",
        num_lines=4  # Начнем с небольшого диалога для теста
    )
    
    print("\nСгенерированный диалог:")
    print(dialogue)
    
    # Генерация изображений
    print("\nГенерация изображений для диалога...")
    dialogue_images = generator.image_manager.generate_images_for_dialogue(dialogue)
    
    # Создание видео
    print("\nСоздание видео...")
    dialogue_lines = [line.strip() for line in dialogue.split("\n") if line.strip()]
    generator.video_manager.create_audio_with_timestamps(dialogue_lines, dialogue_images)
    output_video = generator.video_manager.process_video()
    
    print(f"\nВидео успешно создано: {output_video}")

if __name__ == "__main__":
    main() 