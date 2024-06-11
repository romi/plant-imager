#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from plantimager.webui.utils import get_dataset_dict
from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantdb.rest_api_client import test_db_availability

global dataset_dict

dash.register_page(__name__, path="/plantdb_api")

# -----------------------------------------------------------------------------
# Forms and callbacks to connect to the PlantDB REST API.
# -----------------------------------------------------------------------------
layout = dbc.Row(
    children=[
        dbc.Col(
            dbc.Button("< Back", href="/"),
        ),
        html.Header("Configure the connexion to a PlantDB REST API."),
        # - Input form to specify REST API URL:
        dbc.Col(
            children=[
                dbc.Label("REST API URL:"),
                dbc.Input(id="ip-address", type="text", value=REST_API_URL),
                dbc.FormText(f"Use '{REST_API_URL}' for a local database."),
            ],
            width=6,
        ),
        # - Input form to specify REST API port:
        dbc.Col(
            children=[
                dbc.Label("REST API port:"),
                dbc.Input(id="ip-port", type="text", value=REST_API_PORT),
                dbc.FormText(f"Should be '{REST_API_PORT}' by default."),
            ],
            width=2,
        ),
        # - Test connexion to REST API button
        dbc.Col(
            children=[
                dbc.Button("Test connexion", id="connect-button", color="primary"),
                dbc.FormText(
                    dbc.Alert([
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Unknown server availability."
                    ], color="info"),
                    id="connexion-status"),
            ],
            width=2, align="center"
        ),
        # - Load scans from REST API button
        dbc.Col(
            children=[
                dbc.Button("Load datasets", id="load-button", color="primary", disabled=True),
                dbc.FormText(
                    dbc.Alert([
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Undefined list of datasets."
                    ], color="info"),
                    id="load-status"),
            ],
            width=2, align="center"
        )
    ],
    justify="center"
)


@callback(Output('connexion-status', 'children'),
          Output('load-button', 'disabled'),
          Output('rest-api-host', 'data'),
          Output('rest-api-port', 'data'),
          Input('connect-button', 'n_clicks'),
          State('ip-address', 'value'),
          State('ip-port', 'value'))
def test_connect(n_clicks, host, port):
    if test_db_availability(host, int(port)):
        res = dbc.Alert(
            [
                html.I(className="bi bi-check-circle-fill me-2"),
                "Server available.",
            ],
            color="success",
        )
    else:
        res = dbc.Alert(
            [
                html.I(className="bi bi-x-octagon-fill me-2"),
                f"Server {host}:{port} unavailable!",
            ],
            color="danger",
        )
    return res, not res, host, port


@callback(Output('load-status', 'children'),
          Output('dataset-dict', 'data'),
          Input('load-button', 'n_clicks'),
          State('ip-address', 'value'),
          State('ip-port', 'value'))
def update_db(n_clicks, host, port):
    dataset_dict = get_dataset_dict(host, port)
    if len(dataset_dict) > 0:
        res = dbc.Alert(
            [
                html.I(className="bi bi-check-circle-fill me-2"),
                f"Loaded {len(dataset_dict)} dataset.",
            ],
            color="success",
        )
    else:
        res = dbc.Alert(
            [
                html.I(className="bi bi-x-octagon-fill me-2"),
                f"Could not load any dataset!",
            ],
            color="danger",
        )
    return res, dataset_dict
