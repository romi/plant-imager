#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from requests import RequestException

from plantdb.rest_api_client import REST_API_PORT
from plantdb.rest_api_client import REST_API_URL
from plantdb.rest_api_client import base_url
from plantdb.rest_api_client import list_scan_names
from plantdb.rest_api_client import test_host_port_availability


def dataset_cfg_status(is_connected):
    """Generate a database status icon based on connection state.

    Creates a Bootstrap icon element representing the database connection status.
    Returns a check icon when connected and a gear icon when disconnected.

    Parameters
    ----------
    is_connected : bool
        Flag indicating whether the database connection is established.

    Returns
    -------
    dash.html.I
        A Bootstrap icon component with appropriate class based on connection status.
    """
    if is_connected:
        return html.I(className="bi bi-database-check fs-3")
    else:
        return html.I(className="bi bi-database-gear fs-3")


def create_dataset_cfg_icon(is_connected=False, dataset_list=None):
    """Create a navigation link with database status icon and dataset counter badge.

    Creates a Bootstrap NavLink component that displays a database status icon and
    a badge showing the number of datasets. The icon changes appearance based on
    connection status.

    Parameters
    ----------
    is_connected : bool, optional
        Flag indicating whether the database connection is established,
        by default False
    dataset_list : list, optional
        List of datasets to count, by default empty list

    Returns
    -------
    dash.bootstrap_components.NavLink
        A navigation link component containing:
        - Database status icon
        - Badge showing dataset count
        The NavLink is styled and positioned according to the application's design.
    """
    if dataset_list is None:
        dataset_list = []
    return dbc.NavLink(
        children=[
            dataset_cfg_status(is_connected),
            dbc.Badge(
                children=f"{len(dataset_list)}",
                id="dataset-count-badge",
                color="primary",
                className="position-absolute top-45 start-100 translate-middle",
                pill=True
            )
        ],
        id='plantdb-cfg-button',
        n_clicks=0,
        className="position-relative align-left",
        style={'color': "#f3f3f3"},
    )

# Create PlantDB REST API configuration button component for the navigation bar
cfg_button = create_dataset_cfg_icon()
cfg_tooltip = dbc.Tooltip(
    children="Configure PlantDB REST API connection and load dataset list.",
    target="plantdb-cfg-button",
    placement="bottom",
)

# Card component for PlantDB REST API configuration
plantdb_cfg_modal = html.Div(children=[
    dbc.Modal(id="plantdb-cfg-modal", children=[
        dbc.ModalHeader(
            dbc.ModalTitle(
                children=[
                    html.I(className="bi bi-database-gear-fill me-2"),
                    "PlantDB REST API configuration"
                ]
            )
        ),
        dbc.ModalBody(children=[
            # URL input field for REST API endpoint
            html.Div(children=[
                dbc.Label([html.I(className="bi bi-link-45deg me-2"), "REST API URL:"]),
                dbc.Input(id="ip-address", type="url"),
                dbc.FormText(f"Use '{REST_API_URL}' for a local database.", color="secondary"),
            ]),
            # Port number input for REST API
            html.Div(children=[
                dbc.Label([html.I(className="bi bi-hdd-network me-2"), "REST API port:"]),
                dbc.Input(id="ip-port", type="text"),
                dbc.FormText(f"Should be '{REST_API_PORT}' by default.", color="secondary"),
            ]),
            html.Br(),
            dbc.Row(children=[
                # Connection test button
                dbc.Col([
                    dbc.Button(
                        children=[
                            html.I(className="bi bi-plug-fill me-2"),
                            "Test connexion"
                        ],
                        id="connect-plantdb-button",
                        color="primary",
                        class_name="w-100",
                    ),
                ], width=6),
                # Dataset loading button
                dbc.Col([
                    dbc.Button(
                        children=[
                            html.I(className="bi bi-cloud-download me-2"),
                            "Load datasets"
                        ],
                        id="load-plantdb-button",
                        color="primary",
                        class_name="w-100",
                        disabled=True,
                    )
                ], width=6),
            ]),
        ]),
        dbc.ModalFooter(children=[
            # PlantDB status display
            html.Div(id="plantdb-status-form", className="w-100"),
            html.Div(id="load-status-form", className="w-100"),
        ])
    ])
])


