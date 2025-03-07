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
    dbc.ModalHeader(
        dbc.ModalTitle(children=[
            html.I(className="bi bi-person-plus-fill me-2"),
            "Create New Account"
        ])
    ),
    dbc.ModalBody(children=[
        # Username input, e.g., "username" or "firstname"
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-person")  # Alternatives: bi-person-badge, bi-at
            ),
            dbc.Input(
                id="new-username-input",
                type="text",
                placeholder="Username",
            )
        ], className="mb-3"),
        # Full name input, e.g., "Firstname Lastname" or "Firstname Middlename Lastname"
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-person-vcard")  # Alternatives: bi-person-lines-fill, bi-card-text
            ),
            dbc.Input(
                id="new-fullname-input",
                type="text",
                placeholder="Full Name",
            )
        ], className="mb-3"),
        # Password input, e.g., "<PASSWORD>" or "<PASSWORD>"
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-key")  # Alternatives: bi-lock, bi-shield-lock
            ),
            dbc.Input(
                id="new-password-input",
                type="password",
                placeholder="Password",
            )
        ], className="mb-3"),
        # Password confirmation input
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-key")  # Alternatives: bi-lock, bi-shield-check
            ),
            dbc.Input(
                id="confirm-password-input",
                type="password",
                placeholder="Confirm Password",
            )
        ]),
        # Messages placeholders
        html.Div(id="password-match-message"),
        html.Div(id="registration-message")
    ]),
    dbc.ModalFooter([
        # Register button
        dbc.Button(
            children=[
                html.I(className="bi bi-check2-circle me-2"),  # Alternative: bi-box-arrow-in-right
                "Register"
            ],
            id="register-button",
            color="primary",
            className="me-2"
        )
    ])
], id="new-user-modal")

# Add the following callback functions

@callback(
    Output("new-user-modal", "is_open"),
    Input("new-user-button", "n_clicks"),
    State("new-user-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_register_modal(new_user_clicks, is_open):
    if new_user_clicks:
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
    """Callback handling user registration functionality.

    Validates input fields, matches password and confirmation password, and sends registration data to the
    backend API for account creation.

    Parameters
    ----------
    n_clicks : int
        The number of times the "register" button is clicked. Used to trigger the
        callback process.
    username : str
        The desired username entered by the user in the input field.
    fullname : str
        The full name of the user entered during the registration process.
    password : str
        The password provided by the user for their new account.
    confirm_password : str
        The confirmation of the password, which must match the `password` field.
    host : str
        The host address of the REST API for backend communication.
    port : int
        The port number of the REST API for backend communication.

    Returns
    -------
    str
        A message to indicate if passwords match or any other relevant feedback.
        It is returned as a children property of the "password-match-message" component.
    str
        A message to convey the registration result.
        It is returned as a children property of the "registration-message" component.
    """
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
