import csv
import sqlite3
import time
import socket
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

db_file = '../data/gov-sites.db'
table_name = 'site_info'
url_list_file = '../data/subdomenii-gov.ro-clean.csv'
zitimeout = 10  # Increase the timeout for Selenium
gecko_driver_path = '/usr/local/bin/geckodriver'  # Path to GeckoDriver executable
firefox_options = Options()
firefox_options.headless = True  # Run Firefox in headless mode (without a visible GUI)

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

def get_page_info(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, zitimeout).until(EC.presence_of_element_located((By.TAG_NAME, "title")))
        page_title = driver.title
        og_description = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute("content")
        return page_title, og_description
    except:
        return "No Title", "No OG Description"

def check_wp(url, driver):
    try:
        wp_json_url = f'{url}/wp-json/'
        driver.get(wp_json_url)
        WebDriverWait(driver, zitimeout).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
        wp_json = "application/json" in driver.find_element(By.TAG_NAME, "pre").text

        wp_content_response = requests.get(f'{url}/wp-content/', timeout=10)
        is_wp = 'wp-content' in driver.page_source
        return wp_json, is_wp
    except:
        return False, False

def get_performance(url, driver):
    try:
        start_time = time.time()
        driver.get(url)
        end_time = time.time()
        response_time = end_time - start_time
        page_size = len(driver.page_source) if driver.title != "" else -1
        return response_time, page_size
    except:
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

connection = sqlite3.connect(db_file)

create_table_if_not_exists(connection)

with webdriver.Firefox(service=FirefoxService(executable_path=gecko_driver_path), options=firefox_options) as driver:
    with open(url_list_file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        urls = [row[0] for row in csv_reader]

    for url in urls:
        print(url)
        url_with_protocol = url if url.startswith(('http://', 'https://')) else f'http://{url}'
        page_title, og_description = get_page_info(url_with_protocol, driver)
        wp_json, is_wp = check_wp(url_with_protocol, driver)
        response_time, page_size = get_performance(url_with_protocol, driver)
        ssl, fetch_date, ip = get_ssl_and_ip(url_with_protocol)

        data = (url, page_title, og_description, wp_json, is_wp, response_time, page_size, ssl, fetch_date, ip)
        insert_data(connection, data)
        try:
            print(page_title + ' ' + str(response_time) + ' ' + str(page_size) + ' ' + str(ssl))
        except:
            print('err: some error')

connection.close()
