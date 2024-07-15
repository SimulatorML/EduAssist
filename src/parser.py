import requests
from bs4 import BeautifulSoup
import json
import time

def fetch_olympiad_page(url):
    """Загружает HTML-содержимое по предоставленному URL.

    :param str url: URL веб-страницы для загрузки.
    :rtype str: HTML-содержимое веб-страницы.
    """
    print(f"Загрузка URL: {url}")
    response = requests.get(url)
    response.raise_for_status()  # Проверка наличия ошибок при запросе
    return response.content

def extract_olympiad_data(html):
    """Извлекает данные об олимпиаде из предоставленного HTML-содержимого.

    :param str html: HTML-содержимое веб-страницы.
    :rtype dict: Разобранные данные, включающие детали олимпиады.
    """
    soup = BeautifulSoup(html, 'html.parser')
    parsed_data = {}

    # Извлечение заголовка
    title = soup.title.string.strip() if soup.title else None
    if title:
        parsed_data['title'] = title

    # Извлечение мета-описания
    meta_description = soup.find('meta', {'name': 'description'})
    if meta_description:
        parsed_data['description'] = meta_description['content']

    # Извлечение мета-ключевых слов
    meta_keywords = soup.find('meta', {'name': 'keywords'})
    if meta_keywords:
        parsed_data['keywords'] = meta_keywords['content']

    # Извлечение мета-изображения
    meta_image = soup.find('meta', {'property': 'og:image'})
    if meta_image:
        parsed_data['image'] = meta_image['content']

    # Извлечение мета-URL
    meta_url = soup.find('meta', {'property': 'og:url'})
    if meta_url:
        parsed_data['url'] = meta_url['content']

    # Извлечение названий событий и дат
    events = []
    events_rows = soup.select('table tr')
    for row in events_rows:
        event_name_div = row.find('div', class_='event_name')
        event_date_link = row.find_all('a')
        if event_name_div and len(event_date_link) > 1:
            event_name = event_name_div.get_text(strip=True)
            event_date = event_date_link[1].get_text(strip=True)
            events.append({'name': event_name, 'date': event_date})

    if events:
        parsed_data['events'] = events

    return parsed_data

def fetch_all_olympiad_links(main_url):
    """Загружает все ссылки на олимпиады с главной страницы.

    :param str main_url: URL главной страницы со списком всех олимпиад.
    :rtype list: Список URL для каждой страницы олимпиады.
    """
    html = fetch_olympiad_page(main_url)
    soup = BeautifulSoup(html, 'html.parser')
    
    print("Анализ HTML главной страницы...")
    
    olympiad_links = []
    # Нахождение всех ссылок
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/activity/' in href:
            full_url = f'https://olimpiada.ru{href}'
            olympiad_links.append(full_url)

    return olympiad_links

def main():
    main_url = 'https://olimpiada.ru/activities'

    # Загружаем все ссылки на олимпиады
    olympiad_links = fetch_all_olympiad_links(main_url)
    print(f"Found {len(olympiad_links)} olympiad links")

    # Загружаем и разбираем данные для каждой олимпиады
    all_olympiad_data = []
    for link in olympiad_links:
        try:
            html = fetch_olympiad_page(link)
            parsed_data = extract_olympiad_data(html)
            all_olympiad_data.append(parsed_data)
        except Exception as e:
            print(f"Error fetching data from {link}: {e}")
        time.sleep(1)  # Во избежание блокировки сайта из-за слишком большого количества запросов

    # Сохраняем все данные в JSON-файл
    with open('all_olympiads.json', 'w', encoding='utf-8') as json_file:
        json.dump(all_olympiad_data, json_file, ensure_ascii=False, indent=2)

    print("Data has been saved to all_olympiads.json")

if __name__ == '__main__':
    main()

