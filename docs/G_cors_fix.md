# G — CORS Configuration

## Проблема

При запросе к `http://localhost:8000/api/shops/` из фронтенда на `http://localhost:5173` браузер блокировал запрос:

```
Access to XMLHttpRequest at 'http://localhost:8000/api/shops/' from origin
'http://localhost:5173' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Причина

В `webapp/backend/main.py` CORS-middleware была настроена так:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # <-- wildcard
    allow_credentials=True,   # <-- + credentials
    ...
)
```

Комбинация `allow_origins=["*"]` и `allow_credentials=True` **запрещена спецификацией CORS**. Когда сервер одновременно отправляет:

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Credentials: true`

Браузер отклоняет ответ — `*` нельзя использовать как allowed origin при включённых credentials. Starlette (FastAPI) обнаруживает это противоречие и вовсе **не добавляет** заголовок `Access-Control-Allow-Origin`, что и приводит к ошибке.

## Решение

Заменить wildcard явным списком разрешённых origins:

```python
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Для production

Перед деплоем добавить продакшен-домен в `ALLOWED_ORIGINS` (или вынести список в переменные окружения):

```python
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
```

В `.env`:

```
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
