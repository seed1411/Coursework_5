from typing import Any
import psycopg2
import requests


def get_employers_and_vacancies_info(employers_id: list[int]) -> list[dict[str, Any]]:
    """
    Загрузка информации об организациях и имеющихся у них вакансий из HeadHunter'а
    :param employers_id: ID организации
    :return: список с организациями и их вакансиями
    """
    page_indicator = 0  # Индикатор для подсчета процентов выполнения загрузки
    data = []
    print('\nПодождите идет загрузка данных...')
    for employer_id in employers_id:
        response_1 = requests.get(f'https://api.hh.ru/employers/{employer_id}')
        employer = response_1.json()
        employer_info = {
            'id': employer.get('id'),
            'name': employer.get('name'),
            'area': employer.get('area').get('name'),
            'alternate_url': employer.get('alternate_url'),
            'site_url': employer.get('site_url'),
            'open_vacancies': employer.get('open_vacancies')
        }

        vacancies_list = []
        params = {'text': '', 'page': 0, 'per_page': '100', 'employer_id': employer_id}
        indicator = 3  # Изменяемый параметр, в зависимости от нужного объема выводимых вакансий
        while params['page'] != indicator:
            response_2 = requests.get(f'https://api.hh.ru/vacancies', params=params)
            vacancies = response_2.json()['items']
            for vacancy in vacancies:
                vacancy_info = {
                    'id': vacancy.get('id'),
                    'vacancy': vacancy.get('name'),
                    'published_at': vacancy.get('published_at'),
                    'employment': vacancy.get('employment').get('name'),
                    'schedule': vacancy.get('schedule').get('name'),
                    'type': vacancy.get('type').get('name'),
                    'area': vacancy.get('area').get('name'),
                    'alternate_url': vacancy.get('alternate_url')
                }
                if vacancy['salary'] is None or vacancy['salary']['from'] is None:
                    vacancy_info['salary'] = None
                    vacancy_info['currency'] = None
                elif vacancy['salary']['from']:
                    vacancy_info['salary'] = vacancy['salary']['from']
                    vacancy_info['currency'] = vacancy['salary']['currency']
                vacancies_list.append(vacancy_info)
            params['page'] += 1
            page_indicator += 1
            print(f'Загружено {round(page_indicator * 100 / (indicator * len(employers_id)), 1)} % данных.')
        data.append({
            'employer': employer_info,
            'vacancies': vacancies_list
        })
    return data


def create_database(database_name: str, params: dict) -> None:
    """
    Создание базы данных и таблиц employers, vacancies
    :param database_name: название создаваемой базы
    :param params: Настройки базы данных
    """
    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS {database_name}')
        cur.execute(f'CREATE DATABASE {database_name}')
    print(f"База данных {database_name} создана!")
    conn.close()


    with psycopg2.connect(dbname=database_name, **params) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE employers (
                id_employer INT UNIQUE PRIMARY KEY,
                employer_name VARCHAR(50) NOT NULL,
                area VARCHAR(50),
                employer_page VARCHAR(100),
                employer_website VARCHAR(100),
                open_vacancies INT
                );
            ''')
    print('Таблица employers создана!')
    conn.close()


    with psycopg2.connect(dbname=database_name, **params) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE vacancies (
                id_vacancy INT UNIQUE PRIMARY KEY,
                id_employer INT REFERENCES employers(id_employer),
                vacancy_name VARCHAR(255) NOT NULL,
                salary INT,
                currency VARCHAR(10),
                published_at DATE,
                employment VARCHAR(50),
                url_vacancy VARCHAR,
                schedule VARCHAR(50),
                type VARCHAR(50),
                area VARCHAR(50)
                );
            ''')
    print('Таблица vacancies создана!')
    conn.close()



def save_data_in_database(database_name: str, params: dict, data: list[dict[str, Any]]) -> None:
    """
    Добавление информации в базу данных
    :param database_name: название подключаемой базы данных
    :param params: словарь с параметрами базы данных
    :param data: информация для внесения в базу
    """
    with psycopg2.connect(dbname=database_name, **params) as conn:
        with conn.cursor() as cur:
            for value in data:
                employer = value['employer']
                vacancies = value['vacancies']
                cur.execute('''
                INSERT INTO employers (id_employer, employer_name, area, employer_page, employer_website, open_vacancies) 
                VALUES (%s, %s, %s, %s, %s, %s)''',
                            (employer['id'], employer['name'], employer['area'], employer['alternate_url'],
                             employer['site_url'], employer['open_vacancies']))

                for vacancy in vacancies:
                    cur.execute('''
                    INSERT INTO vacancies (id_vacancy, id_employer, vacancy_name, salary, currency, published_at, employment, url_vacancy, schedule, type, area) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                                (vacancy['id'], employer['id'], vacancy['vacancy'], vacancy['salary'],
                                 vacancy['currency'], vacancy['published_at'], vacancy['employment'], vacancy['alternate_url'],
                                 vacancy['schedule'], vacancy['type'], vacancy['area']))
    print('Данные добавлены в базу данных!')
    conn.close()




