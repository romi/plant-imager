#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from base64 import b64decode
from io import BytesIO
from logging import getLogger
from zipfile import ZipFile

import dash_bootstrap_components as dbc
import requests
import toml
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import get_asset_url
from dash import html
from dash import register_page

from plantimager.webui.utils import base_url
from plantimager.webui.utils import config_upload
from plantimager.webui.utils import create_temp_fsdb
from plantimager.webui.utils import temp_scan_dir
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
                    dbc.Input(id="dataset-name", placeholder="Dataset name",
                              className="mb-3", invalid=True, persistence=True),
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
                dbc.Row([
                    dbc.Col([
                        dcc.Loading([
                            dbc.Button('Start scanning', id='scan-button')
                        ]),
                    ], width=6),
                    dbc.Col([
                        dbc.Button('Preview', id='preview-button', disabled=True)
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

# Car to upload acquired dataset to PlantDB REST API.
upload_card = [
    dbc.Card(
        id="upload-card",
        children=[
            dbc.CardHeader("Upload"),
            dbc.CardBody([
                dcc.Loading([dbc.Button('Upload', id='upload-button', disabled=True)]),
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

preview_modal = dbc.Modal([
    dbc.ModalHeader(
        dbc.ModalTitle(id='preview-title', children="Dataset preview")
    ),
    dbc.ModalBody(id='preview-carousel'),
], id="modal-fs", fullscreen=True, )


# Callback to validate the selected dataset name:
@callback(Output('dataset-name', 'valid'),
          Output('dataset-name', 'invalid'),
          Output('dataset-id', 'data'),
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
    str
        The name of the dataset.
    """
    if dataset_name not in list(dataset_dict.keys()) and sum(
            [letter in FORBIDDEN_CHAR for letter in dataset_name]) == 0:
        return True, False, dataset_name
    else:
        return False, True, dataset_name


@callback(Output('scan-button', 'disabled'),
          Output('scan-response', 'children'),
          Output('scan-output', 'children'),
          Output('preview-button', 'disabled'),
          Output('upload-button', 'disabled'),
          Input('scan-button', 'n_clicks'),
          State('scan-cfg-toml', 'value'),
          State('dataset-name', 'value'),
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

    return True, success, log, False, False


# Callback of the "upload-button" button:
@callback(Output('upload-response', 'children'),
          Output('upload-output', 'children'),
          Input('upload-button', 'n_clicks'),
          State('dataset-id', 'data'),
          State('rest-api-host', 'data'),
          State('rest-api-port', 'data'),
          prevent_initial_call=True)
def upload_archive(n_clicks, scan_id, host, port):
    """Create an archive of the local dataset and send it to the PlantDB REST API using a POST request."""
    # Local path to search for files to archive
    scan_path = temp_scan_dir(scan_id)
    # List to store file paths to archive
    file_paths = []
    # Recursively search for files
    for root, dirs, files in os.walk(scan_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    # Create a zip file in memory
    zip_data = BytesIO()
    with ZipFile(zip_data, mode='w') as zip_file:
        for file_path in file_paths:
            # Check if the file exists
            if os.path.isfile(file_path):
                # Add the file to the zip,
                # removing the path to the scan directory not to get the full path in archived file names
                zip_file.write(file_path,
                               arcname=file_path.replace(str(scan_path) + '/', ''))
            else:
                print(f"Warning: {file_path} is not a file and will be skipped.")

    # Send the POST request
    url = f"{base_url(host, port)}/archive/{scan_id}"
    files = {'zip_file': ('archive.zip', zip_data.getvalue())}
    response = requests.post(url, files=files)

    # Check the response to the POST request:
    if response.ok:
        return 'Zip file uploaded successfully', "```\n" + "\n".join(response.json()['files']) + "```"
    else:
        return 'Error uploading zip file', "```\n" + response.text + "```"


def preview_carousel(img_uri_list):
    carousel = dbc.Carousel(
        items=[{"key": i, "src": img_uri, "caption": f"Image {str(i).zfill(5)}"} for i, img_uri in
               enumerate(img_uri_list)],
        controls=True, indicators=True, className="carousel-fade",
    )
    return carousel


@callback(Output('preview-title', 'children'),
          Output('preview-carousel', 'children'),
          Input('preview-button', 'n_clicks'),
          State('dataset-id', 'data'),
          prevent_initial_call=True)
def preview(n_clicks, dataset_id):
    # Local path to search for image files to preview:
    scan_path = temp_scan_dir(dataset_id)
    img_path = scan_path / 'images'
    img_uri_list = [p for p in img_path.iterdir() if p.is_file()]
    return f"'{dataset_id}' dataset preview", preview_carousel(img_uri_list)


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
        # Content of the scan page:
        dbc.Row(
            id="scan-page-content",
            children=[
                dbc.Col(configuration_card, md=6),
                dbc.Col(dataset_name_card + [html.Br()] + scan_card + [html.Br()] + upload_card, md=6)
            ],
        ),
    ])
