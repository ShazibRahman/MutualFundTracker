from datetime import date, datetime

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import helper.helperFunctions as helper
from app import app
from dash.dependencies import Input, Output, State


def get_all_order() -> dbc.Table:
    mfs = helper.json_data
    MfsReversed = {}
    for k, v in mfs.items():
        MfsReversed[v] = k

    children = []
    children.append(html.Thead(html.Tr([html.Th("Mutual Fund Name"), html.Th(
        "Amount"), html.Th("Units"), html.Th("Nav Date")])))
    body = []
    for k, v in helper.Orders.items():  # id , dic
        for k2, v2 in v.items():  # date ,list[units,amount]
            body.append(
                html.Tr([html.Td(MfsReversed[k]), html.Td(v2[1]), html.Td(v2[0]), html.Td(k2)]))
    children.append(html.Tbody(body))

    return dbc.Table(children=children, className="table table-striped table-bordered  justify-content-center") if len(body) != 0 else dbc.Table()


layout = html.Div([
    dbc.Col([
        dcc.Dropdown(id='dropdown', optionHeight=60, options=helper.get_index_all_mutual_fund(
        ), value='', multi=False, placeholder='Select a product', className="dropdown", style={"width": "100%", "margin-bottom": "20px"}),
    ]),

    dbc.Row([

        dbc.Col([dbc.Input(id='units', type='float',
                placeholder='Enter units',  min=1, className="input")],),
        dbc.Col([dbc.Input(id='amount', type='number',
                placeholder='Enter amount', min=1, className="input")]),
        dbc.Col([dcc.DatePickerSingle(
            id='date', date=date.today(), className="date")]),
        dbc.Col([dbc.Button("Add", id='add', color="primary",
                n_clicks=0, className="button", style={
                    "width": "100%",

                })]),

    ], className="row", style={
        "padding": "0px"
    }),
    html.Div(id='output', className="output"),

    html.Div(
        id='view-order', style={
            "margin-top": "150px"
        },
        children=[get_all_order()]
    )

], className="container")


@app.callback(
    Output('output', 'children'),
    [Input('add', 'n_clicks'),
     State('units', 'value'),
     State('amount', 'value'),
     State('date', 'date'),
     State('dropdown', 'value')],
    prevent_initial_call=True

)
def add_order(n_clicks, units, amount, date, product):
    print(product, units, amount, date)
    if product is None or product == "" or units is None or float(units) <= 0 or amount is None or amount < 1 or date is None:
        return "Please fill all the fields"
    else:
        date_object = datetime.strptime(date, '%Y-%m-%d').strftime("%d-%b-%Y")
        helper.addOrder(product, float(units), amount, date_object)
        return f"Order added for {units} units of {helper.get_id_name_dic(product)} at {amount} on {date_object}"
