#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from base64 import b64decode
from logging import getLogger

import dash_bootstrap_components as dbc
import toml
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import get_asset_url
from dash import html
from dash import register_page

from plantimager.webui.utils import config_upload
from plantimager.webui.utils import create_temp_fsdb
from romitask.log import get_log_filename

register_page(__name__, path_template="/scan")

FORBIDDEN_CHAR = [
    ":", "/", "*", "#", "@", ">", "<", "?", "|", "\"", "\'"
]


# Update the contents of the TOML configuration file when uploading a configuration file:
@callback(Output('scan-cfg-toml', 'value'),
          Input('cfg-upload', 'contents'),
          prevent_initial_call=True)
def update_cfg(contents):
    """Get the contents of the TOML configuration file and return it to the text area."""
    content_type, content_string = contents.split(',')
    cfg = b64decode(content_string)
    return cfg.decode()


# Car to configure acquisition (scan) parameters:
configuration_card = [
    dbc.Card(
        id="configuration-card",
        children=[
            dbc.CardHeader("Configuration"),
            dbc.CardBody([
                dbc.Textarea(id="scan-cfg-toml", className="mb-3", size='md',
                             value=toml.dumps(toml.load(get_asset_url('hardware_scan_rx0.toml')[1:])),
                             title="The scan configuration in TOML format.",
                             placeholder="Scan configuration (TOML).",
                             style={'height': "65vh"}, persistence=True),
            ]),
            dbc.CardFooter([
                config_upload(),
            ], style={"align-content": 'center'})
        ]
    )
]

# Card to select the name of the dataset:
dataset_name_card = [
    dbc.Card(
        id="dataset-card",
        children=[
            dbc.CardHeader("Dataset"),
            dbc.CardBody([
                html.Div([
                    dbc.Label("Name of the dataset to create:"),
                    dbc.Input(id="dataset-name", placeholder="Dataset name", className="mb-3", invalid=True),
                    dbc.FormText(dcc.Markdown(
                        "The list of forbidden characters is: " + ', '.join([f'`{c}`' for c in FORBIDDEN_CHAR])
                    )),
                ]
                )
            ])
        ]
    )
]

# Car to run a scan with the PlantImager:
scan_card = [
    dbc.Card(
        id="scan-card",
        children=[
            dbc.CardHeader("Scan"),
            dbc.CardBody([
                dcc.Loading([
                    dbc.Button('Start scanning', id='scan-button')
                ]),
                dcc.Markdown(id='scan-response', children="_Run a scan first..._"),
            ]
            ),
            dbc.CardFooter([
                dbc.Accordion(
                    dbc.AccordionItem(children=[
                        dcc.Markdown(id="scan-output", children="_Run a scan first..._"),
                    ],
                        title="Detailed scan output:"
                    ),
                    start_collapsed=True, flush=True
                )
            ], style={'bs-accordion-btn-bg': '#21252908'})
        ]
    )
]

# Car to upload acquired dataset to PlantDB REST API.
upload_card = [
    dbc.Card(
        id="upload-card",
        children=[
            dbc.CardHeader("Upload"),
            dbc.CardBody([
                dcc.Loading([dbc.Button('Upload', id='upload-archive', disabled=True)]),
                dcc.Markdown(id='upload-response', children="_Upload first..._"),
            ]
            ),
            dbc.CardFooter([
                dbc.Accordion(
                    dbc.AccordionItem(children=[
                        dcc.Markdown(id="upload-output", children="_Upload first..._"),
                    ],
                        title="Detailed upload output:"
                    ),
                    start_collapsed=True, flush=True, style={'bs-accordion-btn-bg': '#21252908'}
                )
            ])
        ]
    )
]


# Callback to validate the selected dataset name:
@callback(Output('dataset-name', 'valid'),
          Output('dataset-name', 'invalid'),
          Input('dataset-name', 'value'),
          State('dataset-dict', 'data'),
          prevent_initial_call=True)
def validate_dataset_name(dataset_name, dataset_dict):
    """Callback to validate the selected dataset name.

    It should follow two rules:
        1. unicity: it should not exist in the database
        2. decency: no fancy/weird/impossible characters are allowed!

    Parameters
    ----------
    dataset_name : str
        The dataset name to validate.
    dataset_dict : dict
        The dataset indexed dictionary that exists in the database.

    Returns
    -------
    bool
        The `valid` state of the 'dataset-name' `Input` component.
    bool
        The `invalid` state of the 'dataset-name' `Input` component.
    """
    if dataset_name not in list(dataset_dict.keys()) and sum(
            [letter in FORBIDDEN_CHAR for letter in dataset_name]) == 0:
        return True, False
    else:
        return False, True


@callback(Output('scan-button', 'disabled'),
          Output('scan-response', 'children'),
          Output('scan-output', 'children'),
          Input('scan-button', 'n_clicks'),
          State('cfg-toml', 'value'),
          State('dataset-name', 'data'),
          prevent_initial_call=True)
def run_scan(n_clicks, cfg, dataset_name):
    task = "Scan"  # we will run a scan task
    from romitask.cli.romi_run_task import run_task
    # Create a temporary fsdb with the name of the dataset as suffix:
    tmp_db, dataset_path = create_temp_fsdb(dataset_name)
    # Create a combined logger using the configuration:
    logger = getLogger('reconstruct')
    log_fname = get_log_filename(task)

    # Execute the tasks:
    success = False
    try:
        run_task(dataset_path, task=task, config=toml.loads(cfg), logger=logger, log_fname=log_fname)
        success = True
    except Exception as e:
        logger.error(e)

    # Read and return the log:
    with open(dataset_path / log_fname, 'rb') as f:
        log = "```\n" + "".join([line.decode() for line in f.readlines()]) + "```"

    return True, success, log


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
            children=[
                dbc.Col(configuration_card, md=6),
                dbc.Col(dataset_name_card + [html.Br()] + scan_card + [html.Br()] + upload_card, md=6)
            ],
        ),
    ])
