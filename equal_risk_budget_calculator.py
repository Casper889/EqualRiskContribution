from fetch_covariance_matrix import CovarianceMatrixReader
import random
import numpy as np
from scipy.optimize import minimize

sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer Goods', 'Energy', 'Utilities', 'Real Estate', 'Materials', 'Industrials', 'Telecommunications']
baseline_weights = np.full(len(sectors), 1 / len(sectors))


def select_sectors(sectors, number=4):
    return random.sample(sectors, number)

# Function to adjust weights
def adjust_weights(selected_sectors, baseline_weights, adjustment=0.1):
    adjusted_weights = baseline_weights.copy()
    for sector in selected_sectors['overweight']:
        index = sectors.index(sector)
        adjusted_weights[index] += adjustment
    for sector in selected_sectors['underweight']:
        index = sectors.index(sector)
        adjusted_weights[index] -= adjustment
    return adjusted_weights

# Function to calculate active risk
def calculate_active_risk(weights, covariance_matrix):
    portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
    return np.sqrt(portfolio_variance)

# Optimization function to equalize active risk
def optimize_weights(selected_sectors, baseline_weights, covariance_matrix):
    # Initial guess (equal weights for selected sectors)
    initial_weights = adjust_weights(selected_sectors, baseline_weights)
    
    # Constraints and bounds
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})  # The sum of weights must be 1
    bounds = [(0, 1) for _ in range(len(sectors))]  # Weights between 0 and 1
    
    # Objective function to minimize the difference in active risk
    def objective(weights):
        return np.std([calculate_active_risk(weights, covariance_matrix) for sector in selected_sectors])
    
    # Optimization
    result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

# Example usage
selected_sectors = {
    'overweight': select_sectors(sectors),
    'underweight': select_sectors(sectors)
}

reader = CovarianceMatrixReader('data.db')
covariance_matrix = reader.read_covariance_matrix('20240101')

if __name__ == '__main__':
    adjusted_weights = optimize_weights(selected_sectors, baseline_weights, covariance_matrix)
    print(adjusted_weights)
    print(calculate_active_risk(adjusted_weights, covariance_matrix))
    print(calculate_active_risk(baseline_weights, covariance_matrix))