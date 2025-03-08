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


def create_avatar(fullname):
    """Create an avatar with user's initials in a colored circle.

    Generates a circular avatar component containing the initials of a user's full name
    with a background color uniquely derived from the name using MD5 hashing.

    Parameters
    ----------
    fullname : str
        The full name of the user. Can contain multiple names separated by spaces.

    Returns
    -------
    dash.html.Div or None
        A Dash HTML Div component containing the user's initials with styled
        background, or ``None`` if fullname is empty.

    Notes
    -----
    - Background color is deterministically generated from the fullname using MD5 hash
    - Avatar is rendered as a 35x35px circle with centered text
    - Initials are automatically capitalized
    - Multiple word names will use the first letter of each word
    """
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
    """Create a login/logout button with avatar for the navigation bar.

    This function generates a navigation link component that displays either a default
    person icon (when logged out) or a user avatar (when logged in). The avatar is
    created using the user's full name initials.

    Parameters
    ----------
    is_logged_in : bool, optional
        Flag indicating whether a user is currently logged in.
        Default is ``False``.
    user_fullname : str or None, optional
        The full name of the logged-in user. Used to create the avatar display.
        Default is ``None``.

    Returns
    -------
    dash_bootstrap_components.NavLink
        A Bootstrap NavLink component containing either:
        - A user avatar (when logged in)
        - A default person icon (when logged out)

    See Also
    --------
    create_avatar : Function used to generate the user avatar display
    """
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


def login_title(fullname=None, username=None):
    icon = html.I(className="bi bi-person-bounding-box me-2")
    if fullname:
        return [f"{fullname} (@{username})"]
    else:
        return [icon, "Login"]


login_modal = dbc.Modal(children=[
    dbc.ModalHeader(
        dbc.ModalTitle(id='login-modal-title')
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
        ], id='username-input-group', className="mb-3"),
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
        ], id='password-input-group'),
        # Messages placeholders
        html.Div(children=[
            dbc.Alert("Try to log-in first...", color="info", class_name="mb-0")
        ], id='login-attempt-message', style={'display': 'none'}, className="mt-3"),
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
                class_name="me-2"
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
                class_name="me-2"
            )
        ])
], id='login-modal', is_open=True)


@callback(Output("login-modal", "is_open", allow_duplicate=True),
          Input('login-avatar-button', 'n_clicks'),
          State('login-modal', 'is_open'),
          prevent_initial_call=True)
def toggle_login_modal(_, is_open):
    """Toggle the visibility of the login modal.

    This callback function controls the visibility of the login modal when the login avatar button is clicked.

    Parameters
    ----------
    _ : int
        Number of clicks on the login avatar button (unused parameter)
    is_open : bool
        Current state of the login modal visibility

    Returns
    -------
    bool
        ``True`` to open the modal, ``False`` otherwise

    Notes
    -----
    The function only handles opening the modal. Closing is handled by other modal mechanisms
    """
    if not is_open:
        return True
    return False


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


