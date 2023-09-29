
dbfile = '../data/guess-gender/candidati-alegeri-gender.db'
table_name = "Candidati alegeri RO"
countstep = 5000

# TODO:
# make it simple: break name into parts and detect gender for all 
# todo++ build names from wikipedia

import sqlite3
import gender_guesser.gender_guesser.detector as gender
from nameparser import HumanName


d = gender.Detector()

def process_row(nume):

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

    # cursor.execute(
    #     f"UPDATE '" + table_name +
    #     "' SET firstName = ?, lastName = ?, middleName = ? WHERE Nume = ?",
    #     (semantic_name.first, semantic_name.last, zimiddle, nume))

    if zimiddle and d.get_gender(zimiddle) != 'unknown':
        gender = d.get_gender(zimiddle) + ' ' + d.get_gender(semantic_name.last)
    else:
        gender = d.get_gender(semantic_name.last)

    # if last + middle fail, try to look into first name
    if gender == 'unknown':
        gender = d.get_gender(semantic_name.first) + ' +'

    # cursor.execute("UPDATE '" + table_name + "' SET gender = ? WHERE Nume = ?", (gender, nume))

    name_parts =  {
        "first": semantic_name.first,
        "middle": zimiddle,
        "last": semantic_name.last,
        "gender": gender,
    }

    return name_parts



# Create a connection to the SQLite database
conn = sqlite3.connect(dbfile)

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Step 1: Add a new 'gender' column to the 'Candidati alegeri RO' table
try:
    cursor.execute("ALTER TABLE 'Candidati alegeri RO' ADD COLUMN gender TEXT")
except sqlite3.OperationalError:
    # Column already exists, or table doesn't exist
    pass

# Step 2: Fetch all rows from the table
cursor.execute("SELECT Nume FROM 'Candidati alegeri RO'")
rows = cursor.fetchall()

# Step 3: Loop through each row, apply d.get_gender(), and update the 'gender' column
for row in rows:
    nume = row[0]  # Assuming 'Nume' is the correct column name
    # gender = d.get_gender(nume)
    # cursor.execute("UPDATE 'Candidati alegeri RO' SET gender = ? WHERE Nume = ?", (gender, nume))
    ll = process_row(nume)
    cursor.execute(
        f"UPDATE '" + table_name +
        "' SET firstName = ?, lastName = ?, middleName = ?, gender = ? WHERE Nume = ?",
        (ll['first'], ll['last'], ll['middle'], ll['gender'], nume))

# Step 4: Commit the changes to the database
conn.commit()

# Step 5: Close the cursor and the database connection
cursor.close()
conn.close()
print('done')


