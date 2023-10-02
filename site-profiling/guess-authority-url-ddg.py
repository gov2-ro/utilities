import pandas as pd
from duckduckgo_search import DDGS
from tqdm import tqdm
import time, sqlite3

file_path = '../../data/orgs/orgnames.csv'
target_db = '../../data/orgs/orgsearchddg.db'
nameCol = 'Denumire'
extra_search_params=' site:*.ro '
# extra_search_params=' facebook '
sleep = 0.3
max_results = 7

df = pd.read_csv(file_path)

db_connection = sqlite3.connect(target_db)
cursor = db_connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        needle TEXT,
        title TEXT,
        href TEXT,
        body TEXT
    )
''')

# Counter to track rows processed and trigger saving to the database
row_counter = 0

with tqdm(total=len(df)) as pbar:
    for index, row in df.iterrows():
        needle = row[nameCol]        
        tqdm.write(f'> {needle}')
        try:
            with DDGS() as ddgs:
                results = [(needle, r['title'], r['href'], r['body']) for r in ddgs.text(needle + ' site:*.ro ', max_results=max_results)]
                # Add the results to the database
                cursor.executemany('INSERT INTO results VALUES (?, ?, ?, ?)', results)
        except Exception as e:
            print(f"An error occurred while processing '{needle}': {str(e)}")
     
        # with DDGS() as ddgs:
        #     results = [(needle, r['title'], r['href'], r['body']) for r in ddgs.text(needle + extra_search_params, max_results=max_results)]
        #     # Add the results to the database
        #     cursor.executemany('INSERT INTO results VALUES (?, ?, ?, ?)', results)
            
        pbar.update(1)
        time.sleep(sleep)
        
        row_counter += 1
        if row_counter == 5:
            db_connection.commit()  # Save every 50 rows
            row_counter = 0
            time.sleep(sleep + 2)

# Commit any remaining changes and close the database connection
db_connection.commit()
db_connection.close()

tqdm.write('DONE')
