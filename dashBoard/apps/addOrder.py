from datetime import date, datetime
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import helper.helperFunctions as helper

from dash.dependencies import Input, Output, State

from app import app

# layout = dbc.Container(["container for add order"], className="container")
layout = html.Div([
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='dropdown', optionHeight=60, options=helper.get_options(
            ), value='Select a product', multi=False, placeholder='Select a product', className="dropdown", style={"width": "100%"}),
        ]),
        dbc.Col([dbc.Input(id='units', type='float',
                placeholder='Enter units',  min=1, className="input")],),
        dbc.Col([dbc.Input(id='amount', type='number',
                placeholder='Enter amount', min=1, className="input")]),
        dbc.Col([dcc.DatePickerSingle(
            id='date', date=date.today(), className="date")]),
        dbc.Col([dbc.Button("Add", id='add', color="primary",
                n_clicks=0, className="button")]),

    ], className="row"),
    html.Div(id='output', className="output"),

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
        return f"Order added for {units} units of {helper.get_id_name_dic()[product]} at {amount} on {date_object}"
