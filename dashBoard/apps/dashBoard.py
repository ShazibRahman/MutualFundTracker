from datetime import date
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import helper.helperFunctions as helper
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app import app


def getPieChart(value: dict, name: str) -> px.pie:
    return px.pie(pd.DataFrame(list(value.items()), columns=[
        'Funds', 'Amount']), values='Amount', names='Funds', title='Investment Distribution '+name, width=700, height=700)


def getFont(text, dict: dict) -> html.Font:
    return html.Font(text, style=dict)


def number(string: str):
    return html.Font("+₹"+string if float(string) > 0 else "-₹" + string.replace("-", ""), style={'font-weight': 'bold', 'color': 'green' if float(string) > 0 else 'red'})


def percentage(string: str):
    string = string.replace("%", "")
    return html.Font(f"({string})%" if float(string) > 0 else f"({string})%", style={'font-weight': 'bold', 'color': 'green' if float(string) > 0 else 'red'})


def prepareTable() -> dbc.Table:
    summary_table, MutualFund_table = helper.getMainTableData()
    # return [dbc.Table.from_dataframe(pd.DataFrame(summary_table, columns=['Invested', 'Current', '•|Total Returns', 'Last UpDated']), striped=True, bordered=True, hover=True), dbc.Table.from_dataframe(pd.DataFrame(MutualFund_table, columns="SCHEME NAME,DAY CHANGE,RETURNS,CURRENT,NAV".split(",")), striped=True, bordered=True, hover=True)]
    children_sum_tab = []
    for x in range(len(summary_table)):
        if x == 0:
            children_sum_tab.append(html.Thead(
                html.Tr([html.Th(x, className="table-dark") for x in summary_table[x]])))
        else:
            tr = html.Tr()
            tr.children = []
            for y in range(len(summary_table[x])):
                if y == 2:
                    _1, _2 = summary_table[x][y].split(" ")
                    td = html.Td()
                    td.children = [number(_1), " ", percentage(_2)]
                elif y == 3:
                    td = html.Td()
                    td.children = [html.Font(summary_table[x][y], style={
                                             'font-weight': 'bold', 'color': '#ac6f05'})]
                else:
                    td = html.Td(summary_table[x][y])
                tr.children.append(td)
            children_sum_tab.append(html.Tbody(tr))

    sum_tab = dbc.Table(children=children_sum_tab,
                        striped=True, bordered=True, hover=True, className="table table-hover table-striped table-bordered")
    children_mut_tab = []
    theme = "light"

    for x in range(len(MutualFund_table)):
        if x == 0:
            children_mut_tab.append(html.Thead(
                html.Tr([html.Th(x) for x in MutualFund_table[x]])))
        else:
            # children_mut_tab.append(html.Tbody(
            #     html.Tr([html.Td(x) for x in MutualFund_table[x]])))
            theme = 'dark' if theme == 'light' else 'light'

            tr = html.Tr(className=f"table-{theme}", style={
                         'color': "black"})
            tr.children = []

            for y in range(len(MutualFund_table[x])):
                if y == 1:
                    _1, _2 = MutualFund_table[x][y].split(" ")
                    # print(_1, _2)
                    td = html.Td()
                    td.children = [_1, html.Br(), html.Br(), number(_2)]
                elif y == 2:
                    _1, _2 = MutualFund_table[x][y].split(" ")
                    td = html.Td()
                    td.children = [_1, html.Br(), html.Br(), percentage(_2)]
                elif y == 3:
                    _1, _2 = MutualFund_table[x][y].split(" ")
                    td = html.Td()
                    td.children = [
                        "₹"+_1, html.Br(), html.Br(), html.Font("₹"+_2, style={'font-weight': 'bold', 'color': "black"})]
                elif y == 4:
                    _1, _2 = MutualFund_table[x][y].split(" ")
                    td = html.Td()
                    td.children = [html.Font(
                        _1, style={'font-weight': 'bold', 'color': '#ac6f05'}), html.Br(), html.Br(), _2]

                else:
                    td = html.Td(
                        MutualFund_table[x][y])

                tr.children.append(td)
            children_mut_tab.append(html.Tbody(tr, className=f"table-{theme}"))
    mut_tab = dbc.Table(children=children_mut_tab,
                        striped=True, bordered=True, hover=True, className=f"table-{theme} justify-content-center")
    return [sum_tab, html.Br(), html.Br(), mut_tab]


