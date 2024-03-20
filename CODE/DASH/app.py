# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 11:26:23 2024

@author: PC
"""
import dash
from dash import Dash, html, dcc, callback, Output, Input, State, register_page
import pandas as pd
import os
import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Container import Container
import dash_auth
import requests

VALID_USERNAME_PASSWORD_PAIRS = {
    'hello': 'world'
}

app = Dash(__name__,use_pages=True,external_stylesheets=[dbc.icons.FONT_AWESOME])

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

server = app.server


'''
#for debugging purposes
from dash_labs import print_registry
print_registry()
'''

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.NavbarBrand("Title of Dash App1", className="ms-2"),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
            dbc.NavItem(dbc.NavLink("Regime", href="/regime"))
        ]
    )
)


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


SIDEBAR_STYLE = {
    "position": "auto",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}


sidebar = html.Div(
    [
        html.H2("Sidebar", className="sidebar-header"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-home me-2"), html.Span("Home")],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-calendar-alt me-2"),
                        html.Span("Calendar"),
                    ],
                    href="/calendar",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-envelope-open-text me-2"),
                        html.Span("Messages"),
                    ],
                    href="/messages",
                    active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
    className="sidebar",
)



app.layout = html.Div([
    navbar,
    html.Button('Send Request', id='request-button', n_clicks=0),
    dbc.Row([
     dbc.Col([sidebar],width="auto"),
     dbc.Col([dash.page_container])
     ]
    ),
    html.Div(id='container-button-basic',
             children='Enter a value and press submit')

])

@app.callback(
    Output('container-button-basic','children'),
    [Input('request-button', 'n_clicks')],
    prevent_initial_call=True
)
def logout(n_clicks):
    if n_clicks > 0:
        response = requests.get('http://username:password@localhost:8050')
        return f'Error: {response.status_code}'

if __name__ == '__main__':
    #app.run_server(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
    app.run(debug=True)