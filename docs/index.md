# Документация TeamPal Backend

Справочник по слоям **services**, **repositories** и **errors**.

## Разделы

| Документ | Что внутри |
|----------|------------|
| [Сервисы](services.md) | Бизнес-логика: регистрация, проекты, отклики, рекомендации |
| [Репозитории](repositories.md) | Запросы к PostgreSQL |
| [Ошибки](errors.md) | Исключения API и HTTP-коды |

## Как устроен backend

```
HTTP → api/ → services/ → repositories/ → PostgreSQL
                    ↘ Redis, Celery, SMTP, S3
```

**Services** проверяют правила (лимиты, владение, статусы) и вызывают репозитории.  
**Repositories** не содержат бизнес-правил — только чтение и запись данных.
