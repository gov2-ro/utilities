import csv
import sqlite3
import requests
import time, socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse

db_file = 'data/gov-sites.db'
table_name = 'site_info'
url_list_file = 'data/subdomenii-gov.ro-clean.csv'
zitimeout = 4
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
}

def create_table_if_not_exists(connection):
    cursor = connection.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            page_title TEXT,
            og_description TEXT,
            wp_json BOOLEAN,
            is_wp BOOLEAN,
            response_time REAL,
            page_size INTEGER,
            ssl BOOLEAN,
            fetch_date TEXT,
            ip TEXT
        )
    ''')
    connection.commit()

def insert_data(connection, data):
    cursor = connection.cursor()
    cursor.execute(f'''
        INSERT INTO {table_name} (url, page_title, og_description, wp_json, is_wp, response_time, page_size, ssl, fetch_date, ip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    connection.commit()

def get_page_info(url):
    try:
        response = requests.get(url, headers=headers, timeout=zitimeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string if soup.title else "No Title"
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_description = og_description['content'] if og_description else "No OG Description"
        return page_title, og_description
    except requests.exceptions.RequestException as e:
        return str(e), None

def check_wp(url):
    try:
        wp_json_url = f'{url}/wp-json/'
        wp_json_response = requests.get(wp_json_url, timeout=10)
        wp_json = wp_json_response.status_code == 200 and \
                  wp_json_response.headers['Content-Type'] == 'application/json; charset=UTF-8'

        wp_content_response = requests.get(f'{url}/wp-content/', timeout=10)
        is_wp = 'wp-content' in wp_content_response.text
        return wp_json, is_wp
    except requests.exceptions.RequestException:
        return False, False

def get_performance(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        response_time = end_time - start_time
        page_size = len(response.content) if response.status_code == 200 else -1
        return response_time, page_size
    except requests.exceptions.RequestException:
        return -1, -1

def get_ssl_and_ip(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        fetch_date = time.strftime('%Y-%m-%d %H:%M:%S')
        ip = socket.gethostbyname(domain)
        ssl = parsed_url.scheme == 'https'
        return ssl, fetch_date, ip
    except socket.gaierror:
        return False, None, None

with open(url_list_file, 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)
    urls = [row[0] for row in csv_reader]

connection = sqlite3.connect(db_file)

create_table_if_not_exists(connection)

for url in urls:
    print(url)
    url_with_protocol = url if url.startswith(('http://', 'https://')) else f'http://{url}'
    page_title, og_description = get_page_info(url_with_protocol)
    wp_json, is_wp = check_wp(url_with_protocol)
    response_time, page_size = get_performance(url_with_protocol)
    ssl, fetch_date, ip = get_ssl_and_ip(url_with_protocol)

    data = (url, page_title, og_description, wp_json, is_wp, response_time, page_size, ssl, fetch_date, ip)
    insert_data(connection, data)
    print(page_title + ' ' + str(response_time) + ' ' + str(page_size) + ' ' + str(ssl))
connection.close()
