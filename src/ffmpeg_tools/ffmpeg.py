import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg


def extract_audio(video_path, audio_path):
    if os.path.exists(audio_path):
        print(f"Аудиофайл {os.path.basename(audio_path)} уже существует и будет взят за основу")
    else:
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y",
            "-loglevel", "quiet",  # Скрыть логи ffmpeg
            "-i", video_path,
            "-af", "afftdn",
            "-af", "loudnorm",
            "-vn",
            "-c:a", "libmp3lame",  # перевод в mp3
            "-b:a", "192k",
            audio_path
        ]
        print("Выделение аудио с помощью ffmpeg....")
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Аудио дорожка извлечена...")
    return audio_path


def insert_subtitles(video_path, subtitles_path, black_background=False, font_size=16):
    video_path = Path(video_path).resolve()
    subtitles_path = Path(subtitles_path).resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"Видео не найдено: {video_path}")
    if not subtitles_path.is_file():
        raise FileNotFoundError(f"Файл субтитров не найден: {subtitles_path}")

    suffix = "w_b_s" if black_background else "w_s"
    output_path = video_path.with_name(
        f"{video_path.stem}_{subtitles_path.stem}_{suffix}.mp4"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copyfile(subtitles_path, Path(temp_dir) / "subtitles.srt")

        style = f"FontSize={int(font_size)}"
        if black_background:
            style += ",BorderStyle=4,BackColour=&H00000000,Outline=1"
        subtitle_filter = f"subtitles=subtitles.srt:force_style='{style}'"

        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(video_path),
            "-map", "0:v:0", "-map", "0:a?", "-vf", subtitle_filter,
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
        subprocess.run(command, cwd=temp_dir, check=True)
    return str(output_path)
