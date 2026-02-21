"""Парсери: завантажити сторінку з сайту і витягнути з таблиці країни (назва, населення, регіон)."""
import re
from abc import ABC, abstractmethod
from typing import List, Tuple
from bs4 import BeautifulSoup
import aiohttp


class BaseParser(ABC):
    """Базова основа для всіх парсерів — кожен джерело має fetch_data і parse."""

    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    async def fetch_data(self) -> str:
        """Завантажити HTML сторінки з інтернету."""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[Tuple[str, int, str]]:
        """Розібрати HTML і повернути список: (назва країни, населення, регіон)."""
        pass

    def clean_number(self, text: str) -> int:
        """З тексту витягнути число: прибрати коми, пробіли, залишити цифри."""
        cleaned = re.sub(r'[^\d-]', '', text)
        try:
            return int(cleaned)
        except ValueError:
            return 0


class WikipediaParser(BaseParser):
    """Парсер таблиці з Вікіпедії про населення країн."""

    async def fetch_data(self) -> str:
        """Завантажити сторінку Вікіпедії. Заголовки як у браузера, щоб не отримати 403."""
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                response.raise_for_status()
                return await response.text()

    def parse(self, html: str) -> List[Tuple[str, int, str]]:
        """Знайти таблицю wikitable і з кожного рядка витягнути країну, населення, регіон."""
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', class_='wikitable')

        if not table:
            raise ValueError("Wikipedia table not found")

        results = []
        tbody = table.find('tbody')
        if not tbody:
            return results

        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 5:
                continue

            # рядки-підсумки (на кшталт "World") пропускаємо
            if 'static-row-numbers-norank' in row.get('class', []):
                continue

            # назва країни — у першій комірці, посилання
            location_cell = cells[0]
            country_link = location_cell.find('a')
            if not country_link:
                continue

            country_name = country_link.text.strip()
            if country_name == 'World':
                continue

            # населення — у третьій комірці (індекс 2)
            if len(cells) < 3:
                continue

            population_text = cells[2].get_text(strip=True)
            if population_text == 'N/A':
                continue

            population = self.clean_number(population_text)
            if population == 0:
                continue

            # регіон (континент ООН) — у п'ятій комірці (індекс 4)
            if len(cells) < 5:
                continue

            region_cell = cells[4]
            region_link = region_cell.find('a')
            if region_link:
                region = region_link.text.strip()
            else:
                region = region_cell.get_text(strip=True)

            if not region:
                continue

            results.append((country_name, population, region))

        return results


class StatisticsTimesParser(BaseParser):
    """Парсер сайту StatisticsTimes — таблиця країн за населенням."""

    async def fetch_data(self) -> str:
        """Завантажити сторінку. User-Agent як у браузера."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                response.raise_for_status()
                return await response.text()

    def parse(self, html: str) -> List[Tuple[str, int, str]]:
        """Таблиця з id table_id: країна в першій комірці, населення в другій, континент в останній."""
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', id='table_id')

        if not table:
            raise ValueError("StatisticsTimes table not found")

        results = []
        tbody = table.find('tbody')
        if not tbody:
            return results

        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            # назва країни — перша комірка
            country_cell = cells[0]
            country_link = country_cell.find('a')
            if country_link:
                country_name = country_link.text.strip()
            else:
                country_name = country_cell.get_text(strip=True)

            if not country_name or country_name == 'World':
                continue

            # населення — друга комірка (індекс 1)
            population_text = cells[1].get_text(strip=True)
            population = self.clean_number(population_text)
            if population == 0:
                continue

            # континент — остання комірка (індекс 8)
            region = cells[8].get_text(strip=True)
            if not region:
                continue

            results.append((country_name, population, region))

        return results


class WorldOMetersParser(BaseParser):
    """Парсер WorldOMeters — третє джерело (таблиця по країнах)."""

    async def fetch_data(self) -> str:
        """Завантажити сторінку з WorldOMeters."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                response.raise_for_status()
                return await response.text()

    def parse(self, html: str) -> List[Tuple[str, int, str]]:
        """Шукаємо таблицю по id або класу. Країна і населення — у перших комірках; регіон часто не в таблиці — ставимо Unknown."""
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', {'id': 'example2'}) or soup.find('table', class_='table')

        if not table:
            raise ValueError("WorldOMeters table not found")

        results = []
        tbody = table.find('tbody')
        if not tbody:
            return results

        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            # назва країни — у першій або другій комірці (не число)
            country_name = ""
            for cell in cells[:2]:
                text = cell.get_text(strip=True)
                if not re.match(r'^\d+$', text):
                    country_name = text
                    break

            if not country_name or country_name == 'World':
                continue

            # населення — комірка з великим числом (типу населення країни)
            population = 0
            for cell in cells:
                text = cell.get_text(strip=True)
                num = self.clean_number(text)
                if num > 100000:
                    population = num
                    break

            if population == 0:
                continue

            # на цьому сайті регіон не завжди є в таблиці
            region = "Unknown"

            results.append((country_name, population, region))

        return results


def get_parser(source: str) -> BaseParser:
    """За назвою джерела (wikipedia, statisticstimes, worldometers) повернути потрібний парсер."""
    sources = {
        'wikipedia': WikipediaParser(
            'https://en.wikipedia.org/w/index.php?title=List_of_countries_by_population_(United_Nations)&oldid=1215058959'
        ),
        'statisticstimes': StatisticsTimesParser(
            'https://statisticstimes.com/demographics/countries-by-population.php'
        ),
        'worldometers': WorldOMetersParser(
            'https://www.worldometers.info/world-population/population-by-country/'
        ),
    }

    parser = sources.get(source.lower())
    if not parser:
        raise ValueError(f"Unknown data source: {source}. Available: {', '.join(sources.keys())}")

    return parser
