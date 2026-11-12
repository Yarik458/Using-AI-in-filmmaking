import json

import requests

from config import get_routerai_api_key, get_translation_model


def parse_translations(api_response):
    content = api_response['choices'][0]['message']['content']
    translated_entries = json.loads(content)['subtitles']
    return translated_entries


def translate(subtitle_path, target_language):
    subtitle_entries = []
    with open(subtitle_path, 'r') as f:
        for subtitle_block in f.read().strip().split('\n\n'):
            lines = subtitle_block.strip().splitlines()

            text = " ".join(line.strip() for line in lines[2:])
            if text:
                subtitle_entries.append({"id": int(lines[0]), "text": text, })

    url = "https://routerai.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_routerai_api_key()}",
        "Content-Type": "application/json"
    }

    translation_result = {"subtitles": []}

    for i in range(0, len(subtitle_entries), 50):
        subtitle_batch = subtitle_entries[i:i + 50]
        data = {
            "model": get_translation_model(),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Переведи субтитры на {target_language} язык. "
                        "Учитывай контекст соседних реплик. "
                        "Сохрани все id и количество элементов. "
                        "Не объединяй и не пропускай реплики. "
                        "Переводи только значения text. "
                        'Верни JSON-объект вида '
                        '{"subtitles": [{"id": 1, "text": "Перевод"}]}. '
                        "Не добавляй пояснений."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(subtitle_batch, ensure_ascii=False),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        translated_strings = parse_translations(response.json())
        translation_result["subtitles"].extend(translated_strings)

    return translation_result
