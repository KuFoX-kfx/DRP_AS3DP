"""
Russian strings. Demonstrates how to add a locale: same keys as
locales/en-us.py, translated values. Any key you skip here silently
falls back to the fallback locale via localization.py.
"""

STRINGS = {
    "state_idle": "Простой",
    "state_texturing": "Текстурирование",
    "state_baking": "Запекание карт",
    "state_exporting": "Экпорт текстур",
    "details_project": "Проект: {project_name}",
    "details_no_project": "Проект не открыт",
    "details_unsaved_project": "Проект: Без названия",
    # Имя технологии, поэтому здесь оно английское - так же, как в
    # settings_title ниже. Переводить его не нужно, но держать его в
    # исходниках тоже нельзя: локализовать его должен сам плагин.
    "menu_title": "Discord RPC",
    "menu_status": "Состояние: {status}",
    "menu_settings": "Настройки...",
    "menu_show_in_discord": "Показывать в Discord",
    "menu_about": "О плагине DRP AS3DP",
    "status_connected": "Подключено",
    "status_disabled": "Отключено",
    "status_discord_unavailable": "Discord не запущен",
    "status_invalid_client_id": "Неверный ID приложения Discord",
    "status_error": "Ошибка подключения",
    "settings_title": "Настройки Discord Rich Presence",
    "settings_show_project_name": "Показывать название проекта",
    "settings_show_project_name_hint": (
        "Если выключено, в Discord уходит только текущая активность, "
        "а название проекта не передаётся."
    ),
    "settings_show_elapsed_time": "Показывать время сессии",
    "settings_update_interval": "Интервал обновления",
    "settings_reconnect_interval": "Интервал переподключения",
    "settings_locale": "Язык",
    "settings_save": "Сохранить",
    "settings_cancel": "Отмена",
    "settings_restore_defaults": "Сбросить настройки",
    "settings_not_writable": (
        "Папка плагина недоступна для записи, поэтому настройки сбросятся "
        "после перезапуска Painter. Установите плагин в свою папку."
    ),
    "about_version": "Версия: {version}",
    "about_status": "Состояние: {status}",
    "about_client_id": "ID приложения Discord: {client_id}",
    "about_settings_file": "Файл настроек: {path}",
    "about_last_error": "Последняя ошибка: {error}",
}
