ЛАМБРИЗ — Telegram Bot + Telegram Mini App

Локальные папки:
- /Users/maksim/Desktop/Ламбриз бот
- /Users/maksim/Desktop/Ламбриз миниапп

Запуск бота (локально):
1) Установить зависимости: `pip install -r requirements.txt`
2) В `/Users/maksim/Desktop/Ламбриз бот/config.env` указать:
   - `BOT_TOKEN` — токен бота
   - `WEBAPP_URL` — HTTPS‑ссылка на mini‑app
   - `WELCOME_TEXT` — приветственный текст
3) Положить логотип `logo.png` в `/Users/maksim/Desktop/Ламбриз бот`
4) Запустить: `python bot.py`

Где менять URL Mini App:
- `/Users/maksim/Desktop/Ламбриз бот/config.env` → `WEBAPP_URL`

Mini App (локально):
1) Открыть `/Users/maksim/Desktop/Ламбриз миниапп/index.html` в браузере
2) Для Telegram Mini App нужно разместить файлы по HTTPS

Где менять email получателя заявок:
- `/Users/maksim/Desktop/Ламбриз миниапп/config.json` → `orderRecipientEmail`
- Адрес отправки (backend endpoint) для email: `orderEndpoint`

Где редактировать каталог:
- Категории: `/Users/maksim/Desktop/Ламбриз миниапп/data/categories.json`
- Товары: `/Users/maksim/Desktop/Ламбриз миниапп/data/products.json`

Примечание по отправке заявок:
- В mini‑app заявка отправляется POST‑запросом на `orderEndpoint`.
- Этот endpoint должен на сервере отправлять письмо на `orderRecipientEmail`.
