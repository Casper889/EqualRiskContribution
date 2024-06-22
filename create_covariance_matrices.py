import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import json
import math
import pdb
from tqdm import tqdm

class CovarianceMatrixCalculator:
    def __init__(self, db_path, half_life_days=252):
        self.db_path = db_path
        self.half_life_days = half_life_days
        self.decay_factor = self.calculate_decay_factor()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.returns_df = self.read_returns_from_db()

    def calculate_decay_factor(self):
        # Calculate the decay factor based on the half-life
        return math.exp(-math.log(2) / self.half_life_days)

    def read_returns_from_db(self):
        # Read the returns from the database into a pandas DataFrame
        query = "SELECT * FROM returns"
        returns_df = pd.read_sql_query(query, self.conn)
        returns_df['date'] = pd.to_datetime(returns_df['date'])  # Convert the date column to datetime type
        return returns_df

    def calculate_daily_covariance_matrix(self, date):
        # Filter the returns for the given date
        daily_returns = self.returns_df[self.returns_df['date'] <= date]

        daily_returns = daily_returns.pivot(index='date', columns='sector', values='return')
        
        # Calculate the covariance matrix from the weighted returns
        cov_matrix = daily_returns.ewm(halflife=self.half_life_days).cov() * 252  # Multiply by 252 to annualize the covariance matrix

        return cov_matrix.droplevel(0)

    def save_covariance_matrix(self, date, cov_matrix):
        cov_matrix_str = json.dumps(cov_matrix.to_dict())
        self.cursor.execute("INSERT INTO covariance_matrices (date, cov_matrix) VALUES (?, ?)",
                            (date.strftime('%Y%m%d'), cov_matrix_str))
        
    def calculate_and_save_cov_matrices(self):
        # Ensure the covariance_matrices table exists
        self.create_covariance_matrices_table()

        # Get unique dates from the returns DataFrame
        unique_dates = self.returns_df['date'].unique()

        # Iterate through each unique date
        for date in tqdm(unique_dates):

            # Calculate the daily covariance matrix for the current date
            cov_matrix = self.calculate_daily_covariance_matrix(date)

            # Save the calculated covariance matrix to the database
            self.save_covariance_matrix(date, cov_matrix)

        # Close the database connection after saving all covariance matrices
        self.close_connection()

    def create_covariance_matrices_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS covariance_matrices (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL UNIQUE,
            cov_matrix TEXT NOT NULL
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def close_connection(self):
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    db_path = "/Users/casper/Nextcloud2/ERC/data.db"  # Replace with the actual path to the database file
    calculator = CovarianceMatrixCalculator(db_path)
    calculator.calculate_and_save_cov_matrices()