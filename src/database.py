"""Робота з базою даних Postgres: підключення, таблиці, запис і читання."""
import asyncpg
import os
from typing import Optional, List, Tuple


class Database:
    """Клас для підключення до Postgres і роботи з таблицею країн."""

    def __init__(self, database_url: Optional[str] = None):
        # Адреса бази — з змінної оточення або значення за замовчуванням
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/population_db"
        )
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Підключитись до бази і створити пул з'єднань. Одразу створюємо таблиці."""
        # asyncpg хоче postgres://, а не postgresql://
        conn_str = self.database_url.replace("postgresql://", "postgres://")
        self.pool = await asyncpg.create_pool(conn_str, min_size=1, max_size=5)
        await self.create_tables()

    async def disconnect(self):
        """Закрити пул з'єднань."""
        if self.pool:
            await self.pool.close()

    async def create_tables(self):
        """Створити таблицю країн, якщо її ще немає. Індекси для швидкого пошуку по регіону."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id SERIAL PRIMARY KEY,
                    country_name VARCHAR(255) NOT NULL,
                    population BIGINT NOT NULL,
                    region VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_region ON countries(region);
                CREATE INDEX IF NOT EXISTS idx_country_name ON countries(country_name);
            """)

    async def clear_data(self):
        """Видалити всі рядки з таблиці країн (щоб записати свіжі дані)."""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM countries")

    async def insert_country(self, country_name: str, population: int, region: str):
        """Додати одну країну в таблицю."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO countries (country_name, population, region)
                VALUES ($1, $2, $3)
            """, country_name, population, region)

    async def insert_countries_batch(self, countries: List[Tuple[str, int, str]]):
        """Додати багато країн одним пакетом — швидше, ніж по одній."""
        async with self.pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO countries (country_name, population, region)
                VALUES ($1, $2, $3)
            """, countries)

    async def get_region_statistics(self):
        """Отримати по регіонах: сума населення, найбільша країна, найменша. Один SQL-запит."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                -- по кожному регіону: сума, макс і мін населення
                WITH region_stats AS (
                    SELECT
                        region,
                        SUM(population) as total_population,
                        MAX(population) as max_population,
                        MIN(population) as min_population
                    FROM countries
                    GROUP BY region
                ),
                -- по регіону беремо одну країну з найбільшим населенням
                largest_countries AS (
                    SELECT DISTINCT ON (region)
                        region,
                        country_name as largest_country_name,
                        population as largest_country_population
                    FROM countries
                    ORDER BY region, population DESC
                ),
                -- по регіону беремо одну країну з найменшим населенням
                smallest_countries AS (
                    SELECT DISTINCT ON (region)
                        region,
                        country_name as smallest_country_name,
                        population as smallest_country_population
                    FROM countries
                    ORDER BY region, population ASC
                )
                -- збираємо все в одну таблицю результатів
                SELECT
                    rs.region,
                    rs.total_population,
                    lc.largest_country_name,
                    lc.largest_country_population,
                    sc.smallest_country_name,
                    sc.smallest_country_population
                FROM region_stats rs
                LEFT JOIN largest_countries lc ON rs.region = lc.region
                LEFT JOIN smallest_countries sc ON rs.region = sc.region
                ORDER BY rs.total_population DESC
            """)
            return rows
