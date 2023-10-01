import csv, sqlite3, requests, time, socket, datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from email.utils import formatdate
from tqdm import tqdm

db_file = '../data/gov-sites.db'
table_name = 'sites'
url_list_file = '../data/subdomenii-gov.ro-clean.csv'
timeout = 2

days_ago = 4
modified_since_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
modified_since_header = formatdate(modified_since_date.timestamp(), usegmt=True)

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'If-Modified-Since': modified_since_header,
    'If-None-Match': '"848f2-6067ebcfc4f9f-gzip"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

error_count = 0
is_wp_count = 0
wp_json_count = 0

def create_table_if_not_exists(connection):
    cursor = connection.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            page_title TEXT,
            description TEXT,
            og_description TEXT,
            redirected TEXT,
            etag TEXT,
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
        INSERT INTO {table_name} (url, page_title, description, og_description, redirected, etag, wp_json, is_wp, response_time, page_size, ssl, fetch_date, ip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    connection.commit()

def get_page_info(url):
    try:
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Save Etag if present
        etag = response.headers.get('ETag', 'No Etag')

        # Check page encoding and save data accordingly
        encoding = response.encoding
        if encoding == 'ISO-8859-1':
            response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string if soup.title else "No Title"
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_description = og_description['content'] if og_description else "No OG Description"

        # Check if URL has changed due to redirects
        final_url = response.url

        return page_title, og_description, etag, final_url
    except requests.exceptions.RequestException as e:
        global error_count
        error_count += 1
        if not url.startswith('http://www.') and not url.startswith('https://www.'):
            # Try adding "www." to the URL and retry
            new_url = f'http://www.{url}'
            return get_page_info(new_url)
        return 'ERR: ' + str(e), None, None, None


def check_wp(url):
    try:
        wp_json_url = f'{url}/wp-json/'
        wp_json_response = requests.get(wp_json_url, headers=headers, timeout=timeout)
        wp_json = wp_json_response.status_code == 200 and \
                  wp_json_response.headers['Content-Type'] == 'application/json; charset=UTF-8'
        wp_content_response = requests.get(f'{url}/wp-content/', headers=headers, timeout=timeout)
        is_wp = '/wp-content' or '/wp-includes' in wp_content_response.text
        return wp_json, is_wp
    except requests.exceptions.RequestException:
        global error_count
        error_count += 1
        return False, False

def get_performance(url):
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=timeout)
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

with tqdm(total=len(urls), desc="Processing URLs") as pbar:
    for url in urls:
        pbar.update(1)  # Increment progress bar
        pbar.set_postfix(ErrorCount=error_count, IsWPCount=is_wp_count, WPJsonCount=wp_json_count, CurrentlyScraped=url)

        url_with_protocol = url if url.startswith(('http://', 'https://')) else f'http://{url}'
        page_title, og_description, etag, redirected = get_page_info(url_with_protocol)
        wp_json, is_wp = check_wp(url_with_protocol)
        response_time, page_size = get_performance(url_with_protocol)
        ssl, fetch_date, ip = get_ssl_and_ip(url_with_protocol)

        data = (url, page_title, "your_description_value_here", og_description, redirected, etag, wp_json, is_wp, response_time, page_size, ssl, fetch_date, ip)
        insert_data(connection, data)
        try:
            tqdm.write(f' OK: {page_title} {str(response_time)} {str(page_size)} {str(ssl)}')
        except:
            tqdm.write('err: 162')

tqdm.write('done, yay!')

connection.close()

