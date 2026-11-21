import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

URL = "https://guide.herzen.spb.ru/schedule/25490/by-dates"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def create_session() -> requests.Session:
    """Создает сессию requests с автоматическими повторными попытками."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def parse_schedule():
    session = create_session()
    try:
        response = session.get(URL, headers=HEADERS, timeout=(10, 30))
    except Exception as e:
        print(f"Ошибка при сетевом запросе к {URL}: {e}")
        return

    if response.status_code != 200:
        print(f"Ошибка загрузки страницы: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Ищем заголовки дней (тег <time>), они гарантированно содержат дату
    time_tags = soup.find_all("time")
    if not time_tags:
        print("Теги <time> не найдены. Возможно, изменилась разметка страницы.")
        return

    cal = Calendar()
    cal.add("prodid", "-//Herzen Schedule Parser//ru")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Расписание занятий РГПУ")
    cal.add("x-wr-timezone", "Europe/Moscow")

    tz = ZoneInfo("Europe/Moscow")
    total_events = 0

    for t_tag in time_tags:
        # Контейнер дня — родительский блок для тега time
        day_block = t_tag.find_parent("div")
        if not day_block:
            continue

        date_raw = t_tag.get_text(strip=True).split(",")[0].strip()
        try:
            d, m, y = map(int, date_raw.split("."))
        except Exception as e:
            print(f"Пропуск некорректной даты '{date_raw}': {e}")
            continue

        lessons = day_block.find_all("li")
        for li in lessons:
            # 1. Время пары (например, 9:40-11:10)
            time_match = re.search(
                r"(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})", li.get_text()
            )
            if not time_match:
                continue
            sh, sm, eh, em = map(int, time_match.groups())

            # 2. Название дисциплины и ссылка на Moodle (если есть)
            title_div = li.find(
                "div", class_=lambda c: c and "text-base font-normal" in c
            )
            title = (
                " ".join(title_div.get_text().split())
                if title_div
                else "Занятие"
            )

            moodle_url = ""
            if title_div:
                a_tag = title_div.find("a", href=True)
                if a_tag and a_tag.get("href"):
                    moodle_url = a_tag["href"]

            # 3. Детали: тип пары (лаб/лекц/практ/зачёт), преподаватель, аудитория
            details_div = li.find(
                "div", class_=lambda c: c and "flex flex-col text-sm" in c
            )
            items = (
                details_div.find_all(
                    "div", class_=lambda c: c and "inline-flex items-center" in c
                )
                if details_div
                else []
            )

            l_type = ""
            teacher = ""
            location = ""

            for item in items:
                svg_str = str(item.find("svg") or "")
                text = " ".join(item.get_text().split())
                # По иконкам SVG в верстке Герцена:
                # 16.862 - карандаш (тип занятия)
                # 15.75 - силуэт человека (преподаватель)
                # 15 10.5 - маркер геолокации (аудитория)
                if "16.862" in svg_str:
                    l_type = text
                elif "15.75" in svg_str:
                    teacher = text
                elif "15 10.5" in svg_str:
                    location = text

            # Резервный порядок, если иконка изменится
            if not l_type and len(items) > 0:
                l_type = " ".join(items[0].get_text().split())
            if not teacher and len(items) > 1:
                teacher = " ".join(items[1].get_text().split())
            if not location and len(items) > 2:
                location = " ".join(items[2].get_text().split())

            # 4. Примечание (может отсутствовать)
            note = ""
            py2 = li.find("div", class_="py-2")
            if py2:
                for child in py2.find_all("div", recursive=False):
                    txt = " ".join(child.get_text().split())
                    if "Примечание" in txt:
                        note = txt
                        break

            # 5. Формирование события календаря
            summary = f"[{l_type.upper()}] {title}" if l_type else title

            desc_parts = []
            if teacher:
                desc_parts.append(teacher)
            if note:
                desc_parts.append(note)
            if moodle_url:
                desc_parts.append(f"Moodle: {moodle_url}")
            description = "\n".join(desc_parts)

            event = Event()
            event.add("summary", summary)
            if description:
                event.add("description", description)
            if location:
                event.add("location", location)

            event.add("dtstart", datetime(y, m, d, sh, sm, 0, tzinfo=tz))
            event.add("dtend", datetime(y, m, d, eh, em, 0, tzinfo=tz))
            event.add("dtstamp", datetime.now(tz))

            # Детерминированный UID, чтобы при обновлении расписания события не дублировались в календарях
            uid_source = f"{y}-{m}-{d}_{sh:02d}:{sm:02d}_{title}_{l_type}_{teacher}"
            uid = (
                hashlib.sha256(uid_source.encode("utf-8")).hexdigest()
                + "@herzen-schedule"
            )
            event.add("uid", uid)

            cal.add_component(event)
            total_events += 1

    if total_events > 0:
        with open("schedule.ics", "wb") as f:
            f.write(cal.to_ical())
        print(f"Файл schedule.ics успешно обновлен: добавлено {total_events} занятий.")
    else:
        print("Внимание: занятия не были найдены, файл schedule.ics не перезаписан.")


if __name__ == "__main__":
    parse_schedule()
