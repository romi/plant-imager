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
from dash import html

from plantimager.webui.utils import config_upload
from plantimager.webui.utils import create_temp_fsdb
from romitask.log import get_log_filename

# Characters not allowed in dataset names for system compatibility
FORBIDDEN_CHAR = [":", "/", "*", "#", "@", ">", "<", "?", "|", "\"", "\'"]

# Card for scan configuration settings using TOML format
configuration_card = [
    dbc.Card(
        id="configuration-card",
        children=[
            dbc.CardHeader(children=[html.I(className="bi bi-code-square me-2"), "Configuration"]),
            dbc.CardBody([
                dbc.Textarea(id="scan-cfg-toml", class_name="mb-3", size='md',
                             value=toml.dumps(toml.load('assets/hardware_scan_rx0.toml')),
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

# Card for dataset name input with validation
dataset_name_card = [
    dbc.Card(
        id="dataset-card",
        children=[
            dbc.CardHeader(children=[html.I(className="bi bi-tag me-2"), "Dataset"]),
            dbc.CardBody(children=[
                html.Div([
                    dbc.Label("Name of the dataset to create:"),
                    dbc.Input(id="dataset-input-name", placeholder="Dataset name",
                              class_name="mb-3", invalid=True, persistence=True),
                    dbc.FormText(dcc.Markdown(
                        "The list of forbidden characters is: " + ', '.join([f'`{c}`' for c in FORBIDDEN_CHAR])
                    )),
                ]),
                html.Div(children=[
                    dbc.Alert(
                        "Dataset name already exists. Please choose a different name.",
                        color="danger",
                        dismissable=True
                    )
                ], id='dataset-exists-message', style={'display': 'none'}),
            ]),
        ]
    )
]

# Card containing scan controls and status information
scan_card = [
    dbc.Card(
        id="scan-card",
        children=[
            dbc.CardHeader(children=[html.I(className="bi bi-camera me-2"), "Scan"]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dcc.Loading([
                            dbc.Button(
                                children=[
                                    html.I(className="bi bi-play-fill me-2"),
                                    'Start scanning'
                                ],
                                id='scan-button'
                            )
                        ]),
                    ], width=6),
                    dcc.Markdown(id='scan-response', children="_Run a scan first..._"),
                ])
            ]),
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

# Main container for the "scan" layout: two equally sized columns
# Left column, containing the configuration card
# Right column, containing multiple stacked cards
scan_layout = html.Div(
    children=[
        dbc.Row([
            dbc.Col(configuration_card, md=6),
            dbc.Col(dataset_name_card + [html.Br()] + scan_card, md=6)
        ])
    ], id="scan-page-layout"
)


@callback(Output('scan-cfg-toml', 'value'),
          Input('cfg-upload', 'contents'),
          prevent_initial_call=True)
def update_toml_cfg(contents):
    # Parse base64 encoded config file contents and update TOML text area
    content_type, content_string = contents.split(',')
    cfg = b64decode(content_string)
    return cfg.decode()


def all_valid_characters(dataset_name):
    """Validates if all characters in a given dataset name are permissible.

    Parameters
    ----------
    dataset_name : str
        The name of the dataset to be validated.

    Returns
    -------
    bool
        ``True`` if all characters in the dataset name are valid otherwise, ``False``.
    """
    return sum([letter in FORBIDDEN_CHAR for letter in dataset_name]) == 0


def is_valid_dataset_name(dataset_name, existing_datasets):
    if dataset_name not in existing_datasets and all_valid_characters(dataset_name):
        return True
    else:
        return False


# Callback to validate the selected dataset name:
@callback(
    Output('dataset-input-name', 'invalid'),
    Output('dataset-input-name', 'valid'),
    Output('dataset-id', 'data'),
    Input('dataset-input-name', 'value'),
    State('dataset-list', 'data')
)
def validate_dataset_name(dataset_name, existing_datasets):
    """Callback to validate the selected dataset name.

    It should follow two rules:
        1. unicity: it should not exist in the database
        2. decency: no fancy/weird/impossible characters are allowed!

    Parameters
    ----------
    dataset_name : str
        The dataset name to validate.
    existing_datasets : list
        The dataset indexed dictionary that exists in the database.

    Returns
    -------
    bool
        The `invalid` state of the 'dataset-input-name' `Input` component.
    bool
        The `valid` state of the 'dataset-input-name' `Input` component.
    str
        The name of the dataset.
    """
    if is_valid_dataset_name(dataset_name, existing_datasets):
        return False, True, dataset_name
    else:
        return True, False, dataset_name


@callback(
    Output('dataset-exists-message', 'style'),
    Input('dataset-input-name', 'value'),
    State('dataset-list', 'data')
)
def check_dataset_name_uniqueness(dataset_name, existing_datasets):
    if dataset_name in existing_datasets:
        return {'display': 'block', 'margin-top': '10px'}
    else:
        return {'display': 'none'}


@callback(
    Output('scan-button', 'disabled'),
    Input('dataset-input-name', 'valid'),
)
def disable_scan_button(valid):
    return not valid


@callback(
    Output('scan-response', 'children'),
    Output('scan-output', 'children'),
    Input('scan-button', 'n_clicks'),
    State('scan-cfg-toml', 'value'),
    State('dataset-input-name', 'value'),
    prevent_initial_call=True
)
def run_scan(_, cfg, dataset_name):
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

    return True, success, log, False
