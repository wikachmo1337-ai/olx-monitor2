# OLX монитор — установка (10 минут)

## 1. Репозиторий
1. На github.com создай новый репозиторий (например `olx-monitor`), Public.
2. Загрузи в него ВСЕ файлы из этого архива с сохранением папок
   (Add file → Upload files; папку `.github` лучше загрузить через git или создать файл
   `.github/workflows/monitor.yml` вручную через Add file → Create new file).

## 2. Сайт (GitHub Pages)
Settings → Pages → Source: Deploy from a branch → Branch: `main`, папка `/docs` → Save.
Адрес сайта: `https://ТВОЙ_НИК.github.io/olx-monitor/`

## 3. Telegram-уведомления на телефон
1. В Telegram открой @BotFather → /newbot → получи токен.
2. Напиши своему боту любое сообщение (/start).
3. Открой в браузере `https://api.telegram.org/bot<ТОКЕН>/getUpdates` и найди `"chat":{"id": 123456789`.
4. В репозитории: Settings → Secrets and variables → Actions → New repository secret:
   - `TG_TOKEN` = токен бота
   - `TG_CHAT_ID` = твой chat id

## 4. Первый запуск
Actions → OLX monitor → Run workflow. Через минуту в `docs/ads.json` появятся объявления,
сайт покажет их. При первом запуске в Telegram ничего не шлётся (чтобы не было спама старыми).

## 5. Частый запуск (чаще 10 минут)
GitHub `schedule` сильно опаздывает, поэтому запускай через cron-job.org:
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained →
   доступ только к этому репозиторию, Permissions: Actions = Read and write. Скопируй токен.
2. На cron-job.org создай задачу:
   - URL: `https://api.github.com/repos/ТВОЙ_НИК/olx-monitor/actions/workflows/monitor.yml/dispatches`
   - Метод: POST, интервал: каждые 2 минуты
   - Headers: `Authorization: Bearer ТОКЕН`, `Accept: application/vnd.github+json`, `Content-Type: application/json`
   - Body: `{"ref":"main"}`

## Настройка
- `config.json` — бюджет (`max_price`, null = без ограничения), минимальные цены (отсев аксессуаров), поисковые запросы.
- `monitor/matcher.py` — слова-маркеры (pixel/пиксель/піксель, iphone/айфон, samsung s, macbook) и слова-исключения.

## Если не работает
- В логе Actions `HTTP 403` — OLX блокирует IP GitHub. Тогда запусти `python monitor/olx_monitor.py` на домашнем ПК по расписанию.
- Лимит GitHub Actions для публичных репозиториев бесплатный.