layout = dbc.Container(children=[
    html.H1(children='Mutual Funds Dashboard'),

    html.Div(children=[dcc.Dropdown(
        id='my-dropdown',
        options=helper.get_options(),
        value='',
        placeholder="Select a graph"
    ), ], className="dropdown"),
    html.Div(children=[dcc.Graph(id='my-graph', figure={
        'layout': {
            'title': 'Mutual Fund Graph',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'NAV'},
            'hovermode': 'closest',
            'legend': {'x': 0, 'y': 1},
            'transition': {'duration': 500},
            'clickmode': 'event+select',
             'plot_bgcolor': '#e6ecf3'
             }
    }), ], className="graph"),
    html.Div(children=[dcc.Graph(id='my-graph3', figure={
        'layout': {
            'title': 'Daily Change',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Change'},
            'hovermode': 'closest',
            'legend': {'x': 0, 'y': 1},
            'transition': {'duration': 500},
            'clickmode': 'event+select',
             'plot_bgcolor': '#e6ecf3'
             }
    }),
    ], className="container mt-5 mb-5"),

    html.Div(children=[
        dcc.Graph(id='my-graph2', figure={
            'data': helper.getDailyChange(),
            'layout': {
                'title': 'Daily Change',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Change'},
                'hovermode': 'closest',
                'legend': {'x': 0, 'y': 1},
                'transition': {'duration': 500},
                'clickmode': 'event+select',
                'plot_bgcolor': '#e6ecf3'
            }
        }),
    ], className="graph"),

    dbc.Container(children=[
        html.H3("Mutual Fund Investment Distribution"),
        dbc.Row(children=[
            dbc.Col(children=[
                dcc.Graph(id='my-graph4', figure=getPieChart(helper.getInvestmentDistribution()[0], "initial")
                          )
            ], className="col-12 col-md-6"),
            dbc.Col(children=[
                dcc.Graph(id='my-graph5', figure=getPieChart(helper.getInvestmentDistribution()[1], "current")
                          )], className="col-12 col-md-6")

        ]),

    ], id="row", className="row justify-content-center mt-5 mb-5"),
    html.Div(children=prepareTable(),
             className="container mt-5 mb-5  table-responsive"),



], className="container")


@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [dash.dependencies.Input('my-dropdown', 'value')],
    prevent_initial_call=True)
def update_output(value):
    if value is None or value == "":
        raise dash.exceptions.PreventUpdate
    plots, name = helper.return_data(value)

    return {
        'data': plots,
        'layout': {
            'title': name,
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'NAV'},
            'hovermode': 'closest',
            'legend': {'x': 0, 'y': 1},
            'transition': {'duration': 500},
            'clickmode': 'event+select',
            'plot_bgcolor': '#e6ecf3'

        }
    }


@app.callback(
    dash.dependencies.Output('my-graph3', 'figure'),
    [dash.dependencies.Input('my-dropdown', 'value')],
    prevent_initial_call=True)
def update_output_2(value):
    if value is None or value == "":
        raise dash.exceptions.PreventUpdate
    plots, name = helper.dailyChangePerMutualFund(value)

    return {
        'data': plots,
        'layout': {
            'title': name+" Daily Change",
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Change'},
            'hovermode': 'closest',
            'legend': {'x': 0, 'y': 1},
            'transition': {'duration': 500},
            'clickmode': 'event+select',
            'padding': 40,
            'plot_bgcolor': '#e6ecf3',


        }
    }
