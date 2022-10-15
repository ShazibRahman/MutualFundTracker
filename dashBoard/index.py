import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app
from app import server


# connect to your app pages
from apps import dashBoard, addOrder


app.layout = html.Div([

    dbc.Nav(children=[
        dbc.NavItem(dbc.NavLink(
            "DashBoard", href="/apps/dashBoard", className="nav-link")),
        dbc.NavItem(dbc.NavLink(
            "Add Order", href="/apps/addOrder", className="nav-link")),
    ], style={'width': '100%', 'height': '50px', 'background-color': '#f8f9fa', 'margin-bottom': '20px'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/dashBoard':
        return dashBoard.layout
    elif pathname == '/apps/addOrder':
        return addOrder.layout
    else:
        return '/apps/dashBoard'


if __name__ == '__main__':
    app.run_server(debug=True, port=3000)
    # server.run(debug=True, port=3000)
