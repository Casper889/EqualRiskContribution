import pandas as pd
import pdblp
import glob
import os
from datetime import datetime

# Initialize Bloomberg connection
con = pdblp.BCon(debug=False, port=8194, timeout=50000)
con.start()

# Directory containing all CSV files
directory_path = os.getcwd()  # Adjust to your directory

# Define a function to load weight data from each CSV file in the directory
def load_weights_from_directory(directory_path):
    all_files = glob.glob(os.path.join(directory_path, "*.csv"))
    weight_data = pd.DataFrame()
    
    for file_path in all_files:
        # Extract the date from the filename (assuming format is consistent with your example)
        date_str = file_path.split('-')[-3] + '-' + file_path.split('-')[-2] + '-' + file_path.split('-')[-1].replace('.csv', '')
        date = pd.to_datetime(date_str)
        
        # Read each CSV file and select relevant columns
        df = pd.read_csv(file_path)
        df['Date'] = date
        df = df[['Date', 'SEDOL', 'Weight']]  # Only keep necessary columns
        weight_data = pd.concat([weight_data, df])
        
    return weight_data

# Load all weights
weight_data = load_weights_from_directory(directory_path)

# Fetch daily price data without dividends for each SEDOL
def fetch_daily_price_returns(sedols, start_date, end_date):
    # Use overrides to exclude dividends from price returns
    overrides = [('CshAdjAbnormal', False), ('CapChg', False), ('CshAdjNormal', False)]  # Ensures price-only returns
    
    # Dictionary to store data for each SEDOL
    data_dict = {}
    
    for sedol in sedols:
        # Add the "SEDOL" prefix as needed
        formatted_sedol = f"/sedol1/{sedol}"
        try:
            # Fetch data for each SEDOL
            data = con.bdh(formatted_sedol, 'PX_LAST', start_date.replace("-",""), end_date.replace("-",""), elms=overrides)
            data.columns = [sedol]  # Rename column to SEDOL identifier for merging
            data_dict[sedol] = data
        except Exception as e:
            print(f"Error fetching data for SEDOL {sedol}: {e}")

    # Concatenate all data into a single DataFrame
    combined_data = pd.concat(data_dict.values(), axis=1)
    combined_data.index.name = 'Date'
    combined_data.columns.name = 'SEDOL'
    
    # Stack the DataFrame to convert to a long format, if needed
    data = combined_data.stack().reset_index()
    data.columns = ['Date', 'SEDOL', 'Price']
    
    # Pivot back to a wide format if required by later processing
    data = data.pivot(index='Date', columns='SEDOL', values='Price')
    
    return data

# Extract unique SEDOLs and set start and end dates for price data fetching
unique_sedols = weight_data['SEDOL'].unique().tolist()
start_date = weight_data['Date'].min().strftime('%Y-%m-%d')
end_date = weight_data['Date'].max().strftime('%Y-%m-%d')
price_data = fetch_daily_price_returns(unique_sedols, start_date, end_date)

# Calculate daily returns for each SEDOL
daily_returns = price_data.pct_change()

# Ensure Date columns are in datetime format
weight_data['Date'] = pd.to_datetime(weight_data['Date'])
daily_returns.index = pd.to_datetime(daily_returns.index)

# Map monthly weights to daily data by forward filling
weight_data = weight_data.set_index(['Date', 'SEDOL']).unstack().ffill().stack()

# Reshape weight_data to have a single Date index with each SEDOL as a column
weight_data = weight_data.unstack(level='SEDOL')
weight_data.columns = weight_data.columns.droplevel(0)  # Remove the redundant level in column names

daily_weights = weight_data.reindex(pd.to_datetime(daily_returns.index), method='ffill')

# Compute daily portfolio returns
portfolio_daily_returns = (daily_returns * daily_weights).sum(axis=1)

# Save or display the portfolio's daily returns
portfolio_daily_returns.to_csv('portfolio_daily_returns.csv')
print(portfolio_daily_returns)
