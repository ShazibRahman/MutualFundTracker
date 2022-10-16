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
            "DashBoard", id="dasboardLink", href="/apps/dashBoard", className="")),
        dbc.NavItem(dbc.NavLink(
            "Add Order", id="addOrder", href="/apps/addOrder", className="")),
    ], style={'width': '100%', 'height': '50px', 'background-color': '#f8f9fa', 'margin-bottom': '20px'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Output("dasboardLink", component_property="style"),
              Output("addOrder", component_property="style"),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/dashBoard':
        return dashBoard.layout, {}, {'color': "grey"}
    elif pathname == '/apps/addOrder':
        return addOrder.layout, {'color': "grey"}, {}
    else:
        return dashBoard.layout, {}, {'color': "grey"}


if __name__ == '__main__':
    app.run_server(debug=True, port=3000)
    # server.run(debug=True, port=3000)
