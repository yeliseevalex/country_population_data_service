"""Скрипт: прочитати з бази підсумки по регіонах і вивести на екран."""
import asyncio
import os
import sys
from src.database import Database


async def main():
    """Головна функція: беремо з бази вже зібрані по регіонах дані і друкуємо їх."""
    db = Database()
    try:
        await db.connect()
        print("Connected to database")

        # Один SQL-запит повертає по кожному регіону: суму, найбільшу і найменшу країну
        stats = await db.get_region_statistics()

        if not stats:
            print("No data found in database. Run 'get_data' first.")
            sys.exit(1)

        # Виводимо по кожному регіону по черзі — пострічково, як у завданні
        for row in stats:
            region = row['region']
            total_population = row['total_population']
            largest_country = row['largest_country_name']
            largest_population = row['largest_country_population']
            smallest_country = row['smallest_country_name']
            smallest_population = row['smallest_country_population']

            print(region)
            print(total_population)
            print(largest_country)
            print(largest_population)
            print(smallest_country)
            print(smallest_population)
            print()  # порожній рядок між регіонами

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
