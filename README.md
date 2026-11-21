# Расписание занятий РГПУ им. А. И. Герцена в формате iCalendar (.ics)

Автоматический парсер расписания занятий с портала [guide.herzen.spb.ru](https://guide.herzen.spb.ru/schedule/25490/by-dates). Генерирует файл `schedule.ics`, обновляемый каждый час через GitHub Actions.

## 📅 Ссылки для подписки

- **GitHub Pages (основная)**: `https://mickser03.github.io/shedl/schedule.ics`
- **Прямая ссылка для Apple Calendar**: `webcal://mickser03.github.io/shedl/schedule.ics`
- **Резервная ссылка (Raw GitHub)**: `https://raw.githubusercontent.com/MicksER03/shedl/main/schedule.ics`

### Как добавить в календарь:
- **Google Calendar**: В веб-версии слева нажать `+` возле «Другие календари» → «Добавить по URL» → вставить ссылку.
- **Apple Календарь (iOS / macOS)**: Открыть ссылку `webcal://...` или выбрать «Файл» → «Новая подписка на календарь».
- **Яндекс Календарь**: Нажать на шестеренку в левой панели → «Добавить календарь по ссылке».

## ⚙️ Настройка GitHub Pages

Чтобы файл `schedule.ics` был доступен по адресу `https://mickser03.github.io/shedl/schedule.ics`:
1. Перейдите в **Settings** репозитория на GitHub.
2. В левом меню откройте **Pages**.
3. В разделе **Build and deployment** выберите:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`, папка `/ (root)`
4. Нажмите **Save**.

## 🛠 Локальный запуск

```bash
pip install -r requirements.txt
python main.py
```