@callback(Output('logged-username', 'data', allow_duplicate=True),
          Output('logged-fullname', 'data', allow_duplicate=True),
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
    """Handle user authentication through the REST API.

    This callback function processes login attempts by sending credentials to a REST API endpoint
    and handling the response appropriately. It manages both successful and failed login attempts,
    including various error conditions.

    Parameters
    ----------
    username_submit : int or None
        Number of times the username input has been submitted via Enter key.
    password_submit : int or None
        Number of times the password input has been submitted via Enter key.
    n_clicks : int or None
        Number of times the login button has been clicked.
    username : str
        Username entered in the login form.
    password : str
        Password entered in the login form.
    host : str
        REST API host address.
    port : int
        REST API port number.

    Returns
    -------
    str or None
        The authenticated username if login successful, None otherwise.
    str or None
        The user's full name if login successful, None otherwise.
    dict
        CSS style dictionary for the message display.
    dash_bootstrap_components.Alert
        Bootstrap alert component containing success or error message.

    Raises
    ------
    requests.exceptions.RequestException
        If there are network connectivity issues or server communication problems.
    json.JSONDecodeError
        If the server response cannot be parsed as JSON.

    Notes
    -----
    Authentication state is maintained through Dash Store components in the application layout.
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
                alert = dbc.Alert(login_msg, color="success", class_name="mb-0")
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

        alert = dbc.Alert(error_msg, color="danger", class_name="mb-0")
        return None, None, message_style, alert

    except requests.exceptions.RequestException as e:
        # Handle connection errors (network issues, server down, etc.)
        alert = dbc.Alert(f"Connection error: {str(e)}", color="danger", class_name="mb-0")
        return None, None, message_style, alert


@callback(
    Output("login-avatar-button", "children"),
    Input("logged-fullname", "data")
)
def update_login_avatar_button(fullname):
    """Update the login avatar button display based on user login status.

    This callback function modifies the login button appearance in the navigation bar
    to reflect whether a user is logged in or not. When logged in, it displays the
    user's full name; when logged out, it shows the default login button.

    Parameters
    ----------
    fullname : str or None
        The full name of the logged-in user. None if no user is logged in.

    Returns
    -------
    list
        A list of Dash components representing the children of the login button.
        The content varies based on login status.

    See Also
    --------
    create_login_button : The underlying function that creates the button components
    """
    if fullname:
        return create_login_button(
            is_logged_in=True,
            user_fullname=fullname
        ).children
    return create_login_button(is_logged_in=False).children


@callback(
    Output("login-modal-title", "children"),
    Input("logged-fullname", "data"),
    Input("logged-username", "data"),
)
def update_login_modal_title(fullname, username):
    """Updates the title of the login modal window dynamically based on the logged-in
    user's information. If the logged-in user's full name is available, it uses the
    provided full name and username to generate the title. Otherwise, it defaults
    to a generic title.

    Parameters
    ----------
    fullname : str or None
        The full name of the logged-in user.
        If ``None``, the default title is used instead.
    username : str or None
        The username of the logged-in user.
        Used in combination with the full name to generate the title.
        If ``None``, the default title is used.

    Returns
    -------
    str
        The dynamically generated title for the login modal window. This either
        includes the logged-in user's full name and username or a default message
        if no user information is provided.
    """
    if fullname:
        return login_title(fullname, username)
    return login_title()


@callback(
    Output("username-input-group", "style", allow_duplicate=True),
    Output("password-input-group", "style", allow_duplicate=True),
    Output("login-attempt-message", "children", allow_duplicate=True),
    Input("logged-fullname", "data"),
    prevent_initial_call=True,
)
def update_login_modal_body(fullname):
    """Update the visibility of login modal components based on login status.

    This callback controls the display of username and password input groups in the login modal,
    as well as any login attempt messages, based on whether a user is logged in.

    Parameters
    ----------
    fullname : str or None
        The full name of the logged-in user. ``None`` if no user is logged in.

    Returns
    -------
    dict
        Style dictionary for username-input-group component
    dict
        Style dictionary for password-input-group component
    str
        Login-attempt-message component (empty string in this case)

    Examples
    --------
    >>> update_login_modal_body(None)
    ({'display': 'flex'}, {'display': 'flex'}, "")
    >>> update_login_modal_body("John Doe")
    ({'display': 'none'}, {'display': 'none'}, "")
    """
    if not fullname:
        return {'display': 'flex'}, {'display': 'flex'}, ""
    return {'display': 'none'}, {'display': 'none'}, ""


@callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    Input("logged-username", "data"),
    prevent_initial_call=True,
)
def timeout_modal(username):
    """Control the visibility of the login-modal with a timeout.

    This callback automatically closes the login-modal after a 1-second delay
    when a user successfully logs in.

    Parameters
    ----------
    username : str or None
        The username of the logged-in user. None if no user is logged in.

    Returns
    -------
    bool
        ``False`` if a user is logged in (closes modal), ``True`` otherwise (keeps modal open)

    Notes
    -----
    The function includes a 1-second sleep delay to provide time for the logout callback to unset the username.
    """
    time.sleep(1)
    if username:
        return False  # close the login modal
    else:
        return True  # keep the login modal open


@callback(
    Output('logged-username', 'data', allow_duplicate=True),
    Output('logged-fullname', 'data', allow_duplicate=True),
    Output("login-attempt-message", "children", allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout(_):
    """Handle user logout functionality.

    This callback clears the user session data when the logout button is clicked.

    Parameters
    ----------
    _ : int
        Placeholder for the click event of the 'logout-button' (unused).

    Returns
    -------
    None
        Clears the logged username.
    None
        Clears the logged full name.
    str
        Empty string for login attempt message.
    """
    return None, None, ""


@callback(
    Output("logout-button", "disabled"),
    Input("logged-username", "data"),

)
def disable_logout_button(username):
    """Control the enabled/disabled state of the logout button.

    This callback toggles the disabled state of the logout button based on whether
    a user is currently logged in.

    Parameters
    ----------
    username : str or None
        The username of the logged-in user. ``None`` if no user is logged in.

    Returns
    -------
    bool
        ``True`` if the logout button should be disabled (no user logged in),
        ``False`` if the button should be enabled (user is logged in).
    """
    if username:
        return False
    return True
