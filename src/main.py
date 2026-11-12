import shutil
import subprocess
import tempfile
from pathlib import Path

import gradio as gr
import requests

from ffmpeg_tools.ffmpeg import extract_audio, insert_subtitles
from subtitle_tools.srt import build_srt, split_sentences
from subtitle_tools.translate import translate
from transcribe_tools.transcribe import transcribe


def process_video(video, target_languages, black_background, font_size, progress=gr.Progress()):
    if not video:
        raise gr.Error('Загрузите видео.')

    work_dir = Path(tempfile.mkdtemp(prefix='subtitles-'))
    source_path = work_dir / ('video' + Path(video).suffix.lower())
    shutil.copyfile(video, source_path)
    try:
        progress(0.1, desc='Извлечение аудио')
        audio_path = extract_audio(str(source_path), str(work_dir / 'audio.mp3'))
        progress(0.25, desc='Распознавание речи')
        result = transcribe(audio_path)
        words = result.get('words')
        if not words:
            raise gr.Error('Routerai не вернул метки слов')
        segments = split_sentences(words)
        if not segments:
            raise gr.Error('В аудио не обнаружена речь')
        subtitle_path = Path(build_srt(segments, 'original', work_dir))
        translated_files = []
        video_files = []
        for index, target_language in enumerate(target_languages):
            progress(0.4 + 0.5 * index / len(target_languages), desc=f'Переводится на {target_language}')
            result = translate(str(subtitle_path), target_language)
            translated = result['subtitles']
            translations = {item['id']: item['text'] for item in translated}
            all_subs_cnt = set(range(1, len(segments) + 1))
            if len(translated) != len(all_subs_cnt) or set(translations) != all_subs_cnt:
                raise gr.Error(f'Нейросеть вернула неполный перевод: {target_language}. Попробуйте ещё раз.')
            translated_path = work_dir / f'{target_language}.srt'
            blocks = []
            for block in subtitle_path.read_text(encoding='utf-8').strip().split('\n\n'):
                lines = block.splitlines()
                blocks.append(f'{lines[0]}\n{lines[1]}\n{translations[int(lines[0])].strip()}\n\n')
            translated_path.write_text(''.join(blocks), encoding='utf-8')
            translated_files.append(str(translated_path))
            progress(0.4 + 0.5 * (index + 0.5) / len(target_languages), desc=f'Создание видео: {target_language}')
            video_files.append(insert_subtitles(source_path, translated_path, black_background, font_size))
        if not video_files:
            progress(0.75, desc='Добавление субтитров в видео')
            video_files.append(insert_subtitles(source_path, subtitle_path, black_background, font_size))
        progress(1, desc='Готово')
        return video_files[0], video_files, str(subtitle_path), translated_files
    except gr.Error:
        raise
    except requests.RequestException as exception:
        raise gr.Error(f'Ошибка запроса к RouterAI: {exception}') from exception
    except subprocess.CalledProcessError as exception:
        raise gr.Error(f'Не удалось обработать видео {exception.returncode}.') from exception
    except (ValueError, KeyError) as exception:
        raise gr.Error(f'Не удалось обработать результат {exception}') from exception


with gr.Blocks() as app:
    gr.Markdown('Загрузите видео, чтобы распознать речь, при необходимости перевести её и добавить субтитры в ролик.')
    with gr.Row():
        with gr.Column():
            video = gr.Video(label='Исходное видео', sources=['upload'])
            language = gr.Dropdown(['английский', 'русский', 'испанский', 'немецкий', 'французский'], value=[],
                                   multiselect=True, label='Языки перевода',
                                   info='Оставьте пустым, чтобы сохранить субтитры на языке оригинала.')
            background = gr.Checkbox(value=True, label='Чёрный фон для субтитров')
            font_size = gr.Slider(10, 40, value=16, step=1, label='Размер субтитров')
            submit = gr.Button('Создать субтитры', variant='primary')
        with gr.Column():
            output_video = gr.Video(label='Видео с субтитрами')
            video_files = gr.File(label='Все видео', file_count='multiple')
            with gr.Row():
                original_file = gr.File(label='Сгенерированные субтитры SRT')
                translated_file = gr.File(label='Переведённые субтитры SRT', file_count='multiple')
    submit.click(process_video, [video, language, background, font_size],
                 [output_video, video_files, original_file, translated_file])
    app.launch(share=True)
