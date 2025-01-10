# 闲梦Soundream
# Time: 2024/11/15

import pandas as pd
import numpy as np
from dash import Dash, dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

# Read the data from local CSV files for S&P 500, US Government Bonds, and Gold ETF
bond = pd.read_csv("us govt bond.csv", parse_dates=["date"], dayfirst=True)
gold = pd.read_csv("gold.csv", parse_dates=["date"], dayfirst=True)
stock = pd.read_csv("sp500.csv", parse_dates=["date"], dayfirst=True)

# Set 'date' as the index for each DataFrame
bond.set_index("date", inplace=True)
gold.set_index("date", inplace=True)
stock.set_index("date", inplace=True)


# Task 1 & 2
def createPortfolio(stock_weight, bond_weight, gold_weight, start_date, end_date):
    # Filter the data based on the selected date range
    bond_data = bond[(bond.index >= start_date) & (bond.index <= end_date)]["close"].copy()
    gold_data = gold[(gold.index >= start_date) & (gold.index <= end_date)]["close"].copy()
    stock_data = stock[(stock.index >= start_date) & (stock.index <= end_date)]["close"].copy()

    # Ensure the data is not empty
    if bond_data.empty or gold_data.empty or stock_data.empty:
        return []

    # Calculate the cumulative returns for each asset
    bond_cumulative = bond_data / bond_data.iloc[0]
    gold_cumulative = gold_data / gold_data.iloc[0]
    stock_cumulative = stock_data / stock_data.iloc[0]

    # Normalize the weights
    total_weight = stock_weight + bond_weight + gold_weight
    stock_weight /= total_weight
    bond_weight /= total_weight
    gold_weight /= total_weight

    # If the weight is 1 for one asset, return that asset's cumulative return directly
    if stock_weight == 1:
        return stock_cumulative
    elif bond_weight == 1:
        return bond_cumulative
    elif gold_weight == 1:
        return gold_cumulative

    # Calculate the cumulative return of the custom portfolio
    portfolio_data = stock_weight * stock_cumulative + bond_weight * bond_cumulative + gold_weight * gold_cumulative
    portfolio_cumulative = portfolio_data / portfolio_data.iloc[0]
    return portfolio_cumulative


# Bonus Task: Calculate investment related statistics of the portfolio
def calculateStatistics(portfolio_values, risk_free_rate=0.02):
    if portfolio_values.empty:
        return {
            "Annual Return": np.nan,
            "Volatility": np.nan,
            "Sharpe Ratio": np.nan,
            "Sortino Ratio": np.nan,
            "Max Drawdown": np.nan
        }

    returns = portfolio_values.pct_change().dropna()

    annual_return = portfolio_values.iloc[-1] ** (252 / len(portfolio_values)) - 1 # portfolio_values.iloc[0] is 1
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = (annual_return - risk_free_rate) / volatility
    sortino_ratio = (annual_return - risk_free_rate) / (returns[returns < 0].std() * np.sqrt(252))
    max_drawdown = ((portfolio_values / portfolio_values.cummax()) - 1).min()
    return {
        "Annual Return": annual_return,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe_ratio,
        "Sortino Ratio": sortino_ratio,
        "Max Drawdown": max_drawdown
    }


# Bonus Task: Optimize the allocation of the portfolio
def optimize_allocation(start_date, end_date):
    best_sharpe = -np.inf
    best_allocation = (0, 0, 0)
    for stock_weight in range(0, 101, 10):
        for bond_weight in range(0, 101, 10):
            for gold_weight in range(0, 101, 10):
                if stock_weight + bond_weight + gold_weight == 0:
                    continue
                portfolio = createPortfolio(stock_weight, bond_weight, gold_weight,start_date, end_date)
                sharpe_ratio = calculateStatistics(portfolio)["Sharpe Ratio"]
                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_allocation = (stock_weight, bond_weight, gold_weight)
    if stock_weight == 0 and bond_weight == 0:
        best_allocation = (0, 0, 100)
    elif stock_weight == 0 and gold_weight == 0:
        best_allocation = (0, 100, 0)
    elif bond_weight == 0 and gold_weight == 0:
        best_allocation = (100, 0, 0)
    else:
        sum_up = sum(best_allocation)
        best_allocation = tuple([i / sum_up * 100 for i in best_allocation])
    return [best_allocation, best_sharpe]


# Initialize the Dash application
app = Dash(__name__)

