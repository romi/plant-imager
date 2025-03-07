#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
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

from plantdb.rest_api_client import base_url
from plantimager.webui.new_user import new_user_button

# Local storage for users
USERS_DB = {
    'admin': {'password': 'password', 'fullname': "Indiana Jones"},
    'agent007': {'password': 'user007', 'fullname': "James Bond"},
    'batman': {'password': 'joker', 'fullname': "Bruce Wayne"},
}


def create_avatar(fullname):
    """Create an avatar with user's initials in a colored circle"""
    if not fullname:
        return None

    # Get initials from fullname
    initials = ''.join(name[0].upper() for name in fullname.split() if name)

    # Generate a consistent color based on the fullname
    color_hash = hashlib.md5(fullname.encode('utf-8')).hexdigest()
    bg_color = f"#{color_hash[:6]}"

    avatar_style = {
        'backgroundColor': bg_color,
        'color': 'white',
        'borderRadius': '50%',
        'width': '35px',
        'height': '35px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'fontSize': '14px',
        'fontWeight': 'bold',
    }

    return html.Div(initials, style=avatar_style)


def create_login_button(is_logged_in=False, user_fullname=None):
    """Create a login/logout button with avatar"""
    if is_logged_in and user_fullname:
        return dbc.NavLink(
            children=create_avatar(user_fullname),
            id="login-avatar-button",
            n_clicks=0
        )
    else:
        return dbc.NavLink(
            children=html.I(className="bi bi-person-bounding-box fs-3"),
            id="login-avatar-button",
            n_clicks=0,
            style={'color': "#f3f3f3"},
        )


login_button_tooltip = dbc.Tooltip(
    children="Login to access the Plant Imager.",
    target="login-avatar-button",
    placement="bottom",
)

# Create login button components for the navigation bar
login_button = create_login_button()

login_modal = dbc.Modal(children=[
    dbc.ModalHeader(
        dbc.ModalTitle(children=[
            html.I(className="bi bi-person-bounding-box me-2"),
            "Login"
        ])
    ),
    dbc.ModalBody(children=[
        # Username input, e.g., "username" or "firstname"
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-person")  # Alternatives: bi-person-badge, bi-at
            ),
            dbc.FormFloating(
                [
                    dbc.Input(
                        id='username-input',
                        type='text',
                        placeholder="Username",
                        persistence=True,
                        n_submit=0,
                        n_submit_timestamp=-1
                    ),
                    dbc.Label("Username", html_for="username-input"),
                ]),
        ], className="mb-3"),
        # Password input, e.g., "<PASSWORD>" or "<PASSWORD>"
        dbc.InputGroup(children=[
            dbc.InputGroupText(
                html.I(className="bi bi-key")  # Alternatives: bi-lock, bi-shield-lock
            ),
            dbc.FormFloating(
                [
                    dbc.Input(
                        id='password-input',
                        type='password',
                        placeholder="Password",
                        n_submit=0,
                        n_submit_timestamp=-1
                    ),
                    dbc.Label("Password", html_for="password-input"),
                ]),
        ]),
        # Messages placeholders
        html.Div(children=[
            dbc.Alert("Try to log-in first...", color="info")
        ], id='login-attempt-message', style={'display': 'none'}),
    ]),
    dbc.ModalFooter(
        children=[
            new_user_button,
            # Login button
            dbc.Button(
                children=[
                    html.I(className="bi bi-box-arrow-right me-2"),  # Alternative: bi-check2-circle
                    'Login'
                ],
                id='login-button',
                n_clicks=0,
                disabled=False,
                className="me-2"
            ),
            # Logout button
            dbc.Button(
                children=[
                    html.I(className="bi bi-box-arrow-left me-2"),  # Alternative: bi-door-open
                    'Logout'
                ],
                id='logout-button',
                n_clicks=0,
                disabled=True,
                className="me-2"
            )
        ])
], id='login-modal', is_open=True)


# Callback to toggle login modal visibility
@callback(Output("login-modal", "is_open", allow_duplicate=True),
          Input('login-avatar-button', 'n_clicks'),
          State('login-modal', 'is_open'),
          prevent_initial_call=True)
