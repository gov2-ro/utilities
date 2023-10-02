import requests
import csv
from bs4 import BeautifulSoup

search = 'CONSILIUL NAŢIONAL PENTRU COMBATEREA DISCRIMINĂRII'
url = 'https://www.google.com/search'

headers = {
	'Accept' : '*/*',
	'Accept-Language': 'en-US,en;q=0.5',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82',
}
parameters = {'q': search}

html_content = requests.get(url, headers = headers, params = parameters).text

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find the div with id="search"
search_div = soup.find('div', id='search')

# Find the div with data-async-context starting with "query:"
query_div = search_div.find('div', {'data-async-context': lambda x: x and x.startswith('query:')})

# Initialize lists to store URLs and titles
urls = []
titles = []

print(str(query_div))
breakpoint()
# Loop through immediate children divs
for div in query_div.find_all('div', recursive=False):
    # Find the first link and its text
    link = div.find('a', href=True)
    if link:
        url = link['href']
        title = link.find('h3').get_text() if link.find('h3') else ''
        urls.append(url)
        titles.append(title)

# Create a CSV file and write the data
with open('search_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['url', 'title']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for url, title in zip(urls, titles):
        writer.writerow({'url': url, 'title': title})

print("Data saved to 'search_results.csv'")
