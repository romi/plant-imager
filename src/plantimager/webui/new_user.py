#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from urllib.parse import urljoin

import dash_bootstrap_components as dbc
import requests
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from plantdb.rest_api_client import base_url

# Create a button for new user registration
new_user_button = dbc.Button(
    [
        html.I(className="bi bi-person-plus me-2"),  # Add icon with right margin
        "Create Account"
    ],
    id="new-user-button",
    color="secondary",
    className="me-2",
)


# Create the new user registration modal
new_user_modal = dbc.Modal([
    dbc.ModalHeader([
        html.I(className="bi bi-person-plus-fill me-2"),  # Alternative: bi-person-vcard
        "Create New Account"
    ]),
    dbc.ModalBody([
        dbc.InputGroup([
            dbc.InputGroupText(
                html.I(className="bi bi-person-badge")  # Alternatives: bi-person, bi-at
            ),
            dbc.Input(
                id="new-username-input",
                type="text",
                placeholder="Username",
            )
        ], className="mb-3"),

        dbc.InputGroup([
            dbc.InputGroupText(
                html.I(className="bi bi-person-vcard")  # Alternatives: bi-person-lines-fill, bi-card-text
            ),
            dbc.Input(
                id="new-fullname-input",
                type="text",
                placeholder="Full Name",
            )
        ], className="mb-3"),

        dbc.InputGroup([
            dbc.InputGroupText(
                html.I(className="bi bi-key-fill")  # Alternatives: bi-lock-fill, bi-shield-lock
            ),
            dbc.Input(
                id="new-password-input",
                type="password",
                placeholder="Password",
            )
        ], className="mb-3"),

        dbc.InputGroup([
            dbc.InputGroupText(
                html.I(className="bi bi-key")  # Alternatives: bi-lock, bi-shield-check
            ),
            dbc.Input(
                id="confirm-password-input",
                type="password",
                placeholder="Confirm Password",
            )
        ], className="mb-3"),

        html.Div(id="password-match-message"),
        html.Div(id="registration-message")
    ]),
    dbc.ModalFooter([
        dbc.Button(
            [
                html.I(className="bi bi-check2-circle me-2"),  # Alternatives: bi-person-check, bi-box-arrow-in-right
                "Register"
            ],
            id="register-button",
            color="primary",
            className="me-2"
        ),
        dbc.Button(
            [
                html.I(className="bi bi-x-circle me-2"),  # Alternatives: bi-door-closed, bi-arrow-left
                "Close"
            ],
            id="close-register-modal",
            color="secondary"
        )
    ])
], id="new-user-modal")

# Add the following callback functions

@callback(
    Output("new-user-modal", "is_open"),
    [Input("new-user-button", "n_clicks"),
     Input("close-register-modal", "n_clicks")],
    [State("new-user-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_register_modal(new_user_clicks, close_clicks, is_open):
    if new_user_clicks or close_clicks:
        return not is_open
    return is_open


@callback(
    [Output("password-match-message", "children"),
     Output("registration-message", "children")],
    [Input("register-button", "n_clicks")],
    [State("new-username-input", "value"),
     State("new-fullname-input", "value"),
     State("new-password-input", "value"),
     State("confirm-password-input", "value"),
     State("rest-api-host", "data"),
     State("rest-api-port", "data")],
    prevent_initial_call=True
)
def register_user(n_clicks, username, fullname, password, confirm_password, host, port):
    if not n_clicks:
        return "", ""

    if not all([username, fullname, password, confirm_password]):
        return "", dbc.Alert("All fields are required", color="danger")

    if password != confirm_password:
        return dbc.Alert("Passwords do not match", color="danger"), ""

    try:
        response = requests.post(
            urljoin(base_url(host, port), '/register'),
            data=json.dumps({
                'username': username,
                'fullname': fullname,
                'password': password
            }),
            headers={'Content-Type': 'application/json'}
        )

        if response.ok:
            return "", dbc.Alert("Registration successful! You can now login.", color="success")
        else:
            error_msg = "Registration failed"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
            except json.JSONDecodeError:
                error_msg = response.text
            return "", dbc.Alert(error_msg, color="danger")

    except requests.exceptions.RequestException as e:
        return "", dbc.Alert(f"Connection error: {str(e)}", color="danger")
