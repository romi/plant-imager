#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html

from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantdb.rest_api_client import test_db_availability
from plantimager.webui.utils import get_dataset_dict

global dataset_dict

dash.register_page(__name__, path="/config")

# -----------------------------------------------------------------------------
# Forms and callbacks to connect to the PlantDB REST API.
# -----------------------------------------------------------------------------
rest_api_card = dbc.Card(
    id="rest-api-card",
    children=[
        dbc.CardHeader("PlantDB REST API"),
        dbc.CardBody([
            dbc.Row([
                # - Input form to specify REST API URL:
                dbc.Col([
                    dbc.Label("REST API URL:"),
                    dbc.Input(id="ip-address", type="url", value=REST_API_URL),
                    dbc.FormText(f"Use '{REST_API_URL}' for a local database.", color="secondary"),
                ], width=8, ),
                # - Input form to specify REST API port:
                dbc.Col([
                    dbc.Label("REST API port:"),
                    dbc.Input(id="ip-port", type="text", value=REST_API_PORT),
                    dbc.FormText(f"Should be '{REST_API_PORT}' by default.", color="secondary"),
                ], width=4, ),
            ]),
        ]),
        dbc.CardFooter([
            dbc.Row([
                # - Test connexion to REST API button
                dbc.Col([
                    dbc.Button("Test connexion", id="connect-button", color="primary"),
                    dbc.FormText(
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            "Unknown server availability."
                        ], color="info"),
                        id="connexion-status"),
                ], align="center", ),
                # - Load scans from REST API button
                dbc.Col([
                    dbc.Button("Load datasets", id="load-button", color="primary", disabled=True),
                    dbc.FormText(
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            "Undefined list of datasets."
                        ], color="info"),
                        id="load-status"),
                ], align="center", )
            ])
        ], style={"align-content": 'center'})

    ]
)

scanner_card = [
    dbc.Card(
        id="scanner-card",
        children=[
            dbc.CardHeader("Scanner configuration"),
            dbc.CardBody([
                dbc.Row([
                    # - Input form to specify CNC serial port:
                    dbc.Col([
                        dbc.Label("CNC serial port:"),
                        dbc.Input(id="cnc-port-input", type="text", value="/dev/ttyACM0",
                                  placeholder='Enter a serial port...'),
                        dbc.FormText("Should be something like `/dev/ttyACM0`", color="secondary"),
                    ], width=8, ),
                    # - Input form to specify Gimbal serial port:
                    dbc.Col([
                        dbc.Label("Gimbal serial port:"),
                        dbc.Input(id="gimbal-port-input", type="text", value="/dev/ttyACM1",
                                  placeholder='Enter a serial port...'),
                        dbc.FormText("Should be something like `/dev/ttyACM1`", color="secondary"),
                    ], width=8, ),
                    # - Input form to specify Camera URL:
                    dbc.Col([
                        dbc.Label("Camera URL:"),
                        dbc.Input(id="camera-url-input", type="url", value="192.168.122.1:10000",
                                  placeholder='Enter a valid URL...'),
                        dbc.FormText("Should be something like `192.168.122.1:10000`", color="secondary"),
                    ], width=8, ),
                ])
            ]),
            dbc.CardFooter([dbc.Row([
                dbc.Col([
                    dbc.Button("Export settings", id="hw-settings-button")
                ]),
                dbc.Col([
                    dbc.Button("Initialize scanner", id="hw-init-button")
                ])
            ])
            ])
        ]
    )
]

layout = html.Div([
    dcc.Store(id='cnc-port', data=None),
    dcc.Store(id='gimbal-port', data=None),
    dcc.Store(id='camera-url', data=None),
    dcc.Store(id='scanner-obj', data=None),
    # Content of the scan page:
    dbc.Button("< Back", href="/", style={'width': '200px'}),
    html.Br(),
    dbc.Row(
        id="conf-page-content",
        children=[
            dbc.Col(rest_api_card, md=6),
            dbc.Col(scanner_card, md=6),
        ]
    )
])


@callback(Output('connexion-status', 'children'),
          Output('load-button', 'disabled'),
          Output('rest-api-host', 'data'),
          Output('rest-api-port', 'data'),
          Input('connect-button', 'n_clicks'),
          State('ip-address', 'value'),
          State('ip-port', 'value'))
def test_connect(n_clicks, host, port):
    if test_db_availability(host, int(port)):
        res = dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"), "Server available.",
        ], color="success", )
    else:
        res = dbc.Alert([
            html.I(className="bi bi-x-octagon-fill me-2"), f"Server {host}:{port} unavailable!",
        ], color="danger", )
    return res, not res, host, port


@callback(Output('load-status', 'children'),
          Output('dataset-dict', 'data'),
          Input('load-button', 'n_clicks'),
          State('ip-address', 'value'),
          State('ip-port', 'value'))
def update_db(n_clicks, host, port):
    dataset_dict = get_dataset_dict(host, port)
    if len(dataset_dict) > 0:
        res = dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"), f"Loaded {len(dataset_dict)} dataset.",
        ], color="success", )
    else:
        res = dbc.Alert([
            html.I(className="bi bi-x-octagon-fill me-2"), f"Could not load any dataset!",
        ], color="danger", )
    return res, dataset_dict


@callback(Output('cnc-port', 'data'),
          Output('gimbal-port', 'data'),
          Output('camera-url', 'data'),
          Input('hw-settings-button', 'n_clicks'),
          State('cnc-port-input', 'value'),
          State('gimbal-port-input', 'value'),
          State('camera-url-input', 'value'),
          prevent_initial_call=True)
def set_hw_config(cnc_port, gimbal_port, camera_url):
    return cnc_port, gimbal_port, camera_url


@callback(Output('scanner-obj', 'data'),
          Input('hw-init-button', 'n_clicks'),
          State('cnc-port', 'data'),
          State('gimbal-port', 'data'),
          State('camera-url', 'data'),
          prevent_initial_call=True)
def init_scanner(n_clicks, cnc_port, gimbal_port, camera_url):
    from plantimager.scanner import Scanner
    from plantimager.dummy import CNC
    from plantimager.dummy import Gimbal
    from plantimager.dummy import Camera
    cnc = CNC()
    gimbal = Gimbal()
    camera = Camera()
    return Scanner(cnc, gimbal, camera)
    # from plantimager.grbl import CNC
    # from plantimager.blgimbal import Gimbal
    # from plantimager.urlcam import Camera
    # cnc = CNC(cnc_port, x_lims=[0, 800], y_lims=[0, 800], z_lims=[0, 100])
    # gimbal = Gimbal(gimbal_port, has_tilt=False, invert_rotation=True)
    # camera = Camera(camera_url)
    # return Scanner(cnc, gimbal, camera)
