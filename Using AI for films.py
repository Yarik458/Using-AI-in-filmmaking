import base64
from datetime import datetime
import requests
import sys
import subprocess


def time_segments(segments):
    texts = []
    start_times = []

    for segment in segments:
        text = segment['text']
        start = segment['start']

        start_datetime = datetime.fromtimestamp(start)

        formatted_start_time = start_datetime.strftime('%H:%M:%S')

        texts.append(text)
        start_times.append(formatted_start_time)
    return texts, start_times

video_path = r'example_video\Саратовский государственный университет.mp4'
audio_out = r'extracted_audio\extracted_audio.mp3'
command = [
    "ffmpeg", "-y",
    "-loglevel", "quiet",      # Скрыть логи ffmpeg
    "-i", video_path,
    "-af", "afftdn",
    "-af", "loudnorm",
    "-vn",
    "-c:a", "libmp3lame", #перевод в mp3
    "-b:a", "192k",
    audio_out
]

try:
    # Запуск процесса FFmpeg
    print("Выделение аудио с помощью ffmpeg....")
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Аудио дорожка извлечена...")
except FileNotFoundError:
    print("Ошибка: Утилита ffmpeg не найдена в системе.")
    sys.exit(1)

url = "https://routerai.ru/api/v1/audio/transcriptions"
headers = {
    "Authorization": "Bearer sk-I_33fj5z7bwqXgkXChkll6yBvLIt3lzO", #ключ routerai
    "Content-Type": "application/json"
}
print('Начало транскрибации.....')
with open(r'extracted_audio/extracted_audio.mp3', 'rb') as file1:
    audio_base64 = base64.b64encode(file1.read()).decode('utf-8')


data = {
    "model": "openai/whisper-large-v3-turbo",
    "input_audio": {
        "data": audio_base64,
        "format": "mp3"
    },
    "language": "ru",
    "response_format": "verbose_json",
    "timestamp_granularities": ["segment"]
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print("\r\n\r\nРезультат транскрибации аудио дорожки:")

texts, start_times = time_segments(result['segments'])
for start_time, text in zip(start_times, texts):
    print(f'{start_time}{text}')
