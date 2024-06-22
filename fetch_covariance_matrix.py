import pandas as pd
import sqlite3
import json
import pdb

class CovarianceMatrixReader:
    def __init__(self, db_file):
        self.db_file = db_file

    def read_covariance_matrix(self, date=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        if date is None:
            # Fetch all covariance matrices from the database
            cursor.execute("SELECT * FROM covariance_matrices")
            dfs = cursor.fetchall()
            conn.close()
            return dfs
        else:
            # Fetch the covariance matrix with the specified matrix_id from the database
            cursor.execute("SELECT cov_matrix FROM covariance_matrices WHERE date=?", (date,))
            dfs = cursor.fetchall()
            conn.close()
            return pd.DataFrame(json.loads(dfs[0][0]))
    
if __name__ == "__main__":
    reader = CovarianceMatrixReader('data.db')
    covariance_matrices = reader.read_covariance_matrix('20240101')
    pdb.set_trace()
    print(covariance_matrices)