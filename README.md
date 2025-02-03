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

### Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/weather-telegram-bot.git
cd weather-telegram-bot
```
### Установите зависимости:

```bash
pip install -r requirements.txt
```

### Создайте файл для параметров окружения `.env`:

```
token=ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА
OWM_API=ВАШ_API_КЛЮЧ_OPENWEATHERMAP
```

## 🔑 Получение ключей

### OpenWeatherMap API

#### Перейдите на OpenWeatherMap

[![OpenWeather](https://img.shields.io/badge/OpenWeatherAPI-3.0-orange.svg)](https://openweathermap.org/api/one-call-3)

#### Зарегистрируйтесь и создайте API ключ в разделе [API Keys](https://home.openweathermap.org/api_keys)

Скопируйте ключ в `.env`

### Telegram Bot Token

#### Начните диалог с [@BotFather](https://t.me/BotFather)

#### Используйте команду `/newbot` для создания бота

#### Скопируйте полученный токен в `.env`

## 🚀 Запуск

```bash
python main.py
```

## 🖥 Использование

### Стартовое меню:

```
/start - Главное меню
```

### Основные команды:

#### 🌤 Текущее местоположение - запрос геопозиции

#### ➕ Добавить место - сохранение новых координат

#### 🗑️ Удалить место - управление сохраненными местами

### Пример добавления места:

```
Дом, 55.7558, 37.6176
```

### Пример прогноза:

```
📅 Пн (2023-10-23):
   ⏰ 09:00: 15°C, Облачно
   🌪 4 м/с (↘️ СВ)
   ⏰ 12:00: 18°C, Ясно
   🌪 2 м/с (➡️ В)
```

## 📂 Структура проекта
```
weather-bot/
├── code/
│   ├── main.py     # Основной код бота
│   ├── config.py   # Конфигурация
│   └── database/
│       ├── db.py         # Настройки БД
│       ├── models.py     # Модели SQLAlchemy
│       └── repository.py # CRUD-операции
├── .env             # Параметры окружения
├── .env.example     # Пример параметров окружения
├── .gitignore       # gitignore
├── requirements.txt # Требования
└── README.md   	 # Описание проекта
```