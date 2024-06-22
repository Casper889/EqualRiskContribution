import sqlite3
import random
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

class ReturnSeriesGenerator:
    def __init__(self, db_file):
        self.db_file = db_file

    def generate_return_series(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS returns
                          (date TEXT, sector TEXT, return REAL)''')

        # List of sectors and their variances
        sectors_variances = {
            'Technology': 0.02, 'Healthcare': 0.015, 'Finance': 0.018, 'Consumer Goods': 0.013,
            'Energy': 0.02, 'Utilities': 0.01, 'Real Estate': 0.017, 'Materials': 0.016,
            'Industrials': 0.019, 'Telecommunications': 0.014
        }

        # Generate and insert returns into the database
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        current_date = start_date

        annual_skew = 0.05
        daily_skew = annual_skew / 252  # Assuming 252 trading days in a year

        while current_date <= end_date:
            for sector, variance in sectors_variances.items():
                # Generate a random return with a 5% positive bias
                return_value = random.gauss(daily_skew, variance / 252)  # Convert annual variance to daily

                # Insert the return into the database
                cursor.execute("INSERT INTO returns VALUES (?, ?, ?)",
                    (current_date.strftime('%Y-%m-%d'), sector, return_value))

            # Move to the next day
            current_date += timedelta(days=1)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

# Usage example
if __name__ == "__main__":
    db_path = "/Users/casper/Nextcloud2/ERC/data.db"  # Replace with the actual path to the database file
    generator = ReturnSeriesGenerator('data.db')
    generator.generate_return_series()