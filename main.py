import requests
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def creation_table(all_stats, title):
    table = [["Язык програмирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"], ]
    for language, stats in all_stats:
        table_stats = [language] + list(stats.values())
        table.append(table_stats)
    table_avg_salary = AsciiTable(table, title)
    return table_avg_salary.table


def predict_rub_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        expected_salary = None
    elif salary_from and salary_to:
        expected_salary = (salary_from + salary_to) / 2
    elif not salary_from:
        expected_salary = salary_to * 0.8
    else:
        expected_salary = salary_from * 1.2
    return expected_salary


def search_vacancy_hh(languages):
    all_stats = {}
    for language in languages:
        all_salary = []
        for page in count(0):
            url = 'https://api.hh.ru/vacancies'
            params = {
                'text': language,
                'area': '1',
                'page': page,
                'period': 1
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            vacancies_found = response.json()['found']
            vacancies = response.json()['items']
            pages = response.json()['pages']
            for vacancy in vacancies:
                salary = vacancy['salary']
                if not salary or salary['currency'] != 'RUR':
                    expected_salary = None
                else:
                    expected_salary = predict_rub_salary(salary['from'], salary['to'])
                if expected_salary:
                    all_salary.append(expected_salary)

            if page >= pages - 1:
                break
        vacancies_processed = len(all_salary)
        average_salary = int(sum(all_salary) / vacancies_processed)
        all_stats[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary

        }
    return all_stats


def search_vacancy_sj(languages, sj_token):
    all_stats_sj = {}
    url = 'https://api.superjob.ru/2.0/vacancies/'
    for language in languages:
        all_salary = []
        for page in count(0):

            headers = {
                "X-Api-App-Id": sj_token
            }
            params = {
                'keyword': f'{language}',
                'town': 'Москва',
                'catalogues': 48,
                'page': 0,
                'currency': 'rub',
                'count': 100
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            vacancies_found = response.json()['total']
            vacancies = response.json()['objects']
            for vacancy in vacancies:
                expected_salary = predict_rub_salary(vacancy['payment_from'], vacancy['payment_to'])
                if expected_salary:
                    all_salary.append(expected_salary)
            if not response.json()['more']:
                break
        vacancies_processed = len(all_salary)
        if vacancies_processed:
            average_salary = int(sum(all_salary) / vacancies_processed)
        if vacancies_found:
            all_stats_sj[language] = {
                "vacancies_found": vacancies_found,
                "vacancies_processed": vacancies_processed,
                "average_salary": average_salary
            }

    return all_stats_sj


def main():
    load_dotenv()
    sj_token = os.environ['sj_token']
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

    hh_statistics = search_vacancy_hh(languages).items()
    sj_statistics = search_vacancy_sj(languages, sj_token).items()
    hh_table = creation_table(hh_statistics,'hh Moscow')
    sj_table = creation_table(sj_statistics,'sj Moscow')

    print(hh_table)
    print(sj_table)


if __name__ == '__main__':
    main()
