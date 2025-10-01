from app import app
from helper.helperFunctions import helper_functions

from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

helper = helper_functions()


# Sample helper function to simulate fetching data


layout = dbc.Container(
    children=[
        html.H3("Mutual Fund Current and Invested Graph"),
        html.Div(
            children=[
                # Time Filter Dropdown
                dcc.Dropdown(
                    id="time-filter",
                    options=[
                        {"label": "All", "value": "all"},
                        {"label": "1M", "value": "1M"},
                        {"label": "3M", "value": "3M"},
                        {"label": "6M", "value": "6M"},
                        {"label": "1Y", "value": "1Y"},
                        {"label": "3Y", "value": "3Y"},
                        {"label": "5Y", "value": "5Y"},
                    ],
                    value="all",  # Default value
                    clearable=False,
                    style={"width": "200px", "margin-bottom": "20px"},
                ),
                # Mutual Fund Name Filter Dropdown
                dcc.Dropdown(
                    id="fund-name-filter",
                    options=helper.get_fund_name_options(),
                    value="ALL",  # Updated default value to "ALL"
                    clearable=False,
                    style={"width": "400px", "margin-bottom": "20px"},
                ),
                # Graph Component
                dcc.Graph(
                    id="my-cur-inv-graph",
                    style={"height": "600px"},  # Set the height of the graph
                ),
            ],
            style={"padding": "20px"},  # Add padding inside the div
        ),
    ],
    className="graph",
    style={"padding": "20px"},  # Add padding to the container
)


# Callback to update the graph based on the selected filter
@app.callback(
    Output("my-cur-inv-graph", "figure"),
    Input("time-filter", "value"),
    Input("fund-name-filter", "value"),
)
def update_graph(selected_filter, selected_fund_name):
    # Fetch the full dataset
    data = helper.get_current_invest_data(selected_filter, selected_fund_name)

    # Define the date range based on the selected filter

    # Filter the data based on the date range

    # Return the updated figure
    return {
        "data": data,
        "layout": {
            "title": "Current Investment Data",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Amount"},
            "hovermode": "closest",
            "legend": {"x": 0, "y": 1},
            "transition": {"duration": 500},
            "clickmode": "event+select",
        },
    }


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