# Application layout
app.layout = html.Div([
    html.H1("Investment Portfolio Dashboard"),

    html.H3("Asset Allocation"),
    html.Label("Weight for stock: "),
    dcc.Input(id="sp500_weight", type="number", value=60, min=0, max=100, step=1),
    html.Br(),  # Line break

    html.Label("Weight for bond: "),
    dcc.Input(id="bonds_weight", type="number", value=40, min=0, max=100, step=1),
    html.Br(),  # Line break

    html.Label("Weight for gold: "),
    dcc.Input(id="gold_weight", type="number", value=0, min=0, max=100, step=1),
    html.Br(),  # Line break

    html.Label("* Weights will be automatically normalized to sum up to 100%.", style={'fontSize': '12px'}),
    html.Br(),  # Line break
    html.Label("* Stock: S&P500, Bond: US Govt Bonds, Gold: Gold ETF. ", style={'fontSize': '12px'}),
    html.Br(),  # Line break
    html.Br(),  # Line break

    html.Label("Select the date range:  "),
    dcc.DatePickerRange(
        id='date_picker',
        start_date='2020-01-01',
        end_date='2020-10-21',
        min_date_allowed='2018-01-02',
        max_date_allowed='2021-12-31',
        display_format='YYYY-MM-DD',
        minimum_nights=2
    ),
    html.Br(),  # Line break

    html.Div(id='portfolio_output', children=[]),
])


# Use decorators to connect inputs and outputs
@app.callback(
    Output('portfolio_output', 'children'),
    [
        Input('sp500_weight', 'value'),
        Input('bonds_weight', 'value'),
        Input('gold_weight', 'value'),
        Input('date_picker', 'start_date'),
        Input('date_picker', 'end_date'),
    ]
)
def update_portfolio(s_weight, b_weight, g_weight, start_date, end_date):
    # Create the charts
    stock_cumulative = createPortfolio(1, 0, 0, start_date, end_date)
    trace1 = go.Scatter(x=stock_cumulative.index, y=stock_cumulative, mode='lines', name='S&P 500')
    bond_cumulative = createPortfolio(0, 1, 0, start_date, end_date)
    trace2 = go.Scatter(x=bond_cumulative.index, y=bond_cumulative, mode='lines', name='US Government Bonds')
    gold_cumulative = createPortfolio(0, 0, 1, start_date, end_date)
    trace3 = go.Scatter(x=gold_cumulative.index, y=gold_cumulative, mode='lines', name='Gold')

    portfolio_cumulative = createPortfolio(s_weight, b_weight, g_weight, start_date, end_date)
    trace4 = go.Scatter(x=portfolio_cumulative.index, y=portfolio_cumulative, mode='lines', name='Custom Portfolio')
    equal_weight_cumulative = createPortfolio(1, 1, 1, start_date, end_date)
    trace5 = go.Scatter(x=equal_weight_cumulative.index, y=equal_weight_cumulative, mode='lines',
                        name='Equal Weight Portfolio')

    # Create two figures
    fig1 = go.Figure(data=[trace1, trace2, trace3])
    fig2 = go.Figure(data=[trace4, trace5])

    # Calculate "premium return" as the difference between custom and equal-weighted portfolios
    premium_return = portfolio_cumulative - equal_weight_cumulative

    # Plot chart with 2 portfolio lines and premium return as shaded area
    trace_custom = go.Scatter(x=portfolio_cumulative.index, y=portfolio_cumulative, mode='lines',
                              name='Custom Portfolio')
    trace_equal = go.Scatter(x=equal_weight_cumulative.index, y=equal_weight_cumulative, mode='lines',
                             name='Equal Weight Portfolio')
    trace_premium = go.Scatter(x=premium_return.index, y=premium_return, fill='tozeroy', name='Premium Return',
                               yaxis='y2')
    layout = go.Layout(
        yaxis=dict(title="Cumulative Returns"),
        yaxis2=dict(title="Premium Return", overlaying='y', side='right', tickformat="0%", ))

    fig3 = go.Figure(data=[trace_custom, trace_equal, trace_premium], layout=layout)

    # Calculate statistics
    stats_custom = calculateStatistics(portfolio_cumulative)
    stats_table = html.Table([
        html.Tr([html.Th(key),
                 html.Td(f"{value:.2%}" if key != "Sharpe Ratio" and key != "Sortino Ratio" else f"{value:.2f}")])
        for key, value in stats_custom.items()
    ], style={'border': '1px solid black', 'margin-top': '20px'})

    # Optimize allocation for maximum Sharpe ratio
    optimal_allocation = optimize_allocation(start_date, end_date)
    if optimal_allocation[1] == -np.inf:
        optimal_text = "No data available for the selected date range"
    elif optimal_allocation[1] == 0:
        optimal_text = "No optimal allocation found"
    else:
        optimal_text = f"Suggested Allocation is (Stock: {optimal_allocation[0][0]:.0f}%, Bond: {optimal_allocation[0][1]:.0f}%, Gold: {optimal_allocation[0][2]:.0f}%) with highest Sharpe ratio {optimal_allocation[1]:.0f}"

    return [
        html.Div([html.H3("Cumulative Returns of S&P 500, US Government Bonds, and Gold ETF"),
                  dcc.Graph(figure=fig1)]),

        html.Div([html.H3("Cumulative Returns of Custom Portfolio and Equal Weight Portfolio"),
                  dcc.Graph(figure=fig2)]),

        html.Div([html.H3("Custom Portfolio Statistics"),
                  stats_table,
                  html.P(optimal_text),
                  html.Br(),  # Line break
                  html.H3("Premium Return"),
                  dcc.Graph(figure=fig3),

                  ])
    ]


# Run app
if __name__ == '__main__':
    app.run_server(debug=True)


