import requests
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


SEARCH_PERIOD = 1
CITY_CODE = 1
JOB_ID = 48

def create_table(all_stats, title):
    table = [["Язык програмирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"], ]
    for language, stats in all_stats:
        table_stats = [language] + list(stats.values())
        table.append(table_stats)
    avg_salary_table = AsciiTable(table, title)
    return avg_salary_table.table


def predict_salary_rub(salary_from, salary_to):
    if not salary_from and not salary_to:
        expected_salary = None
    elif salary_from and salary_to:
        expected_salary = (salary_from + salary_to) / 2
    elif not salary_from:
        expected_salary = salary_to * 0.8
    else:
        expected_salary = salary_from * 1.2
    return expected_salary


def get_stats_hh(languages):
    all_stats = {}
    for language in languages:
        all_salaries = []
        for page in count(0):
            url = 'https://api.hh.ru/vacancies'
            params = {
                'text': language,
                'area': CITY_CODE,
                'page': page,
                'period': SEARCH_PERIOD
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            response = response.json()
            vacancies_found = response['found']
            vacancies = response['items']
            pages = response['pages']
            for vacancy in vacancies:
                salary = vacancy['salary']
                if not salary or salary['currency'] != 'RUR':
                    expected_salary = None
                else:
                    expected_salary = predict_salary_rub(salary['from'], salary['to'])
                if expected_salary:
                    all_salaries.append(expected_salary)

            if page >= pages - 1:
                break
        vacancies_processed = len(all_salaries)
        if vacancies_processed:
            average_salary = int(sum(all_salaries) / vacancies_processed)
        else:
            average_salary = 0

        all_stats[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary

        }
    return all_stats


def get_stats_sj(languages, sj_token):
    all_stats_sj = {}
    url = 'https://api.superjob.ru/2.0/vacancies/'
    for language in languages:
        all_salaries = []
        for page in count(0):
            headers = {
                "X-Api-App-Id": sj_token
            }
            params = {
                'keyword': f'{language}',
                'town': 'Москва',
                'catalogues': JOB_ID,
                'page': 0,
                'currency': 'rub',
                'count': 100
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()
            vacancies_found = response['total']
            vacancies = response['objects']
            for vacancy in vacancies:
                expected_salary = predict_salary_rub(vacancy['payment_from'], vacancy['payment_to'])
                if expected_salary:
                    all_salaries.append(expected_salary)
            if not response['more']:
                break
        vacancies_processed = len(all_salaries)
        if vacancies_processed:
            average_salary = int(sum(all_salaries) / vacancies_processed)
        else:
            average_salary = 0
        if vacancies_found:
            all_stats_sj[language] = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }

    return all_stats_sj


def main():
    load_dotenv()
    sj_token = os.environ['SJ_TOKEN']
    languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'C#',
        'Swift',
        'TypeScript'
    ]

    hh_statistics = get_stats_hh(languages).items()
    sj_statistics = get_stats_sj(languages, sj_token).items()
    hh_table = create_table(hh_statistics, 'hh Moscow')
    sj_table = create_table(sj_statistics, 'sj Moscow')

    print(hh_table)
    print(sj_table)


if __name__ == '__main__':
    main()