@callback(Output("plantdb-cfg-modal", "is_open"),
          Input('plantdb-cfg-button', 'n_clicks'),
          State('plantdb-cfg-modal', 'is_open'),
          prevent_initial_call=True)
def toggle_plantdb_cfg_modal(n_clicks, is_open):
    """Toggle the visibility state of the PlantDB configuration modal.

    This callback function controls the opening and closing of the PlantDB configuration
    modal dialog. It is triggered by clicks on the configuration button and toggles
    the modal's visibility state.

    Parameters
    ----------
    n_clicks : int
        Number of times the plantdb-cfg-button has been clicked. Used to determine
        when to toggle the modal state.
    is_open : bool
        Current visibility state of the modal.

    Returns
    -------
    bool or None
        The new visibility state of the modal. Returns the opposite of the current
        state when n_clicks > 0, otherwise returns None.
    """
    if n_clicks > 0:
        return not is_open


@callback(
    Output("ip-address", "value"),
    Input("plantdb-cfg-modal", "is_open"),
    State("rest-api-host", "data")
)
def update_ip_address(modal_is_open, stored_host):
    """Callback updating the value of the IP address field when opening the PlantDB configuration modal.

    Parameters
    ----------
    modal_is_open : bool
        Indicates whether the configuration modal is currently open.
    stored_host : str or None
        The stored value of the REST API host. Can be ``None`` if not previously set.

    Returns
    -------
    str
        The IP address to be used, either the stored host value or the ``REST_API_URL`` constant.
    """
    if modal_is_open:
        return stored_host if stored_host is not None else REST_API_URL
    else:
        return stored_host


# Callback to update IP port from stored value
@callback(
    Output("ip-port", "value"),
    Input("plantdb-cfg-modal", "is_open"),
    State("rest-api-port", "data")
)
def update_ip_port(modal_is_open, stored_port):
    """Callback updating the value of the port field for IP address when opening the PlantDB configuration modal.

    Parameters
    ----------
    modal_is_open : bool
        Boolean indicating whether the configuration modal is open or closed.
    stored_port : str or None
        Stored port value retrieved from the state. Can be ``None`` if not specified.

    Returns
    -------
    str
        Value to be set for the "ip-port" input field, either the stored port value or the ``REST_API_PORT`` constant.
    """
    if modal_is_open:
        return stored_port if stored_port is not None else REST_API_PORT
    else:
        return stored_port


@callback(
    Output("plantdb-status-form", "children"),
    Input("connected", "data"),
    State("rest-api-host", "data"),
    State("rest-api-port", "data"),
)
def show_plantdb_status(status, host, port):
    """Display the connection status of the PlantDB server in a Bootstrap alert component.

    This callback function generates a styled alert component that shows whether the
    PlantDB server is available or not. The alert includes an icon and descriptive text
    with the server's host and port information when applicable.

    Parameters
    ----------
    status : bool or None
        Connection status of the PlantDB server:
        - None: status unknown
        - True: server is available
        - False: server is unavailable
    host : str
        Hostname or IP address of the PlantDB server
    port : int
        Port number of the PlantDB server

    Returns
    -------
    dash_bootstrap_components.Alert
        A Bootstrap alert component with appropriate styling and message based on
        the connection status:
        - Info (blue): when status is unknown
        - Success (green): when server is available
        - Danger (red): when server is unavailable
    """
    if status is None:
        status_form = dbc.Alert(children=[
            html.I(className="bi bi-info-circle-fill me-2"),
            "Unknown server availability."
        ], color="info")
    elif status:
        status_form = dbc.Alert(children=[
            html.I(className="bi bi-check-circle-fill me-2"), f"Server {host}:{port} available.",
        ], color="success")
    else:
        status_form = dbc.Alert(children=[
            html.I(className="bi bi-x-octagon-fill me-2"), f"Server {host}:{port} unavailable!",
        ], color="danger")
    return status_form


