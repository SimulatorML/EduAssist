import requests
from bs4 import BeautifulSoup
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_olympiad_page(url):
    print(f"Loading URL: {url}")
    return requests.get(url).content

def extract_olympiad_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    parsed_data = {}

    meta_tags = {'description': 'name', 'keywords': 'name', 'image': 'property', 'url': 'property'}
    for key, attr in meta_tags.items():
        meta = soup.find('meta', {attr: f"og:{key}" if key in ['image', 'url'] else key})
        if meta:
            parsed_data[key] = meta.get('content')

    if soup.title:
        parsed_data['title'] = soup.title.string.strip()

    events = []
    for row in soup.select('table tr'):
        event_name = row.find('div', class_='event_name')
        event_date = row.find_all('a')
        if event_name and len(event_date) > 1:
            events.append({
                'name': event_name.get_text(strip=True),
                'date': event_date[1].get_text(strip=True)
            })

    if events:
        parsed_data['events'] = events

    return parsed_data

def fetch_all_olympiad_links(main_url):
    soup = BeautifulSoup(fetch_olympiad_page(main_url), 'html.parser')
    return [f'https://olimpiada.ru{link["href"]}' for link in soup.find_all('a', href=True) if '/activity/' in link['href']]

def process_olympiad(link):
    try:
        return extract_olympiad_data(fetch_olympiad_page(link))
    except Exception as e:
        print(f"Error fetching data from {link}: {e}")
        return None

def dict_to_string(data):
    return "\n".join(f"{key}: {value}" for key, value in data.items() if key != 'events') + \
           "\nEvents:\n" + "\n".join(f"- {event['name']} ({event['date']})" for event in data.get('events', []))

def main():
    main_url = 'https://olimpiada.ru/activities'
    olympiad_links = fetch_all_olympiad_links(main_url)
    print(f"Found {len(olympiad_links)} olympiad links")

    all_olympiad_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_link = {executor.submit(process_olympiad, link): link for link in olympiad_links}
        for future in as_completed(future_to_link):
            data = future.result()
            if data:
                all_olympiad_data.append(data)
            time.sleep(0.2)

    # Transform the list of dictionaries to a list of strings
    olympiad_strings = [dict_to_string(data) for data in all_olympiad_data]

    # Save the list of strings to a JSON file
    with open('all_olympiads_strings.json', 'w', encoding='utf-8') as json_file:
        json.dump(olympiad_strings, json_file, ensure_ascii=False, indent=2)

    print("Data has been saved to all_olympiads_strings.json")
    
    return olympiad_strings

if __name__ == '__main__':
    main()
