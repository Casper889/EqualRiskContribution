import sqlite3
import random
from datetime import datetime, timedelta

class ReturnSeriesGenerator:
    def __init__(self, db_file):
        self.db_file = db_file

    def generate_return_series(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS returns
                          (date TEXT, return REAL)''')

        # Generate and insert returns into the database
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        current_date = start_date

        while current_date <= end_date:
            # Generate a random return with a 5% positive bias
            return_value = random.uniform(0, 0.05)

            # Insert the return into the database
            cursor.execute("INSERT INTO returns VALUES (?, ?)",
                           (current_date.strftime('%Y-%m-%d'), return_value))

            # Move to the next day
            current_date += timedelta(days=1)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

# Usage example
generator = ReturnSeriesGenerator('returns.db')
generator.generate_return_series()