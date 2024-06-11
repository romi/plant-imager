#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from base64 import b64decode

import dash_bootstrap_components as dbc
import toml
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import get_asset_url
from dash import html
from dash import register_page

from plantimager.webui.utils import config_upload

register_page(__name__, path_template="/scan")


# Update the contents of the TOML configuration file when uploading a configuration file:
@callback(Output('cfg-toml', 'value'),
          Input('cfg-upload', 'contents'),
          prevent_initial_call=True)
def update_cfg(contents):
    """Get the contents of the TOML configuration file and return it to the text area."""
    content_type, content_string = contents.split(',')
    cfg = b64decode(content_string)
    return cfg.decode()


# The card regrouping the reconstruction configuration parameters:
configuration_card = [
    dbc.Card(
        id="configuration-card",
        children=[
            dbc.CardHeader("Configuration"),
            dbc.CardBody(
                [
                    html.Div([
                        config_upload(),
                        dbc.Textarea(id="scan-cfg-toml", className="mb-3", size='md',
                                     value=toml.dumps(toml.load(get_asset_url('hardware_scan_rx0.toml')[1:])),
                                     title="The scan configuration in TOML format.",
                                     placeholder="Scan configuration (TOML).",
                                     style={'height': 400}, persistence=True),
                    ]),
                ]
            )
        ]
    )
]

# The card regrouping the buttons to reconstruct and upload:
scan_card = [
    dbc.Card(
        id="scan-card",
        children=[
            dbc.CardHeader("Scan"),
            dbc.CardBody(
                [
                    html.Div([
                        dcc.Textarea(id="dataset-name", placeholder="Dataset name", className="mb-3",),
                        dcc.Loading([dbc.Button('Start scanning', id='scan-button')]),
                        dcc.Markdown(id='scan-response', children="_Run a scan first..._"),
                        dbc.Accordion(
                            dbc.AccordionItem(children=[
                                dcc.Markdown(id="scan-output", children="_Run a scan first..._"),
                            ],
                                title="Detailed scan output:"
                            ),
                            start_collapsed=True, flush=True
                        )
                    ])
                ]
            )
        ]
    )
]


def layout(dataset_id=None, **kwargs):
    """Create the page layout for the reconstruction page.

    Parameters
    ----------
    dataset_id : str
        The name of the dataset to show in the reconstruction page.

    Returns
    -------
    html.Div
        The layout for the reconstruction page.
    """
    return html.Div([
        # Store the dataset id to use in the callback.
        dcc.Store(id='dataset-id', data=dataset_id),
        # Content of the reconstruction app:
        dbc.Row(
            id="app-content",
            children=[dbc.Col(configuration_card, md=6), dbc.Col(scan_card, md=6)],
        ),
    ])
