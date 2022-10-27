import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from datetime import date
import pandas as pd
from dash.dependencies import Input, Output, State
from plotly import graph_objs as go
import helper.helperFunctions as helper

from app import app


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
