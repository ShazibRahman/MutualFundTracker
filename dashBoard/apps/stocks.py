from datetime import date

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import helper.helperFunctions as helper
import helper.stock_helper as stock_helper
import pandas as pd
from app import app
from dash.dependencies import Input, Output, State
from plotly import graph_objs as go

layout = html.Div([html.Div(children=[
    html.H1(children='Stocks', className="text-center"),
    dbc.Row([
            dbc.Col([dbc.Input(id="input-1", placeholder="Enter a value...", className="form-control me-sm-2"),
                     ]),
            dbc.Col([dcc.DatePickerRange(id="input-2", min_date_allowed=date(2015, 8, 5), max_date_allowed=date.today(), initial_visible_month=date(2021, 8, 23),
                                         start_date=date(2021, 8, 23), end_date=date.today(),),
                     ]),
            dbc.Col([dbc.Button("Submit", id="button",
                    color="primary", className="ml-2", n_clicks=0)])
            ], id="row2", className="row justify-content-center mt-5 mb-5"),
]),
    html.Div(children=[
        dcc.Graph(id='my-graph6', figure={
            'layout': {
                'title': 'History Graph',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'NAV'},
                'hovermode': 'closest',
                'legend': {'x': 0, 'y': 1},
                'transition': {'duration': 500},
                'clickmode': 'event+select',
                'plot_bgcolor': '#e6ecf3'

            }
        })

    ], id="row3"),
    html.Div([
        html.H2("add stock order", style={
                "text-align": "center", "margin-top": "10px", "margin-bottom": "10px", "padding": "5px"}),
        dbc.Col([
                dcc.Dropdown(id='dropdown', optionHeight=60, options=helper.get_all_stocks_list(
                ), value='', multi=False, placeholder='Select a product', className="dropdown", style={"width": "100%", "margin-bottom": "20px"}),
                ]),
        dbc.Row([

            dbc.Col([dbc.Input(id='units', type='number',
                               placeholder='Enter units',  min=1, className="input")],),
            dbc.Col([dbc.Input(id='amount', type='flaot',
                               placeholder='Enter amount per unit', min=1, className="input")]),
            dbc.Col([dbc.Button("Add", id='add', color="primary",
                                          n_clicks=0, className="button", style={
                                              "width": "100%",
                                          })]),

        ], className="row", style={
            "padding": "0px",
            "margin": "10px"
        }), html.Div(id="stock_added_output")],
    style={
        "display": "flex", "justify-content": "center", "flex-direction": "column"}),
    html.Div([stock_helper.get_stock_data_in_form_of_table()

              ], className="container")
], className="container")


@app.callback(
    Output('my-graph6', 'figure'),
    Output('input-1', 'style'),
    Output('input-2', 'style'),
    [Input('button', 'n_clicks'),
     State('input-1', 'value'),
     State('input-2', 'start_date'),
     State('input-2', 'end_date')
     ],
    prevent_initial_call=True
)
def add_graph(n_clicks, input1, start_date, end_date):
    if input1 is None or input1 == "":
        return {'layout': {
            'title': 'History Graph',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'NAV'},
                'hovermode': 'closest',
                'legend': {'x': 0, 'y': 1},
                'transition': {'duration': 500},
                'clickmode': 'event+select',
                'plot_bgcolor': '#e6ecf3'}
                }, {'border': '1px solid red'}, {}
    elif start_date is None or end_date is None or start_date == end_date or start_date > end_date:
        return {'layout': {
            'title': 'History Graph',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'NAV'},
                'hovermode': 'closest',
                'legend': {'x': 0, 'y': 1},
                'transition': {'duration': 500},
                'clickmode': 'event+select',
                'plot_bgcolor': '#e6ecf3'

                }
                }, {}, {'border': '1px solid red'}
    plots: pd.DataFrame = helper.get_history(input1, start_date, end_date)
    if plots.empty:
        return {'layout': {
            'title': 'History Graph',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'NAV'},
                'hovermode': 'closest',
                'legend': {'x': 0, 'y': 1},
                'transition': {'duration': 500},
                'clickmode': 'event+select',
                'plot_bgcolor': '#e6ecf3'

                }
                }, {'border': '1px solid red'}, {}
    return {
        'data': [go.Scatter(x=plots.index, y=plots['Close'], mode='lines')],
        'layout': {
            'title': input1+" History Graph",
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'CLosed Price'},
            'hovermode': 'closest',
            'legend': {'x': 0, 'y': 1},
            'transition': {'duration': 500},
            'clickmode': 'event+select',
            'plot_bgcolor': '#e6ecf3'

        }
    }, {'border': '1px solid green'}, {'border': '1px solid green'}


@app.callback(
    Output('stock_added_output', 'children'),
    [Input('add', 'n_clicks')],
    [State('dropdown', 'value'),
        State('units', 'value'),
        State('amount', 'value')],
    prevent_initial_call=True
)
def add_stock_order(n_clicks, dropdown, units, amount):
    if n_clicks > 0:
        if dropdown is None or dropdown == "":
            return html.Div("Please select a stock", style={
                "color": "red",
                "font-weight": "bold",
                "font-size": "20px",
                "text-align": "center"
            })
        if units is None or units == "":
            return html.Div("Please enter units", style={
                "color": "red",
                "font-weight": "bold",
                "font-size": "20px",
                "text-align": "center"
            })
        if amount is None or amount == "":
            return html.Div("Please enter amount", style={
                "color": "red",
                "font-weight": "bold",
                "font-size": "20px",
                "text-align": "center"
            })
        booolean = helper.add_order_stock(dropdown, int(units), float(amount))
        if not booolean:
            return html.Div("Order not added because there is no such Stock", style={
                "color": "red",
                "font-weight": "bold",
                "font-size": "20px",
                "text-align": "center"
            })

        return html.Div(f"Order for {helper.get_all_stock_dic()[dropdown]} units {units} at amount per units {amount}", style={
            "color": "green",
            "font-weight": "bold",
            "font-size": "20px",
            "text-align": "center"
        }), "", 0, 0
