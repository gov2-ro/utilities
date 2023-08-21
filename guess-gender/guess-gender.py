# breaks name into first / last, guesses gender
# uses:
#   https://github.com/derek73/python-nameparser
#   https://github.com/lead-ratings/gender-guesser/

import sqlite3
from tqdm import tqdm
from unidecode import unidecode
from nameparser import HumanName
import gender_guesser.gender_guesser.detector as gender


dbfile = '../data/guess-gender/candidati-alegeri-gender.db'
table_name = "Candidati alegeri RO"
countstep = 5000

d = gender.Detector()
conn = sqlite3.connect(dbfile)
cursor = conn.cursor()

try:
    cursor.execute(f"ALTER TABLE '{table_name}' ADD COLUMN firstName TEXT")
    conn.commit()
    print("1 Columns added successfully.")
except sqlite3.Error as e:
    # print(f"Error: {e}")
    pass

try:
    cursor.execute(f"ALTER TABLE '{table_name}' ADD COLUMN lastName TEXT")
    conn.commit()
    print("1 Columns added successfully.")
except sqlite3.Error as e:
    # print(f"Error: {e}")
    pass

try:
    cursor.execute(f"ALTER TABLE '{table_name}' ADD COLUMN middleName TEXT")
    conn.commit()
    print("1 Columns added successfully.")
except sqlite3.Error as e:
    # print(f"Error: {e}")
    pass

try:
    cursor.execute(f"ALTER TABLE '{table_name}' ADD COLUMN gender TEXT")
    conn.commit()
    print("1 Columns added successfully.")
except sqlite3.Error as e:
    # print(f"Error: {e}")
    pass

# Count the total number of rows in the table
cursor.execute("SELECT COUNT(*) FROM '" + table_name + "' ")
total_rows = cursor.fetchone()[0]

progress_bar = tqdm(total=total_rows, desc="Processing Rows", unit=" row")
tqdm.write(total_rows + ' rows')

def process_row(row):

    nume = row[0]
    semantic_name = HumanName(nume)
    # break into names, see if >50% known gender
    # if unknown, assume hungarian, reverse name, write to db
    # FIXME: what to do when can't guess name parts?!
    #   1 if nume prenume, check gender for both and choose the one w gender
    #   2 catch <familie> <prenume1> - <prenume2>
    # remove unidecode?!

    if semantic_name.middle and semantic_name.middle != 'unknown':
        zimiddle = semantic_name.middle.replace('–', '-')
        zimiddle = zimiddle.replace(' - ', '')
        zimiddle = zimiddle.replace('-', ' ')
        zimiddle = zimiddle.strip()

        if zimiddle == 'unknown':
            zimiddle = ''

    else:
        zimiddle = ''

    cursor.execute(
        f"UPDATE '" + table_name +
        "' SET firstName = ?, lastName = ?, middleName = ? WHERE Nume = ?",
        (semantic_name.first, semantic_name.last, zimiddle, nume))

    if zimiddle and d.get_gender(zimiddle) != 'unknown':
        gender = d.get_gender(zimiddle) + ' ' + d.get_gender(semantic_name.last)
    else:
        gender = d.get_gender(semantic_name.last)

    # if last + middle fail, try to look into first name
    if gender == 'unknown':
        gender = d.get_gender(semantic_name.first) + ' +'

    cursor.execute("UPDATE '" + table_name + "' SET gender = ? WHERE Nume = ?", (gender, nume))

    pass


# tqdm batches
""" cursor.execute("SELECT Nume FROM '" + table_name + "'")

while True:
    rows = cursor.fetchmany(500)
    if not rows:
        break
    for row in rows:
        process_row(row)
        progress_bar.update(len(rows))  # Increment the progress bar
 """

# one by one
cursor.execute("SELECT Nume FROM '" + table_name + "'")
rows = cursor.fetchall()
xsteps = 0
for row in rows:
    nume = row[0]  # Assuming 'Nume' is the correct column name
    process_row(row)
    xsteps +=1
    if xsteps >= countstep:
        progress_bar.update(countstep)
        xteps = 0 
        conn.commit()


cursor.close()
conn.close()

progress_bar.close()

print('DONE')