# Callback to test REST API connection and update UI accordingly
@callback(
    Output('connected', 'data'),
    Output('load-plantdb-button', 'disabled'),
    Output('rest-api-host', 'data'),
    Output('rest-api-port', 'data'),
    Input('connect-plantdb-button', 'n_clicks'),
    State('ip-address', 'value'),
    State('ip-port', 'value'),
    State('rest-api-host', 'data'),
    State('rest-api-port', 'data')
)
def check_server_availability(_, host, port, stored_host, stored_port):
    """Checks the availability of a server based on the provided host and port and updates the UI accordingly.

    Parameters
    ----------
    _ : int
        The n_clicks property of the load-plantdb-button element, which triggers the callback (not used).
    host : str
        The IP address or hostname of the server to test.
    port : int
        The port number of the server to test.
    stored_host : str
        The previously stored server host value, used if the connection test fails.
    stored_port : int
        The previously stored server port value, used if the connection test fails.

    Returns
    -------
    bool
        A storer flag indicating whether the connection test was successful.
    bool
        A boolean indicating whether the load button should be disabled.
    str
        The updated server host value to store.
    int
        The updated server port value to store.
    """
    if host is None:
        host = stored_host
    if port is None:
        port = stored_port
    if host.startswith("http://"):
        host = host[7:]
    elif host.startswith("https://"):
        host = host[8:]

    try:
        test_host_port_availability(base_url(host, port))
    except:
        is_available = False
    else:
        is_available = True

    if is_available:
        return True, False, host, port
    else:
        return False, True, host, port


@callback(
    Output("plantdb-cfg-button", "children"),
    Input("connected", "data"),
    State("dataset-list", "data"),
)
def update_plantdb_cfg_button(status, dataset_list):
    """Update the PlantDB configuration button's appearance based on connection status.

    This callback function updates the visual representation of the PlantDB configuration
    button in the navigation bar depending on the connection status and dataset list state.
    It uses the create_dataset_cfg_icon function to generate the appropriate icon.

    Parameters
    ----------
    status : bool or None
        The connection status to the PlantDB REST API.
        ``None`` indicates no connection attempt has been made.
        ``True`` indicates successful connection.
        ``False`` indicates failed connection.
    dataset_list : list or None
        List of available datasets from the PlantDB.
        ``None`` if no datasets are loaded or connection is not established.

    Returns
    -------
    dash.html.Component
        A Dash HTML component representing the configuration button icon
        with appropriate styling based on the connection status.
    """
    return create_dataset_cfg_icon(status, dataset_list)


# Callback to load dataset list from PlantDB REST API
@callback(
    Output('load-status-form', 'children'),
    Output('dataset-list', 'data'),
    Input('load-plantdb-button', 'n_clicks'),
    Input('connected', 'data'),
    State('rest-api-host', 'data'),
    State('rest-api-port', 'data'),
    prevent_initial_call=True,
)
def update_dataset_list(n_clicks, connected, host, port):
    """Callback updating the dataset list and displaying the load status when a user clicks the load button.

    Parameters
    ----------
    n_clicks : int
        The n_clicks property of the load-plantdb-button element, which triggers the callback (not used).
    connected : bool
        The connection status of the PlantDB REST API server.
    host : str
        The IP address of the server to connect to for retrieving dataset names.
    port : str
        The port number of the server to use for the connection.

    Returns
    -------
    dash_bootstrap_components.Alert
        An alert component indicating success or failure of dataset retrieval.
    list of str
        A list of dataset names retrieved from the server.
    """
    try:
        dataset_list = list_scan_names(host, port)
    except RequestException:
        dataset_list = []

    if dataset_list:
        status = dbc.Alert(children=[
            html.I(className="bi bi-check-circle-fill me-2"),
            f"Loaded {len(dataset_list)} dataset.",
        ], color="success")
    else:
        status = dbc.Alert([
            html.I(className="bi bi-x-octagon-fill me-2"),
            f"Could not load any dataset!",
        ], color="danger")

    return status, dataset_list


@callback(
    Output("dataset-count-badge", "children"),
    Input("dataset-list", "data")  # Assuming you have a dataset list stored in dcc.Store
)
def update_dataset_badge(dataset_list):
    """Update the dataset count badge with the current number of datasets.

    This callback function updates a badge element in the UI to display the total
    number of datasets currently available in the system. It converts the length
    of the dataset list to a string for display.

    Parameters
    ----------
    dataset_list : list
        A list containing the dataset names stored in the dcc.Store component.

    Returns
    -------
    str
        String representation of the number of datasets in the list.
    """
    return str(len(dataset_list))
