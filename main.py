from functions import get_employers_and_vacancies_info, create_database, save_data_in_database
from config import config


def main():
    """
    Запуск скрипта программы
    """
    employers_id = [1740, 78638, 3529, 4181, 740, 80, 39305, 907345, 49357, 1942330]
    data = get_employers_and_vacancies_info(employers_id)
    params = config()
    create_database('headhunter', params)
    save_data_in_database('headhunter', params, data)


if __name__ == '__main__':
    main()