#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash_ag_grid as dag
import pandas as pd
from dash import Input
from dash import Output
from dash import callback
from dash import html
from dash import register_page

from plantimager.webui.utils import base_url

register_page(__name__, path='/')

# -----------------------------------------------------------------------------
# Table
# -----------------------------------------------------------------------------

TASKS = [
    "Colmap",
    "PointCloud",
    "Mesh",
    "Skeleton",
    "TreeGraph",
    "AngleData",
]

layout = html.Div(id="dataset-table", style={"width": "100%", "height": "84vh"})


def _carousel_href(ds_id: str) -> str:
    """The URL pointing to the image carousel for the given dataset."""
    return f"/carousel/{ds_id}"


def _column_defs(col_name):
    """Set the properties of the AG Grid columns."""
    cdef = {"field": col_name, 'filter': True}
    # Enable markdown rendering to include images and icons:
    if col_name in ["Thumbnail"] + TASKS:
        cdef["cellRenderer"] = "markdown"
    return cdef


# Icon indication that the task has been performed:
CHECK = "![alt text: Yes](https://icons.getbootstrap.com/assets/icons/check-circle.svg)"
# Icon indication that the task has not been performed:
CROSS = "![alt text: No](https://icons.getbootstrap.com/assets/icons/x-circle.svg)"


@callback(Output('dataset-table', 'children'),
          Input('dataset-dict', 'data'),
          Input('rest-api-host', 'data'),
          Input('rest-api-port', 'data'))
def update_table(dataset_dict, url, port):
    if dataset_dict is not None:
        table_dict = {col: [] for col in ["Thumbnail", "Name", "Date", "Species", "Images"] + TASKS}
        api_url = base_url(url, port)
        for ds_id, md in dataset_dict.items():
            thumbnail_url = md["thumbnailUri"]
            # Include the first image thumbnail and a link to the carousel
            table_dict["Thumbnail"].append(
                f"[![thumbnail]({api_url}{thumbnail_url})]({_carousel_href(ds_id)})"
            )
            table_dict["Name"].append(ds_id)
            table_dict["Date"].append(md["metadata"]["date"])
            table_dict["Species"].append(md["metadata"]["species"])
            table_dict["Images"].append(md["metadata"]["nbPhotos"])
            # Use icons to indicate tasks status:
            for task in TASKS:
                table_dict[task].append(CHECK if md[f"has{task}"] else CROSS)
        df = pd.DataFrame().from_dict(table_dict)
        table = dag.AgGrid(
            id="get-started-example-basic-df",
            rowData=df.to_dict("records"),
            columnDefs=[_column_defs(i) for i in df.columns],
            dashGridOptions={
                "rowHeight": 100, "animateRows": False,
                "pagination": True, "paginationAutoPageSize": True,
            },
            # columnSize="autoSize",
            style={"height": 800, "width": "100%"},
        )
    else:
        table = "No dataset loaded yet!"
    return table
