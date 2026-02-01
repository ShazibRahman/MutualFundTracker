import pathlib
import sys

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# autopep8 : off
sys.path.append(pathlib.Path(__file__).parent.resolve().as_posix())
sys.path.append(pathlib.Path(__file__).parent.parent.parent.resolve().as_posix())
from app import app
from apps import addOrder, dashBoard, stocks, graphs

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
                dbc.NavItem(
                    dbc.NavLink(
                        "Graphs", id="graphs", href="/apps/graphs", className=""
                    ),
                    id="graphsLink",
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
    Output("graphsLink", component_property="style"),
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

    routes = {
        "/apps/dashBoard": dashBoard.layout,
        "/apps/addOrder": addOrder.layout,
        "/apps/stocks": stocks.layout,
        "/apps/graphs": graphs.layout,
    }
    # Generate data for the routes
    data = generate_data(routes, active_Style, inactive_Style)
    # Set the styles for the navbar links based on the current pathname

    if pathname == "/":
        return data["/apps/dashBoard"]

    return data[pathname]


def generate_data(routes, active_Style, inactive_Style):
    data = {}
    all_routes = list(routes.keys())  # List of all routes

    for i, route in enumerate(all_routes):
        # Create a list of styles with all inactive styles
        styles = [inactive_Style] * len(all_routes)

        # Set the active style for the current route
        styles[i] = active_Style

        # Add the route and its corresponding layout and styles to the data dictionary
        data[route] = (routes[route], *styles)

    return data


if __name__ == "__main__":
    app.run(debug=True, port="3000")
