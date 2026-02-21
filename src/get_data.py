"""Скрипт: завантажити дані про населення, розпарсити і зберегти в базу."""
import asyncio
import os
import sys
from src.database import Database
from src.parsers import get_parser


async def main():
    """Головна функція: дістаємо дані з сайту і пишемо їх у базу."""
    # Звідки брати дані — з змінної оточення (за замовчуванням wikipedia)
    data_source = os.getenv('DATA_SOURCE', 'wikipedia')

    print(f"Using data source: {data_source}")

    # Підключаємось до бази
    db = Database()
    try:
        await db.connect()
        print("Connected to database")

        # Спочатку очищаємо старі дані, щоб не дублювати
        await db.clear_data()
        print("Cleared existing data")

        # Обираємо парсер залежно від джерела (wikipedia, statisticstimes тощо)
        parser = get_parser(data_source)
        print(f"Fetching data from {parser.url}")

        # Завантажуємо сторінку з інтернету
        html = await parser.fetch_data()
        print("Data fetched, parsing...")

        # Розбираємо HTML і витягуємо список країн (назва, населення, регіон)
        countries = parser.parse(html)
        print(f"Parsed {len(countries)} countries")

        # Зберігаємо всі країни в базу одним пакетом
        if countries:
            await db.insert_countries_batch(countries)
            print(f"Successfully saved {len(countries)} countries to database")
        else:
            print("Warning: No countries parsed from the source")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Завжди відключаємось від бази
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
