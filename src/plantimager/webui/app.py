#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time

import dash_bootstrap_components as dbc
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dash
from dash import dcc
from dash import html

from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantimager.webui.config import plantdb_cfg_modal
from plantimager.webui.login import USERS_DB
from plantimager.webui.login import error_modal
from plantimager.webui.login import login_modal
from plantimager.webui.login import success_modal

ROMI_LOGO = "https://romi-project.eu/assets/logo.svg"


def parsing():
    parser = argparse.ArgumentParser(description="PlantImager WebUI.")

    app_args = parser.add_argument_group("Dash app options")
    app_args.add_argument('--host', type=str, default=REST_API_URL,
                          help="Host address of the PlantDB REST API.")
    app_args.add_argument('--port', type=int, default=REST_API_PORT,
                          help="Port of the PlantDB REST API.")
    return parser


def main(url, port):
    # Initialize Dash application with Bootstrap styling and multipage support
    app = Dash("PlantImager_WebUI",
               external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

    cfg_button = dbc.Button("Configuration", id='open-cfg-button', n_clicks=0,
                              outline=True, color="primary", className="me-1")

    # Create login button and user avatar components for the navigation bar
    login_button = dbc.Button("Login", id='open-login-button', n_clicks=0,
                              outline=True, color="primary", className="me-1")

    # Avatar card displays user initials when logged in, "?" when logged out
    login_avatar = dbc.Card([
        dbc.CardImg(src='https://icons.getbootstrap.com/assets/icons/circle-fill.svg',
                    top=True, style={'width': '35px', "opacity": 0.3}),
        dbc.CardImgOverlay(id="card-username", children="?")
    ], id='login-avatar')

    # Define main navigation items including scan, database, and documentation links
    nav_item = dbc.Nav([
        dbc.NavItem(dbc.NavLink("Tutorial", style={'color': "#f3f3f3"},
                                href="https://docs.romi-project.eu/plant_imager/tutorials/reconstruct_scan/")),
        dbc.NavItem(cfg_button),
        dbc.NavItem(login_button),
        dbc.NavItem(login_avatar),
    ])

    # Construct responsive navigation bar with ROMI logo and branding
    navbar = dbc.Navbar(
        dbc.Container([
            # Logo and brand section
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src=ROMI_LOGO, height="35px")),
                    dbc.Col(dbc.NavbarBrand("PlantImager", href="/",
                                            className="ms-2", style={'color': "#f3f3f3"})),
                ], align="center", className="g-0"),
                href="https://romi-project.eu/",
                style={"textDecoration": "none"},
            ),
            # Collapsible navigation menu for mobile view
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav([nav_item, ], className="ms-auto", navbar=True),
                id="navbar-collapse", navbar=True,
            ),
        ]),
        color="#00a960", className="mb-5",
    )

    # Callback to toggle configuration modal visibility
    @callback(Output("plantdb-cfg-modal", "is_open", allow_duplicate=True),
              Input('open-cfg-button', 'n_clicks'),
              State('plantdb-cfg-modal', 'is_open'),
              prevent_initial_call=True)
    def toggle_config_modal(n, is_open):
        return not is_open

    # Callback to toggle login modal visibility
    @callback(Output("login-modal", "is_open", allow_duplicate=True),
              Input('open-login-button', 'n_clicks'),
              State('login-modal', 'is_open'),
              prevent_initial_call=True)
    def toggle_login_modal(n, is_open):
        return not is_open

    # Handle login form submission and authentication
    @callback(Output('logged-username', 'data'),
              Output("success-modal", "is_open", allow_duplicate=True),
              Output("error-modal", "is_open", allow_duplicate=True),
              Input('login-button', 'n_clicks'),
              State('username', 'value'),
              State('password', 'value'),
              prevent_initial_call=True)
    def login(n_clicks, username, password):
        if n_clicks > 0:
            # Verify credentials against user database
            if username in list(USERS_DB.keys()) and password == USERS_DB[username]['password']:
                return username, True, False  # Login successful
            else:
                return None, False, True  # Login failed
        return None, False, False

    # Manage modal dialogs timing and visibility
    @callback(Output("success-modal", "is_open", allow_duplicate=True),
              Output("error-modal", "is_open", allow_duplicate=True),
              Output("login-modal", "is_open", allow_duplicate=True),
              Input("success-modal", "is_open"),
              Input("error-modal", "is_open"),
              prevent_initial_call=True)
    def timeout_modal(success, error):
        # Auto-close modals after 2 seconds
        if success:
            time.sleep(2)
            return False, False, False
        elif error:
            time.sleep(2)
            return False, False, True
        return False, False, False

    # Reset login button clicks on logout
    @callback(Output('login-button', 'n_clicks'),
              Input('logout-button', 'n_clicks'),
              prevent_initial_call=True)
    def logout(n_clicks):
        return 0

    # Update navigation UI based on login status
    @callback(Output("card-username", 'children'),
              Output("open-login-button", 'children'),
              Input('logged-username', 'data'),
              prevent_initial_call=True)
    def nav_login(username):
        if username is None:
            return "??", "Login"
        # Display user initials from full name when logged in
        initials = "".join([i[0].upper() for i in USERS_DB[username]['fullname'].split(' ')])
        return initials, "Logout"

    # Main application layout definition
    app.layout = html.Div([
        # Navigation and modal components
        html.Div(children=[navbar, plantdb_cfg_modal, login_modal, success_modal, error_modal]),
        # Global state storage
        dcc.Store(id='dataset-list', data=None),
        dcc.Store(id='rest-api-host', data=url),
        dcc.Store(id='rest-api-port', data=port),
        dcc.Store(id='dataset-id', data=None),
        dcc.Store(id='logged-username', data=None),
        # Main content container
        html.Div(children=[dash.page_container], style={"margin": 20}),
    ])

    return app


if __name__ == "__main__":
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()
    # - Start the Dash app:
    app = main(args.host, args.port)
    app.run(debug=True, port=8000)
