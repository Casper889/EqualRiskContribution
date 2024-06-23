from fetch_covariance_matrix import CovarianceMatrixReader
import random
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from tqdm import tqdm
from multiprocessing import Pool
import pdb
from fetch_covariance_matrix import CovarianceMatrixReader


sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer Goods', 'Energy', 'Utilities', 'Real Estate', 'Materials', 'Industrials', 'Telecommunications']
baseline_weights = np.full(len(sectors), 0)

def select_sectors(sectors, number=4):
    # Ensure number is even to divide equally between overweight and underweight
    if number % 2 != 0:
        raise ValueError("Number of sectors must be even.")
    
    half_number = number // 2
    all_sectors = set(sectors)
    
    # Select overweight sectors
    overweight_sectors = random.sample(sorted(all_sectors), half_number)
    
    # Remove selected overweight sectors from the pool
    remaining_sectors = all_sectors - set(overweight_sectors)
    
    # Select underweight sectors from the remaining pool
    underweight_sectors = random.sample(sorted(remaining_sectors), half_number)
    
    return {'overweight': overweight_sectors, 'underweight': underweight_sectors}

# Function to adjust weights
def adjust_weights(selected_sectors, baseline_weights, adjustment=0.1):
    adjusted_weights = baseline_weights.copy()
    adjusted_weights = pd.Series(adjusted_weights, index=sectors).astype(float)
    for sector in selected_sectors['overweight']:
        index = sectors.index(sector)
        adjusted_weights.iloc[index] += adjustment
    for sector in selected_sectors['underweight']:
        index = sectors.index(sector)
        adjusted_weights.iloc[index] -= adjustment
    return np.array(adjusted_weights)

# Function to calculate active risk
def calculate_active_risk(weights, covariance_matrix):
    portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
    return np.sqrt(portfolio_variance)


# Optimization function to equalize active risk
def optimize_weights(selected_sectors, baseline_weights, covariance_matrix):
    # Initial guess (equal weights for selected sectors)
    initial_weights = adjust_weights(selected_sectors, baseline_weights) + np.random.uniform(-0.01, 0.01, len(baseline_weights))
    original_active_risk = calculate_active_risk(initial_weights, covariance_matrix)

    # Calculate the total risk contribution for each sector
    def total_risk_contribution(weights):
        marginal_risk_contribution = np.dot(covariance_matrix, weights)
        total_risk_contribution = weights * marginal_risk_contribution
        return total_risk_contribution
    
    def no_negative_risk_contributions(weights):
        contributions = total_risk_contribution(weights)
        # Return the minimum value; optimization will ensure this is >= 0
        return np.min(contributions)
    
    # Constraint to maintain the original active risk
    def risk_constraint(weights):
        # Calculate current risk based on weights
        current_risk = calculate_active_risk(weights, covariance_matrix)
        # Define risk tolerance
        risk_tolerance = 0.01
        # Return the absolute difference between the current and original risk, ensuring it's within tolerance
        return -(abs(current_risk - original_active_risk) - risk_tolerance)

    # Objective function to minimize the range of risk contributions across sectors
    def objective(weights):
        risk_contributions = total_risk_contribution(weights)
        return np.var(risk_contributions)
    
    # Constraints and bounds
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x)}, # The sum of active weights must be 0
                   {'type': 'eq', 'fun' : lambda x: np.sum([el for el in x if el > 0]) - 0.4},  # The sum of overweight weights must be 0.4  
                    {'type': 'ineq', 'fun' : no_negative_risk_contributions},  # Ensure no negative risk contributions
                    {'type': 'ineq', 'fun': risk_constraint})  # Maintain original active risk

    bounds = [(0, 0.3) if sector in selected_sectors['overweight'] else (-0.3, 0) if sector in selected_sectors['underweight'] else (0, 0) for sector in sectors]


    # Optimization
    best_solution = None
    best_value = np.inf

    for _ in range(1000):
        initial_guess = initial_weights + np.random.uniform(-0.05, 0.05, len(baseline_weights))
        result = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.fun < best_value:
            best_value = result.fun
            best_solution = result.x

    return best_solution

if __name__ == '__main__':

    reader = CovarianceMatrixReader('data.db')
    risk_contribs = {}
    tracking_errors_before = {}
    tracking_errors_after = {}
    active_weights_calculated = {}

    for date in tqdm(pd.date_range('20060101', '20240101', freq='ME')):
    
        selected_sectors = select_sectors(sectors, 8)

        covariance_matrix = reader.read_covariance_matrix(date.strftime('%Y%m%d'))
        
        adjusted_weights = optimize_weights(selected_sectors, baseline_weights, covariance_matrix)
        active_weights_calculated[date] = adjusted_weights
        tracking_errors_before[date] = (calculate_active_risk(adjust_weights(selected_sectors, baseline_weights), covariance_matrix))
        tracking_errors_after[date] = calculate_active_risk(adjusted_weights, covariance_matrix)
        
        # Calculate the total risk contribution for each sector
        def total_risk_contribution(adjusted_weights):
            marginal_risk_contribution = np.dot(covariance_matrix, adjusted_weights)
            total_risk_contribution = adjusted_weights * marginal_risk_contribution
            return pd.Series(total_risk_contribution, index=sectors)
        
        risk_contribs[date] = total_risk_contribution(adjusted_weights)

def run_simulation(date):
    reader = CovarianceMatrixReader('data.db')
    selected_sectors = select_sectors(sectors, 8)
    covariance_matrix = reader.read_covariance_matrix(date.strftime('%Y%m%d'))
    adjusted_weights = optimize_weights(selected_sectors, baseline_weights, covariance_matrix)
    return adjusted_weights, covariance_matrix