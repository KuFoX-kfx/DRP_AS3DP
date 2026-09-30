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
    "menu_update_check": "Проверить обновления",
    "menu_update_checking": "Проверка обновлений...",
    "menu_update_install": "Обновить",
    "menu_update_installing": "Обновление...",
    "menu_update_failed": "Не удалось обновить",
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
    "settings_auto_update": "Устанавливать обновления автоматически",
    "settings_auto_update_hint": (
        "Когда выйдет новая версия, она установится сама при следующем "
        "запуске Painter. Больше ничего от вас не требуется."
    ),
    "settings_advanced": (
        "Расширенные настройки - менять их обычно не нужно и чаще всего "
        "бесполезно, поэтому открывайте только если есть причина"
    ),
    "settings_check_updates": "Проверять обновления при запуске плагина",
    "settings_api_token": "Токен API",
    "settings_api_token_empty": "не задан",
    "settings_api_token_hint": (
        "Необязательно. Нужен только для репозитория, который его "
        "требует, или когда упрётесь в лимит запросов. Хранится открытым "
        "текстом в settings.json, поэтому не вставляйте токен с "
        "правами шире, чем чтение релизов."
    ),
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
    "about_last_update_error": "Последняя ошибка обновления: {error}",

    "update_dialog_title": "Обновление DRP AS3DP",
    "update_stage_check": "Поиск более новой версии...",
    "update_stage_download": "Загрузка с {source}...",
    "update_stage_verify": "Проверка загруженного архива...",
    "update_stage_unpack": "Распаковка...",
    "update_stage_install": "Установка...",
    "update_cancel": "Отмена",

    "update_error_network": "Не удалось связаться ни с одним источником релизов.",
    "update_error_download": "Не удалось скачать новую версию.",
    "update_error_checksum": (
        "Загруженный архив не совпал с опубликованной контрольной суммой."
    ),
    "update_error_archive": "Не удалось распаковать загруженный архив.",
    "update_error_no_asset": (
        "В опубликованном релизе нет архива плагина."
    ),
    "update_error_install": "Не удалось заменить папку плагина.",
    "update_error_cancelled": "Отменено.",
    "update_error_unknown": "Обновление завершилось неизвестной ошибкой.",

    "update_notice_installed": "Обновлено до версии {version}",
    "update_notice_restart": "Обновлено до версии {version} - перезапустите Painter",
    "update_reload_failed": (
        "Новая версия установлена, но не запустилась. Перезапустите "
        "Painter, чтобы загрузить её.\n\n{error}"
    ),
}
