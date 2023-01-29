from typing import Tuple
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app

# connect to your app pages
from apps import dashBoard, addOrder, stocks


app.layout = html.Div([

    dbc.Nav(children=[
        dbc.NavItem(dbc.NavLink(
            "DashBoard", id="dasboardLink", href="/apps/dashBoard", className="")),
        dbc.NavItem(dbc.NavLink(
            "Add Order", id="addOrder", href="/apps/addOrder", className="")),
        dbc.NavItem(dbc.NavLink(
            "Stocks", id="stocks", href="/apps/stocks", className="")),
    ], style={'width': '100%', 'height': '50px', 'background-color': '#f8f9fa', 'margin-bottom': '20px'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Output("dasboardLink", component_property="style"),
              Output("addOrder", component_property="style"),
              Output("stocks", component_property="style"),
              [Input('url', 'pathname')])
def display_page(pathname: str):
    # active style for navbar links
    active_Style: dict[str:str] = {
        'background-color': '#e9ecef', 'border-radius': '5px'}
    inactive_Style: dict[str:str] = {'background-color': '#f8f9fa',
                                     'border-radius': '5px', 'color': "grey"}  # inactive style for navbar links
    data: dict[str:Tuple] = {"/apps/dashBoard": (dashBoard.layout, active_Style, inactive_Style, inactive_Style),
                             "/apps/addOrder": (addOrder.layout, inactive_Style, active_Style, inactive_Style),
                             "/apps/stocks": (stocks.layout, inactive_Style, inactive_Style, active_Style),
                             "/": (dashBoard.layout, active_Style, inactive_Style, inactive_Style)}

    return data[pathname]


if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=3000)
    # server.run(debug=True, port=3000)
