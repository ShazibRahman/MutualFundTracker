import dash
import dash_bootstrap_components as dbc
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width ,initial-scale=1"}], external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'])

# Path: dashBoard/app.py
server = app.server
