#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantdb.rest_api_client import base_url
from plantdb.rest_api_client import list_scan_names
from plantdb.rest_api_client import test_host_port_availability

# Card component for PlantDB REST API configuration
plantdb_cfg_modal = html.Div(
    [
        dbc.Modal(id="plantdb-cfg-modal", is_open=False, centered=True, size="sm"),
        dbc.ModalHeader(
            dbc.ModalTitle("PlantDB REST API configuration")
        ),
        dbc.ModalBody(
            [
                dbc.Row([
                    dbc.Col([
                        # URL input field for REST API endpoint
                        dbc.Col([
                            dbc.Label("REST API URL:"),
                            dbc.Input(id="ip-address", type="url"),
                            dbc.FormText(f"Use '{REST_API_URL}' for a local database.", color="secondary"),
                        ], width=8),

                        # Port number input for REST API
                        dbc.Col([
                            dbc.Label("REST API port:"),
                            dbc.Input(id="ip-port", type="text"),
                            dbc.FormText(f"Should be '{REST_API_PORT}' by default.", color="secondary"),
                        ], width=4),
                    ])
                ])
            ]
        ),
        dbc.ModalFooter([
            dbc.Row([
                # Connection test button and status display
                dbc.Col([
                    dbc.Button("Test connexion", id="connect-button", color="primary"),
                    dbc.FormText(
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            "Unknown server availability."
                        ], color="info"),
                        id="connexion-status"),
                ], align="center"),

                # Dataset loading button and status display
                dbc.Col([
                    dbc.Button("Load datasets", id="load-button", color="primary", disabled=True),
                    dbc.FormText(
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            "Undefined list of datasets."
                        ], color="info"),
                        id="load-status"),
                ], align="center")
            ])
        ])
    ]
)


# Callback to update IP address from stored value
@callback(
    Output("ip-address", "value"),
    Input("plantdb-cfg_modal", "is_open"),
    State("rest-api-host", "data")
)
def update_ip_address(modal_is_open, stored_host):
    if modal_is_open:
        return stored_host if stored_host is not None else REST_API_URL


# Callback to update IP port from stored value
@callback(
    Output("ip-port", "value"),
    Input("plantdb-cfg_modal", "is_open"),
    State("rest-api-port", "data")
)
def update_ip_address(modal_is_open, stored_port):
    if modal_is_open:
        return stored_port if stored_port is not None else REST_API_URL


# Callback to test REST API connection and update UI accordingly
@callback(
    Output('connexion-status', 'children'),
    Output('load-button', 'disabled'),
    Output('rest-api-host', 'data'),
    Output('rest-api-port', 'data'),
    Input('connect-button', 'n_clicks'),
    State('ip-address', 'value'),
    State('ip-port', 'value'),
    State('rest-api-host', 'data'),
    State('rest-api-port', 'data')
)
def test_connect(n_clicks, host, port, stored_host, stored_port):
    is_available = test_host_port_availability(base_url(host, port))
    status = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"), "Server available.",
    ], color="success") if is_available else dbc.Alert([
        html.I(className="bi bi-x-octagon-fill me-2"), f"Server {host}:{port} unavailable!",
    ], color="danger")
    if is_available:
        return status, False, host, port
    else:
        return status, True, stored_host, stored_port


# Callback to load dataset list from PlantDB REST API
@callback(
    Output('load-status', 'children'),
    Output('dataset-list', 'data'),
    Input('load-button', 'n_clicks'),
    State('ip-address', 'value'),
    State('ip-port', 'value')
)
def update_db(n_clicks, host, port):
    scans_list = list_scan_names(host, port)
    status = dbc.Alert([
        html.I(className="bi bi-check-circle-fill me-2"), f"Loaded {len(scans_list)} dataset.",
    ], color="success") if scans_list else dbc.Alert([
        html.I(className="bi bi-x-octagon-fill me-2"), f"Could not load any dataset!",
    ], color="danger")
    return status, scans_list
