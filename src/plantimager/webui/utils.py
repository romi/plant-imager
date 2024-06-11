import tempfile
from pathlib import Path

import requests
import toml
from dash import dcc
from dash import dcc
from dash import html
from dash import html

from plantdb.rest_api_client import list_scan_names
from plantdb.rest_api_client import parse_scans_info


def base_url(host, port):
    """Format the URL for the PlantDB REST API at given host and port.

    Parameters
    ----------
    host : str
        The hostname or IP address of the PlantDB REST API server.
    port : str
        The port number of the PlantDB REST API server.

    Returns
    -------
    str
        The formatted URL.
    """
    return f"http://{host}:{port}"


def get_dataset_dict(host, port):
    """Returns the dataset dictionary for the PlantDB REST API at given host url and port.

    Parameters
    ----------
    host : str
        The hostname or IP address of the PlantDB REST API server.
    port : str
        The port number of the PlantDB REST API server.

    Returns
    -------
    dict
        The dataset dictionary for the PlantDB REST API at given host url and port.

    See Also
    --------
    plantdb.rest_api_client.list_scan_names
    plantdb.rest_api_client.parse_scans_info
    """
    scans_list = list_scan_names(host, port)
    if len(scans_list) > 0:
        dataset_dict = parse_scans_info(host, port)
    else:
        dataset_dict = None
    return dataset_dict


def pipeline_cfg_url(host, port, scan_id):
    """Get the URL corresponding to the 'pipeline.toml' backup file for the given scan ID in a PlantDB REST API.

    Parameters
    ----------
    host : str
        The hostname or IP address of the PlantDB REST API server.
    port : str
        The port number of the PlantDB REST API server.
    scan_id : str
        The name of the dataset to test for the reconstruction pipeline.

    Returns
    -------
    str
        The URL corresponding to the 'pipeline.toml' backup file for the given scan ID.
    """
    return f"{base_url(host, port)}/files/{scan_id}/pipeline.toml"


def get_pipeline_cfg(host, port, scan_id):
    """Get the backup configuration file of the reconstruction pipeline for the given scan ID.

    Parameters
    ----------
    host : str
        The hostname or IP address of the PlantDB REST API server.
    port : str
        The port number of the PlantDB REST API server.
    scan_id : str
        The name of the dataset to test for the reconstruction pipeline.

    Returns
    -------
    dict
        The backup configuration for the reconstruction pipeline for the given scan ID.

    Examples
    --------
    >>> from plantimager.webui.utils import get_pipeline_cfg
    >>> get_pipeline_cfg('127.0.0.1','5000','real_plant')
    {}
    >>> cfg = get_pipeline_cfg('127.0.0.1','5000','real_plant_analyzed')
    """
    if has_pipeline_cfg(host, port, scan_id):
        return toml.loads(requests.get(pipeline_cfg_url(host, port, scan_id)).content.decode())
    else:
        return {}


def has_pipeline_cfg(host, port, scan_id):
    """Test if a named dataset has a reconstruction pipeline.

    Reconstruction pipeline are named 'pipeline.toml', so we test if the request from the file ressource is ok.

    Parameters
    ----------
    host : str
        The hostname or IP address of the PlantDB REST API server.
    port : str
        The port number of the PlantDB REST API server.
    scan_id : str
        The name of the dataset to test for the reconstruction pipeline.

    Returns
    -------
    bool
        Indicates if a reconstruction pipeline is found.

    Examples
    --------
    >>> from plantimager.webui.utils import has_pipeline_cfg
    >>> has_pipeline_cfg('127.0.0.1','5000','real_plant')
    False
    >>> has_pipeline_cfg('127.0.0.1','5000','real_plant_analyzed')
    True
    """
    return requests.get(pipeline_cfg_url(host, port, scan_id)).ok


def temp_fsdb_dir(scan_id):
    """Path to the temporary FSDB directory."""
    return Path(tempfile.gettempdir()) / f'romidb_{scan_id}'


def temp_scan_dir(scan_id):
    """Path to the temporary FSDB dataset directory."""
    return temp_fsdb_dir(scan_id) / scan_id


def config_upload():
    """The TOML configuration file upload component."""
    return dcc.Loading([
        dcc.Upload(id="cfg-upload",
                   children=html.Div(['Drag and Drop or ', html.B('Select'), ' a TOML configuration file.']),
                   style={
                       'width': '100%',
                       'height': '60px',
                       'lineHeight': '60px',
                       'borderWidth': '1px',
                       'borderStyle': 'dashed',
                       'borderRadius': '5px',
                       'textAlign': 'center',
                       'margin': '10px'
                   },
                   accept=".toml",
                   # Do not allow multiple files to be uploaded
                   multiple=False
                   ),
    ])
