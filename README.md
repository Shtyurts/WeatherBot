# 🌤 Weather Telegram Bot

Телеграм-бот для получения точного прогноза погоды по координатам с возможностью сохранения избранных мест.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blue.svg)](https://docs.aiogram.dev/)

## ✨ Особенности

- 📍 Получение погоды по геолокации
- 💾 Сохранение пользовательских мест (название + координаты)
- 📅 Прогноз на:
  - Текущий момент
  - Сегодня (почасово)
  - 5 дней (сводка)
- 🌪 Отображение скорости и направления ветра
- 🗑 Управление сохраненными местами
- 🎛 Интуитивный inline-интерфейс

## ⚙️ Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/weather-telegram-bot.git
cd weather-telegram-bot
Установите зависимости:

bash
Copy
pip install -r requirements.txt
Создайте файл конфигурации config.py:

python
Copy
api = "ВАШ_API_КЛЮЧ_OPENWEATHERMAP"
token = "ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА"
🔑 Получение ключей
OpenWeatherMap API
Перейдите на OpenWeatherMap

Зарегистрируйтесь и создайте API ключ в разделе API Keys

Скопируйте ключ в config.py

Telegram Bot Token
Начните диалог с @BotFather

Используйте команду /newbot для создания бота

Скопируйте полученный токен в config.py

🚀 Запуск
bash
Copy
python main.py
🖥 Использование
Стартовое меню:

Copy
/start - Главное меню
Основные команды:

🌤 Текущее местоположение - запрос геопозиции

➕ Добавить место - сохранение новых координат

🗑️ Удалить место - управление сохраненными местами

Пример добавления места:

Copy
Дом, 55.7558, 37.6176
📂 Структура проекта
Copy
weather-bot/
├── database/
│   ├── db.py       # Настройки БД
│   ├── models.py   # Модели SQLAlchemy
│   └── repository.py # CRUD-операции
├── main.py         # Основной код бота
├── config.py       # Конфигурация (API ключи)
└── requirements.txt # Зависимости
