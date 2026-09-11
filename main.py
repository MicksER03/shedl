import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
from zoneinfo import ZoneInfo
URL = "https://guide.herzen.spb.ru/schedule/25490/by-dates"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

cal = Calendar()
cal.add("prodid", "-//My Calendar Product//://example.com")
cal.add("version", "2.0")


def parse_schedule():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Ошибка загрузки страницы: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ищем все контейнеры дней по указанному вами набору CSS-классов
    day_blocks = soup.find_all('div', class_="p-5 mt-5 rounded-lg border border-gray-100 bg-gray-200")
    
    if not day_blocks:
        print("Блоки расписания не найдены. Возможно, изменились классы или расписание пустое.")
        return

    for block in day_blocks:
        # Обычно заголовок дня (дата) идет первым крупным текстом внутри блока (например, h3, h4 или просто div)
        # Если внутри блока есть тег заголовка, ищем его, иначе берем первый попавшийся текст


        date, day = block.find(['time']).get_text(strip=True).split(', ')
        
        print(date, day)
        lessons = block.find_all('li')
        date = date.split('.')
        for lesson in lessons:
            raw_text = lesson.get_text(separator=" | ")

            # 2. Очищаем от мусорных переносов строк и лишних пробелов:
            # Разделяем строку по пробелам и переносам, отсекая пустоту
            words = raw_text.split() 
            # Собираем обратно в одну строку, разделяя одиночным пробелом
            clean_text = " ".join(words)

            # 3. Красиво убираем склеившиеся разделители "| | | |" 
            # Заменяем цепочки из палочек и пробелов на одну аккуратную палочку
            while "| |" in clean_text or "||" in clean_text:
                clean_text = clean_text.replace("| |", "|").replace("||", "|")

            # Убираем палочки, если они случайно остались в самом начале или конце строки
            clean_text = clean_text.strip(" |").split(' | ')



            
            # 2. Создаем событие
            event = Event()
            event.add("summary", f"[{clean_text[4].upper()}] {clean_text[1]}")
            event.add("description", f"{clean_text[5]}\n{clean_text[3]}")
            event.add("location", f"{clean_text[6]}")


            time = clean_text[0].replace("-", ":").split(":")

            
            # Настройка времени с таймзоной через встроенный ZoneInfo
            tz = ZoneInfo("Europe/Moscow")
            event.add("dtstart", datetime(int(date[2]), int(date[1]), int(date[0]), int(time[0]), int(time[1]), 0, tzinfo=tz))
            event.add("dtend", datetime(int(date[2]), int(date[1]), int(date[0]), int(time[2]), int(time[3]), 0, tzinfo=tz))
            event.add("dtstamp", datetime.now(tz))  # Текущее время сразу с таймзоной

            # 3. Добавляем событие в календарь
            cal.add_component(event)
            print("qjjjj")
                

            # print(f"Найдена пара: {clean_text}")

    with open("company_event.ics", "wb") as f:
        f.write(cal.to_ical())

    print("Файл company_event.ics успешно создан без использования pytz!")

if __name__ == "__main__":
    parse_schedule()


