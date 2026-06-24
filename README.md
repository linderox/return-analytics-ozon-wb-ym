# Marketplace Returns SaaS

> **Author: Anton Mislawsky**
> Project Date: June 2026

Комплексная SaaS-платформа для управления и аналитики возвратов с маркетплейсов Ozon, Wildberries и Яндекс Маркет.

## Особенности

- **Claude Code 2026 UI:** Современный, минималистичный интерфейс в стиле терминала Claude (желтый/белый фон, моноширинные шрифты).
- **Hybrid Storage:** Уникальная архитектура хранения данных:
  - **Supabase (PostgreSQL):** Хранит профили, настройки магазинов и данные подписок.
  - **Local SQLite (`returns_history.db`):** Позволяет хранить неограниченную историю возвратов локально на сервере, обходя лимиты облачных БД.
- **Google Auth:** Бесшовная авторизация через Supabase Google OAuth.
- **СБП Интеграция:** Поддержка платежной системы РФ через ЮKassa.
- **Панель Администратора:** Полный контроль над аккаунтами клиентов и мониторинг объемов локальных данных.
- **Локализация:** Полностью на русском языке.

## Технологический стек

- **Backend:** FastAPI (Python 3.11+), AsyncPG, SQLite
- **Frontend:** Vue 3 (Composition API), Vite, Tailwind CSS, Pinia
- **Auth/DB:** Supabase (PostgreSQL 15)
- **Testing:** Pytest (Backend), Vitest (Frontend)

## Быстрый старт

### Настройка окружения
1. Создайте `.env` в корне проекта на основе `webapp/backend/.env.example`.
2. Установите зависимости бэкенда: `pip install -r webapp/backend/requirements.txt`.
3. Установите зависимости фронтенда: `cd webapp/frontend && npm install`.

### Запуск
- **Backend:** `PYTHONPATH=. uvicorn webapp.backend.main:app --reload`
- **Frontend:** `cd webapp/frontend && npm run dev`

## Документация

Подробные инструкции находятся в папке `docs/`:
- [A] Локальный запуск
- [B] Развертывание на Ubuntu
- [C] Гайд для агентов
- [D] Настройка платежей и Auth
- [F] Тестирование
- [G] Структура проекта

---
© 2026 Anton Mislawsky
