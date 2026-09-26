"""
Russian strings. Demonstrates how to add a locale: same keys as
locales/en.py, translated values. Any key you skip here silently
falls back to the English text via localization.py.
"""

STRINGS = {
    "state_idle": "Простой",
    "state_texturing": "Текстурирование",
    "state_baking": "Запекание карт",
    "state_exporting": "Экспорт текстур",
    "details_project": "Проект: {project_name}",
    "details_no_project": "Проект не открыт",
    "large_text": "Substance 3D Painter",
}
