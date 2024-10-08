import pathlib
import sys

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# autopep8 : off
sys.path.append(pathlib.Path(__file__).parent.resolve().as_posix())
sys.path.append(pathlib.Path(__file__).parent.parent.parent.resolve().as_posix())
from app import app, server
from apps import addOrder, dashBoard, stocks

# connect to your app pages

app.layout = html.Div(
    [
        dbc.Nav(
            children=[
                dbc.NavItem(
                    dbc.NavLink(
                        "DashBoard",
                        id="dashboardLink",
                        href="/apps/dashBoard",
                        className="",
                    ),
                    id="dashLink",
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        "Add Order", id="addOrder", href="/apps/addOrder", className=""
                    ),
                    id="orderLink",
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        "Stocks", id="stocks", href="/apps/stocks", className=""
                    ),
                    id="stockLink",
                ),
            ],
            style={
                "width": "100%",
                "height": "50px",
                "background-color": "#f8f9fa",
                "margin-bottom": "20px",
            },
        ),
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)


@app.callback(
    Output("page-content", "children"),
    Output("dashLink", component_property="style"),
    Output("orderLink", component_property="style"),
    Output("stockLink", component_property="style"),
    [Input("url", "pathname")],
)
def display_page(pathname: str):
    # active style for navbar links
    active_Style = {
        "background-color": "#e9ecef",
        "border-radius": "5px",
    }

    inactive_Style = {
        "background-color": "#f8f9fa",
        "border-radius": "5px",
        "color": "grey",
    }  # inactive style for navbar links

    data = {
        "/apps/dashBoard": (
            dashBoard.layout,
            active_Style,
            inactive_Style,
            inactive_Style,
        ),
        "/apps/addOrder": (
            addOrder.layout,
            inactive_Style,
            active_Style,
            inactive_Style,
        ),
        "/apps/stocks": (stocks.layout, inactive_Style, inactive_Style, active_Style),
        "/": (dashBoard.layout, active_Style, inactive_Style, inactive_Style),
    }

    return data[pathname]


if __name__ == "__main__":
    app.run_server(debug=True, port="3000")
