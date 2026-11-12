import base64

import requests

from config import get_routerai_api_key, get_transcription_model


def transcribe(audio_path):
    url = "https://routerai.ru/api/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {get_routerai_api_key()}",
        "Content-Type": "application/json"
    }
    print('Начало транскрибации.....')
    with open(audio_path, 'rb') as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

    data = {
        "model": get_transcription_model(),
        "input_audio": {
            "data": audio_base64,
            "format": "mp3",
        },
        "response_format": "verbose_json",
        "timestamp_granularities": ["segment", "word"],
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
