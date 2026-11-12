import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_routerai_api_key():
    api_key = os.getenv("ROUTERAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Укажи ROUTERAI_API_KEY в .env в корне проекта")
    return api_key


def get_transcription_model():
    model = os.getenv("TRANSCRIPTION_MODEL", "").strip()
    if not model:
        raise ValueError("Укажи TRANSCRIPTION_MODEL в .env в корне проекта")
    return model


def get_translation_model():
    model = os.getenv("TRANSLATION_MODEL", "").strip()
    if not model:
        raise ValueError("Укажи TRANSLATION_MODEL в .env в корне проекта")
    return model
