# Import necessary libraries
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
from fetch_covariance_matrix import CovarianceMatrixReader
from equal_risk_budget_calculator import sectors, select_sectors, calculate_active_risk, run_simulation
import numpy as np

# Initialize Dash app
app = dash.Dash(__name__)

# Simulate selecting some sectors
selected_sectors = select_sectors(sectors, 8)

adjusted_weight, covariance_matrix = run_simulation(pd.Timestamp('20010503'))
adjusted_weight = pd.Series(adjusted_weight, index=sectors)

tracking_error = calculate_active_risk(pd.Series(adjusted_weight), covariance_matrix)

# Calculate the total risk contribution for each sector
def total_risk_contribution(weights, covariance_matrix):
    marginal_risk_contribution = np.dot(covariance_matrix, weights)
    total_risk_contribution = weights * marginal_risk_contribution
    return total_risk_contribution

# App layout
app.layout = html.Div([
    dcc.Graph(id='risk-contribution-chart'),
    dash_table.DataTable(id='covariance-matrix-table', columns=[{"name": i, "id": i} for i in covariance_matrix.columns], data=covariance_matrix.to_dict('records')),
    dash_table.DataTable(id='weights-table', columns=[{"name": "Sector", "id": "Sector"}, {"name": "Weight", "id": "Weight", "editable": True}], data=[{"Sector": sector, "Weight": weight} for sector, weight in adjusted_weight.items()]),
    html.Div(id='tracking-error', children=f'Tracking Error: {tracking_error}'),
    html.Button('Update Risk Contributions', id='update-button', n_clicks=0),
])

# Callback for updating the risk contribution chart
@app.callback(
    [Output('risk-contribution-chart', 'figure'),
    Output('weights-table', 'data'),
    Output('tracking-error', 'children')],
    [Input('update-button', 'n_clicks')],
    [State('weights-table', 'data')]
)
def update_risk_contribution_chart(n_clicks, weights_data):
    weights = pd.Series({row['Sector']: float(row['Weight']) for row in weights_data})

    risk_contribs = total_risk_contribution(weights, covariance_matrix)

    fig = go.Figure([go.Bar(x=risk_contribs.index, y=risk_contribs.values)])
    fig.update_layout(title='Risk Contribution per Sector')

    # Update the weights table data to reflect the adjusted weights
    updated_weights_data = [{"Sector": sector, "Weight": round(weight, 4)} for sector, weight in weights.items()]

    tracking_error = calculate_active_risk(weights, covariance_matrix)

    return fig, updated_weights_data, tracking_error

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)