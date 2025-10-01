from datetime import date, datetime

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from app import app
from dash.dependencies import Input, Output, State
from dash.html import Span
from helper.helperFunctions import helper_functions

from models import InvestmentHistory

helper = helper_functions()


def get_all_order() -> Span:
    children = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Mutual Fund Name"),
                    html.Th("Amount"),
                    html.Th("Units"),
                    html.Th("Nav Date"),
                ]
            )
        )
    ]
    body = []
    # get all orders
    orders = helper.get_all_open_orders()
    print("printing all order", orders)
    for order in orders:
        # id , dic
        body.append(
            html.Tr(
                [
                    html.Td(order.mfname),
                    html.Td(order.amount),
                    html.Td(order.unit),
                    html.Td(order.nav_date),
                ]
            )
        )
    children.append(html.Tbody(body))

    return html.Span(
        [
            html.H1("All Orders"),
            dbc.Table(
                children=children,
                className="table table-striped table-bordered  justify-content-center",
                responsive=True,
            ),
        ]
    )


layout = html.Div(
    [
        dbc.Col(
            [
                dcc.Dropdown(
                    id="dropdown",
                    optionHeight=60,
                    options=helper.get_index_all_mutual_fund(),
                    value="",
                    multi=False,
                    placeholder="Select a product",
                    className="dropdown",
                    style={"width": "100%", "margin-bottom": "20px"},
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Input(
                            id="units",
                            type="float",
                            placeholder="Enter units",
                            min=1,
                            className="input",
                        )
                    ],
                ),
                dbc.Col(
                    [
                        dbc.Input(
                            id="amount",
                            type="number",
                            placeholder="Enter amount",
                            min=1,
                            className="input",
                        )
                    ]
                ),
                dbc.Col(
                    [
                        dcc.DatePickerSingle(
                            id="date", date=date.today(), className="date"
                        )
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Add",
                            id="add",
                            color="primary",
                            n_clicks=0,
                            className="button",
                            style={
                                "width": "100%",
                            },
                        )
                    ]
                ),
            ],
            className="row",
            style={"padding": "0px"},
        ),
        html.Div(id="output", className="output"),
        html.Div(id="output-2", className="output", style={"margin-top": "20px"}),
        html.Div(
            id="view-order", style={"margin-top": "300px"}, children=[get_all_order()]
        ),
    ],
    className="container",
)


@app.callback(
    Output("output", "children"),
    [
        Input("add", "n_clicks"),
        State("units", "value"),
        State("amount", "value"),
        State("date", "date"),
        State("dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def add_order(n_clicks, units, amount, date_input, product):
    global helper
    if helper is None:
        helper = helper_functions()
    print(product, units, amount, date_input)
    if (
        product is None
        or product == ""
        or units is None
        or float(units) <= 0
        or amount is None
        or amount < 1
        or date_input is None
    ):
        return "Please fill all the fields"
    date_object = datetime.strptime(date_input, "%Y-%m-%d").date()
    # _, order = helper.add_order(product, float(units), amount, date_object)

    order_history = helper.add_order_db(product, float(units), amount, date_object)
    return f"Order added for {order_history.mfname} on {order_history.nav_date} with amount {order_history.amount} and units {order_history.unit} and nav {order_history.nav}"


@app.callback(
    Output("output-2", "children"),
    [
        Input("dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def update_output(value):
    if value is None or value == "":
        return "Please select a product"

    # day_change = asdict(helper.daychange_json)
    # funds = day_change["funds"]
    # # check if the fund is in the funds

    # if value not in funds:
    #     return "No data available for this fund"
    # fund = funds[value]
    # return f"Invested {fund['invested']} Current {fund['current']} Day Change {fund['dayChange']}"

    investment_history: InvestmentHistory = helper.get_mfid_by_id_order_by_date_desc(
        value
    )
    if investment_history is None:
        return "No data available for this fund"
    return f"Fund Name: {investment_history.mfname}, Invested Amount: {investment_history.invested_amount}, Current Amount: {investment_history.current_amount}"
