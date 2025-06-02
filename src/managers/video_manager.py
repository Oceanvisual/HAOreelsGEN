"""Модуль для работы с видео."""

import logging
import os
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import moviepy.editor as mp
from PIL import Image

logger = logging.getLogger(__name__)

class VideoManager:
    """Менеджер для работы с видео."""

    def __init__(
        self, 
        output_dir: str = "output",
        background_video: str = "assets/background.mp4"
    ):
        """Инициализация менеджера видео.
        
        Args:
            output_dir: Директория для выходных файлов
            background_video: Путь к фоновому видео
        """
        self.output_dir = output_dir
        self.background_video = background_video
        self.video_size = (1080, 1920)  # 9:16 для вертикального видео
        
        # Создаем директорию, если она не существует
        os.makedirs(output_dir, exist_ok=True)

    def create_video(
        self,
        audio_files: List[str],
        character_images: List[Tuple[str, str]],  # [(character, image_path), ...]
        output_filename: str,
        duration: float = 30.0
    ) -> str:
        """Создание видео с персонажами и озвучкой.
        
        Args:
            audio_files: Список путей к аудио файлам
            character_images: Список кортежей (персонаж, путь к изображению)
            output_filename: Имя выходного файла
            duration: Длительность видео в секундах
            
        Returns:
            str: Путь к созданному видео
        """
        try:
            # Загружаем фоновое видео
            background = mp.VideoFileClip(
                self.background_video
            ).resize(self.video_size)
            
            # Обрезаем или зацикливаем фоновое видео
            if background.duration < duration:
                background = background.loop(duration=duration)
            else:
                background = background.subclip(0, duration)
            
            # Создаем клипы с персонажами
            character_clips = []
            for character, image_path in character_images:
                if not os.path.exists(image_path):
                    logger.warning(f"Изображение не найдено: {image_path}")
                    continue
                    
                # Создаем клип с изображением персонажа
                img = mp.ImageClip(image_path)
                
                # Позиционируем персонажа
                if character == "rick":
                    position = (self.video_size[0] - 500, 100)
                else:  # morty
                    position = (100, self.video_size[1] - 450)
                
                img = img.set_position(position)
                character_clips.append(img)
            
            # Создаем аудио клипы
            audio_clips = [
                mp.AudioFileClip(audio) for audio in audio_files
            ]
            
            # Объединяем все аудио
            final_audio = mp.CompositeAudioClip(audio_clips)
            
            # Создаем финальное видео
            final_video = mp.CompositeVideoClip(
                [background] + character_clips,
                size=self.video_size
            ).set_audio(final_audio)
            
            # Сохраняем результат
            output_path = os.path.join(self.output_dir, output_filename)
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Закрываем все клипы
            final_video.close()
            background.close()
            for clip in audio_clips:
                clip.close()
            for clip in character_clips:
                clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании видео: {str(e)}")
            raise 

    def create_subtitle_clips(self, timestamps: List[Dict], video_size: tuple) -> List[mp.TextClip]:
        """Создание субтитров для видео.
        
        Args:
            timestamps (List[Dict]): Список временных меток с текстом
            video_size (tuple): Размер видео (ширина, высота)
            
        Returns:
            List[TextClip]: Список клипов с субтитрами
        """
        subtitle_clips = []
        for ts in timestamps:
            text = ts["text"]
            start_time = ts["start"]
            end_time = ts["end"]
            
            # Создание субтитра
            txt_clip = mp.TextClip(
                text,
                fontsize=40,
                color="white",
                stroke_color="black",
                stroke_width=2,
                font="Arial-Bold",
                size=video_size,
                method="caption"
            )
            
            # Позиционирование субтитра внизу экрана
            txt_clip = txt_clip.set_position(("center", "bottom"))
            txt_clip = txt_clip.set_start(start_time).set_end(end_time)
            
            subtitle_clips.append(txt_clip)
        
        return subtitle_clips
    
    def create_image_clips(self, timestamps: List[Dict], video_size: tuple) -> List[mp.ImageClip]:
        """Создание клипов с изображениями.
        
        Args:
            timestamps (List[Dict]): Список временных меток с путями к изображениям
            video_size (tuple): Размер видео (ширина, высота)
            
        Returns:
            List[ImageClip]: Список клипов с изображениями
        """
        image_clips = []
        for ts in timestamps:
            image_path = ts["image"]
            start_time = ts["start"]
            end_time = ts["end"]
            
            # Создание клипа с изображением
            img_clip = mp.ImageClip(image_path)
            
            # Изменение размера изображения с сохранением пропорций
            img_width, img_height = img_clip.size
            target_width = video_size[0]
            target_height = int(img_height * (target_width / img_width))
            
            if target_height > video_size[1]:
                target_height = video_size[1]
                target_width = int(img_width * (target_height / img_height))
            
            img_clip = img_clip.resize((target_width, target_height))
            
            # Центрирование изображения
            x_pos = (video_size[0] - target_width) // 2
            y_pos = (video_size[1] - target_height) // 2
            img_clip = img_clip.set_position((x_pos, y_pos))
            
            # Установка времени
            img_clip = img_clip.set_start(start_time).set_end(end_time)
            
            image_clips.append(img_clip)
        
        return image_clips
    
    def process_video(self, output_filename: Optional[str] = None) -> str:
        """Создание финального видео.
        
        Args:
            output_filename (str, optional): Имя выходного файла
            
        Returns:
            str: Путь к созданному видео
        """
        try:
            # Размер видео для TikTok (9:16)
            video_size = (1080, 1920)
            
            # Создание черного фона
            background = mp.ColorClip(size=video_size, color=(0, 0, 0))
            background = background.set_duration(sum(ts["end"] - ts["start"] for ts in self.timestamps))
            
            # Создание субтитров и клипов с изображениями
            subtitle_clips = self.create_subtitle_clips(self.timestamps, video_size)
            image_clips = self.create_image_clips(self.timestamps, video_size)
            
            # Загрузка аудио
            audio = mp.AudioFileClip("temp/audio/final_audio.wav")
            
            # Создание композиции
            video = mp.CompositeVideoClip(
                [background] + image_clips + subtitle_clips,
                size=video_size
            )
            
            # Добавление аудио
            video = video.set_audio(audio)
            
            # Генерация имени файла
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"output/video_{timestamp}.mp4"
            
            # Сохранение метаданных
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "video_size": video_size,
                "duration": video.duration,
                "output_file": output_filename,
                "dialogue_lines": self.dialogue_lines,
                "timestamps": self.timestamps
            }
            
            metadata_filename = f"metadata/video/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metadata_filename, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            # Экспорт видео
            print(f"\nСоздание видео: {output_filename}")
            video.write_videofile(
                output_filename,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="medium"
            )
            
            print(f"Видео успешно создано: {output_filename}")
            return output_filename
            
        except Exception as e:
            print(f"Ошибка при создании видео: {str(e)}")
            raise
    
    def create_audio_with_timestamps(self, dialogue_lines: List[str], dialogue_images: Dict[int, str]) -> None:
        """Создание аудио с временными метками для видео.
        
        Args:
            dialogue_lines (List[str]): Список строк диалога
            dialogue_images (Dict[int, str]): Словарь с путями к изображениям
        """
        from ..managers.voice_manager import ElevenLabsVoiceManager
        
        voice_manager = ElevenLabsVoiceManager()
        self.dialogue_lines = dialogue_lines
        self.audio_files = []
        self.image_files = []
        self.timestamps = []
        
        current_time = 0
        for i, line in enumerate(dialogue_lines):
            # Определение персонажа по номеру строки
            is_rick = i % 2 == 0
            
            # Генерация аудио
            audio_file = voice_manager.generate_audio(line, is_rick)
            self.audio_files.append(audio_file)
            
            # Получение длительности аудио
            audio = mp.AudioFileClip(audio_file)
            duration = audio.duration
            
            # Добавление временной метки
            self.timestamps.append({
                "text": line,
                "image": dialogue_images.get(i, ""),
                "start": current_time,
                "end": current_time + duration
            })
            
            current_time += duration
        
        # Объединение аудио файлов
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for audio_file in self.audio_files:
            audio = AudioSegment.from_file(audio_file)
            combined += audio
        
        # Сохранение финального аудио
        combined.export("temp/audio/final_audio.wav", format="wav")
        print("Аудио успешно объединено и сохранено в temp/audio/final_audio.wav") 