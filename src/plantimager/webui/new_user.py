#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
from urllib.parse import urljoin

import dash_bootstrap_components as dbc
import requests
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from dash import no_update

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
        html.Div(id="registration-message", className="mt-3")
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


@callback(
    Output("new-user-modal", "is_open"),
    Input("new-user-button", "n_clicks"),
    State("new-user-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_register_modal(new_user_clicks, is_open):
    """Toggle the visibility state of the new user registration modal.

    This callback controls the opening and closing of the registration modal dialog
    when the new user button is clicked.

    Parameters
    ----------
    new_user_clicks : int or None
        Number of times the new user button has been clicked. ``None`` before first click.
    is_open : bool
        Current state of the modal dialog (True if open, False if closed).

    Returns
    -------
    bool
        The new state of the modal dialog - toggled from current state if button
        was clicked.
    """
    if new_user_clicks:
        return not is_open
    return is_open


@callback(
    Output('new-username-input', 'valid'),
    Output('new-username-input', 'invalid'),
    Input('new-username-input', 'value'),
    State('new-user-modal', 'is_open'),
    State('rest-api-host', 'data'),
    State('rest-api-port', 'data')
)
def validate_new_username(new_username, is_modal_open, host, port):
    """Validate if the entered username is available for registration.

    Makes an API request to check if the username already exists in the system.
    Updates the validation state of the username input field accordingly.

    Parameters
    ----------
    new_username : str or None
        The username entered by the user to validate.
    is_modal_open : bool
        Current state of the registration modal.
    host : str
        The host address of the REST API server.
    port : int
        The port number of the REST API server.

    Returns
    -------
    bool
        ``True`` if username is available (valid new username), ``False`` otherwise.
    bool
        ``True`` if username exists or there's an error (invalid new username), ``False`` otherwise.

    Raises
    ------
    requests.exceptions.RequestException
        If there are network connectivity issues or API errors.
    """
    if not is_modal_open or not new_username:
        return False, False
    # Make request to the login API endpoint
    try:
        response = requests.get(urljoin(base_url(host, port), f'/login?username={new_username}'))
        user_exists = response.json().get('exists', False)
        if user_exists:
            return False, True  # Unavailable username
        else:
            return True, False  # Available username
    except Exception as e:
        return False, True


@callback(
    [
        Output("new-password-input", "valid"),
        Output("new-password-input", "invalid"),
        Output("confirm-password-input", "valid"),
        Output("confirm-password-input", "invalid")
    ],
    [
        Input("new-password-input", "value"),
        Input("confirm-password-input", "value")
    ]
)
def validate_password_match(password, confirm_password):
    """Validate that the password and confirmation password match.

    Provides real-time validation feedback for both password input fields,
    ensuring they contain identical values.

    Parameters
    ----------
    password : str or None
        The value entered in the new password field.
    confirm_password : str or None
        The value entered in the password confirmation field.

    Returns
    -------
    tuple
        A tuple of four boolean values in the order:
    bool
        ``True`` if passwords match and not empty, ``False`` otherwise.
    bool
        ``True`` if passwords don't match, ``False`` otherwise.
    bool
        ``True`` if passwords match and not empty, ``False`` otherwise.
    bool
        ``True`` if passwords don't match, ``False`` otherwise.

    Notes
    -----
    Returns all ``False`` values if either password field is empty.
    """
    if not password or not confirm_password:
        return (
            False,  # new password not valid
            False,  # new password not invalid
            False,  # confirm password not valid
            False  # confirm password not invalid
        )
    passwords_match = password == confirm_password
    return (
        passwords_match,  # new password valid state
        not passwords_match,  # new password invalid state
        passwords_match,  # confirm password valid state
        not passwords_match  # confirm password invalid state
    )


@callback(
     Output("registration-message", "children"),
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
    """Process user registration by validating inputs and creating a new account.

    This callback handles the complete user registration process, including input
    validation, password matching, and account creation through the backend API.

    Parameters
    ----------
    n_clicks : int or None
        Number of times the register button has been clicked. ``None`` before first click.
    username : str
        The desired username for the new account.
    fullname : str
        The full name of the user.
    password : str
        The desired password for the new account.
    confirm_password : str
        Password confirmation entry.
    host : str
        The host address of the REST API server.
    port : int
        The port number of the REST API server.

    Returns
    -------
    dash_bootstrap_components.Alert
        A Bootstrap alert component containing either:
        - Success message if registration is successful
        - Error message if validation fails or API request fails

    Notes
    -----
    This callback uses prevent_initial_call=True to avoid triggering on page load.
    The function performs the following validations:
    - All fields must be non-empty
    - Passwords must match
    - Backend API must successfully create the account

    Raises
    ------
    requests.exceptions.RequestException
        If there are network connectivity issues or API errors.
    json.JSONDecodeError
        If the API response contains invalid JSON data.

    See Also
    --------
    validate_new_username : Function for validating username availability
    validate_password_match : Function for validating password matching
    """
    if not n_clicks:
        return ""

    if not all([username, fullname, password, confirm_password]):
        return dbc.Alert("All fields are required", color="danger", class_name="mb-0")

    if password != confirm_password:
        return dbc.Alert("Passwords do not match", color="danger", class_name="mb-0")

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
            return dbc.Alert("Registration successful! You can now login.", color="success", class_name="mb-0")
        else:
            error_msg = "Registration failed"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
            except json.JSONDecodeError:
                error_msg = response.text
            return dbc.Alert(error_msg, color="danger", class_name="mb-0")

    except requests.exceptions.RequestException as e:
        return dbc.Alert(f"Connection error: {str(e)}", color="danger", class_name="mb-0")
