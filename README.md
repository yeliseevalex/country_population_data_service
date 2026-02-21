# Сервіс даних про населення країн

Сервіс запускається через docker-compose: зберігає дані про населення країн у Postgres і виводить на екран підсумки по регіонах. Код можна завантажити на GitHub.

## Джерело даних

За замовчуванням використовується таблиця зі сторінки:
https://en.wikipedia.org/w/index.php?title=List_of_countries_by_population_(United_Nations)&oldid=1215058959

Додатково підтримуються інші джерела (StatisticsTimes, WorldOMeters); джерело вибирається змінною оточення `DATA_SOURCE`.

## Репозиторій

https://github.com/yeliseevalex/country_population_data_service

## Як перевірити

```bash
git clone https://github.com/yeliseevalex/country_population_data_service
cd country_population_data_service
docker compose up get_data
docker compose up print_data
```

(Або `docker-compose` замість `docker compose`, залежно від версії Docker.)

## Вимоги до реалізації

- Django не використовувати (дозволені інші фреймворки та ORM).
- Postgres має підніматися автоматично через docker-compose.
- У базі дані зберігаються в неагрегованому вигляді — окремий запис на кожну країну.
- При виводі агрегація має виконуватися одним SQL-запитом.
- Код має бути організований на класах.

## Як працює сервіс

**get_data** — завантажує сторінку, парсить таблицю і зберігає рядки (країна, населення, регіон) у базу.

**print_data** — читає дані з бази і виводить по регіонах пострічково в такому форматі:

- Назва регіону  
- Загальне населення регіону  
- Назва найбільшої країни в регіоні (за населенням)  
- Населення найбільшої країни в регіоні  
- Назва найменшої країни в регіоні  
- Населення найменшої країни в регіоні  

## Додаткові можливості (реалізовано)

- Використання асинхронних бібліотек (aiohttp, asyncpg).
- Парсинг також з https://statisticstimes.com/demographics/countries-by-population.php та третього джерела; перемикання джерела — через змінну оточення.