def toggle_login_modal(_, is_open):
    return not is_open

@callback(
    Output('username-input', 'valid'),
    Output('username-input', 'invalid'),
    Input('username-input', 'value'),
    State('login-modal', 'is_open'),
    State('rest-api-host', 'data'),
    State('rest-api-port', 'data')
)
def validate_username(username, is_modal_open, host, port):
    if not is_modal_open or not username:
        return False, False
    # Make request to the login API endpoint
    try:
        response = requests.get(urljoin(base_url(host, port), f'/login?username={username}'))
        user_exists = response.json().get('exists', False)
        if user_exists:
            return True, False  # Valid username
        else:
            return False, True  # Invalid username
    except Exception as e:
        return False, True

# Handle login form submission and authentication
@callback(Output('logged-username', 'data'),
          Output('logged-fullname', 'data'),
          Output('login-attempt-message', 'style'),
          Output('login-attempt-message', 'children'),
          Input('username-input', 'n_submit'),
          Input('password-input', 'n_submit'),
          Input('login-button', 'n_clicks'),
          State('username-input', 'value'),
          State('password-input', 'value'),
          State('rest-api-host', 'data'),
          State('rest-api-port', 'data'),
          prevent_initial_call=True)
def login(username_submit, password_submit, n_clicks, username, password, host, port):
    """Callback handling user login functionality.

    Parameters
    ----------
    n_clicks : int
        The number of times the login button has been clicked. Used to trigger
        the function upon a button press.
    username : str
        The username input provided by the user attempting to log in.
    password : str
        The password input provided by the user attempting to log in.

    Returns
    -------
    str
        The username of the logged-in user if login is successful, or ``None`` if the login fails.
    bool
        A flag indicating whether the success modal should be opened (``True`` for success, ``False`` otherwise).
    bool
        A flag indicating whether the error modal should be opened (``True`` for failure, ``False`` otherwise).
    """
    message_style = {'display': 'block', 'margin-top': '10px'}

    try:
        # Send login request to REST API endpoint
        response = requests.post(
            urljoin(base_url(host, port), '/login'),
            data=json.dumps({'username': username, 'password': password}),
            headers={'Content-Type': 'application/json'}
        )

        if response.ok:
            # Parse successful response
            loggin_attempt = response.json()
            is_logged_in = loggin_attempt['authenticated']
            fullname = loggin_attempt['fullname']
            login_msg = loggin_attempt['message']
            if is_logged_in:
                # Setup success message display
                alert = dbc.Alert(login_msg, color="success")
                return username, fullname, message_style, alert

        # Handle failed login attempts
        error_msg = "Login failed. Please check your credentials."
        if response.text:
            try:
                # Attempt to extract error message from response
                error_data = response.json()
                if 'message' in error_data:
                    error_msg = error_data['message']
            except json.JSONDecodeError:
                # Use raw response text if JSON parsing fails
                error_msg = response.text

        alert = dbc.Alert(error_msg, color="danger")
        return None, None, message_style, alert

    except requests.exceptions.RequestException as e:
        # Handle connection errors (network issues, server down, etc.)
        alert = dbc.Alert(f"Connection error: {str(e)}", color="danger")
        return None, None, message_style, alert


@callback(
    Output("login-avatar-button", "children"),
    Input("logged-fullname", "data")
)
def update_login_avatar_button(fullname):
    if fullname:
        return create_login_button(
            is_logged_in=True,
            user_fullname=fullname
        ).children
    return create_login_button(is_logged_in=False).children


# Manage modal dialogs timing and visibility
@callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    Input("logged-username", "data"),
    prevent_initial_call=True
)
def timeout_modal(username):
    # Auto-close modals after 2 seconds
    if username:

        time.sleep(1)
        return False
    else:
        return True


# Reset login button clicks on logout
@callback(
    Output('login-avatar-button', 'n_clicks'),
    Output('logged-username', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout(_):
    """Callback handling the logout functionality.

    Parameters
    ----------
    _ : int
        Placeholder for the click event of the 'logout-button' (unused).

    Returns
    -------
    int
        The reset value of the 'n_clicks' property for the 'login-button', which is always `0`.
    """
    return 0, None
