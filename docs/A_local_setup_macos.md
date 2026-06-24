# [A] Инструкция по локальному запуску (macOS)

- **Дата создания:** 2026-06-24
- **Дата обновления:** 2026-06-24
- **Изменения:** Обновлены команды запуска и структура импортов

## Предварительные требования
- Python 3.11+
- Node.js 20+
- Аккаунт Supabase

## Запуск Backend
1. Находясь в корне репозитория, установите зависимости:
   ```bash
   pip install -r webapp/backend/requirements.txt
   ```
2. Настройте `.env` в корне (см. `webapp/backend/.env.example`)
3. Запустите сервер из корня:
   ```bash
   PYTHONPATH=. uvicorn webapp.backend.main:app --reload
   ```

## Запуск Frontend
1. Перейдите в `webapp/frontend`
2. Установите зависимости: `npm install`
3. Запустите: `npm run dev`
