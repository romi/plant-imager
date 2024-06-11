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
from plantimager.webui.login import USERS_DB
from plantimager.webui.login import error_modal
from plantimager.webui.login import login_modal
from plantimager.webui.login import success_modal

ROMI_LOGO = "https://romi-project.eu/assets/logo.svg"


def parsing():
    parser = argparse.ArgumentParser(description="WebUI to scan dataset.")

    app_args = parser.add_argument_group("Dash app options")
    app_args.add_argument('--host', type=str, default=REST_API_URL,
                          help="host IP used to serve the application")
    app_args.add_argument('--port', type=int, default=REST_API_PORT,
                          help="port used to serve the application")

    hw_args = parser.add_argument_group("Hardware options")
    hw_args.add_argument('--cnc_dev', type=str, default="/dev/ttyACM0")
    hw_args.add_argument('--gimbal_dev', type=str, default="/dev/ttyACM1")

    return parser


def main(url, port):
    app = Dash("PlantImager_WebUI", use_pages=True,
               external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

    # -----------------------------------------------------------------------------
    # Navigation bar
    # -----------------------------------------------------------------------------
    login_button = dbc.Button("Login", id='open-login-button', n_clicks=0,
                              outline=True, color="primary", className="me-1",
                              #style={'color': "#ff8400", 'font-weight': 'bold'},
                              )
    login_avatar = dbc.Card(
        [
            dbc.CardImg(src='https://icons.getbootstrap.com/assets/icons/circle-fill.svg',
                        top=True, style={'width': '35px', "opacity": 0.3}),
            dbc.CardImgOverlay(id="card-username", children="?")
        ], id='login-avatar'
    )

    # Navigation links
    nav_item = dbc.Nav([
        dbc.NavItem(
            dbc.NavLink("PlantDB", style={'color': "#f3f3f3"},
                        href="/plantdb_api")),
        dbc.NavItem(
            dbc.NavLink("Tutorial", style={'color': "#f3f3f3"},
                        href="https://docs.romi-project.eu/plant_imager/tutorials/reconstruct_scan/")),
        dbc.NavItem(login_button),
        dbc.NavItem(login_avatar),
    ])

    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=ROMI_LOGO, height="35px")),
                            dbc.Col(dbc.NavbarBrand("PlantImager", href="/",
                                                    className="ms-2", style={'color': "#f3f3f3"})),
                        ],
                        align="center", className="g-0",
                    ),
                    href="https://romi-project.eu/", style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    dbc.Nav([nav_item, ], className="ms-auto", navbar=True),
                    id="navbar-collapse", navbar=True,
                ),
            ],
        ),
        color= "#00a960", className="mb-5",
    )

    @callback(Output("login-modal", "is_open", allow_duplicate=True),
              Input('open-login-button', 'n_clicks'),
              State('login-modal', 'is_open'),
              prevent_initial_call=True)
    def toggle_login_modal(n, is_open):
        return not is_open

    @callback(Output('logged-username', 'data'),
              Output("success-modal", "is_open", allow_duplicate=True),
              Output("error-modal", "is_open", allow_duplicate=True),
              Input('login-button', 'n_clicks'),
              State('username', 'value'),
              State('password', 'value'),
              prevent_initial_call=True)
    def login(n_clicks, username, password):
        if n_clicks > 0:
            if username in list(USERS_DB.keys()) and password == USERS_DB[username]['password']:
                return username, True, False
            else:
                return None, False, True
        else:
            return None, False, False

    @callback(Output("success-modal", "is_open", allow_duplicate=True),
              Output("error-modal", "is_open", allow_duplicate=True),
              Output("login-modal", "is_open", allow_duplicate=True),
              Input("success-modal", "is_open"),
              Input("error-modal", "is_open"),
              prevent_initial_call=True)
    def timeout_modal(success, error):
        if success:
            time.sleep(2)
            return False, False, False
        elif error:
            time.sleep(2)
            return False, False, True
        else:
            return False, False, False

    @callback(Output('login-button', 'n_clicks'),
              Input('logout-button', 'n_clicks'),
              prevent_initial_call=True)
    def logout(n_clicks):
        return 0

    @callback(Output("card-username", 'children'),
              Output("open-login-button", 'children'),
              Input('logged-username', 'data'),
              prevent_initial_call=True)
    def nav_login(username):
        if username is None:
            return "??", "Login"
        else:
            initials = "".join([i[0].upper() for i in USERS_DB[username]['fullname'].split(' ')])
            return initials, "Logout"

    app.layout = html.Div(
        [
            html.Div(children=[navbar, login_modal, success_modal, error_modal]),
            dcc.Store(id='dataset-dict', data=None),
            dcc.Store(id='rest-api-host', data=url),
            dcc.Store(id='rest-api-port', data=port),
            dcc.Store(id='dataset-id', data=None),
            dcc.Store(id='logged-username', data=None),
            html.Div(
                children=[dash.page_container],
                style={"margin": 20},
            ),
        ]
    )

    # we use a callback to toggle the collapse on small screens
    @callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    return app


if __name__ == "__main__":
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()
    # - Start the Dash app:
    app = main(args.host, args.port)
    app.run(debug=True, port=8000)
