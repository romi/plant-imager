#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

import dash_bootstrap_components as dbc
from dash import Dash
from dash import dcc
from dash import html
from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantimager.webui.config import plantdb_cfg_modal
from plantimager.webui.login import login_modal
from plantimager.webui.nav import navbar_layout
from plantimager.webui.scan import scan_layout


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
    app = Dash(name="PlantImager_WebUI", title="Plant Imager",
               external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

    # Main application layout definition
    app.layout = html.Div([
        # Global state storage
        dcc.Store(id='rest-api-host', data=url),
        dcc.Store(id='rest-api-port', data=port),
        dcc.Store(id='connected', data=None),
        dcc.Store(id='logged-username', data=None),
        dcc.Store(id='dataset-list', data=[]),
        dcc.Store(id='dataset-id', data=None),
        # Navigation and modal components
        html.Div(children=[
            navbar_layout,
            plantdb_cfg_modal,
            login_modal
        ]),
        # Main content container
        html.Div(children=[scan_layout], style={"margin": 20}),
    ])

    return app


if __name__ == "__main__":
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()
    # - Start the Dash app:
    app = main(args.host, args.port)
    app.run(debug=True, port=8000)
