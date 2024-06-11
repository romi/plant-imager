#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import html

# Local storage for users
USERS_DB = {
    'admin': {'password': 'password', 'fullname': "Indiana Jones"},
    'agent007': {'password': 'user007', 'fullname': "James Bond"},
    'batman': {'password': 'joker', 'fullname': "Bruce Wayne"},
}

login_modal = html.Div([
    dbc.Modal(id='login-modal', children=[
        dbc.ModalHeader(dbc.ModalTitle("Login")),
        dbc.ModalBody(children=[
            html.Div(children=[
                dbc.Label('Username'),
                dbc.Input(id='username', type='text', placeholder="Enter username", persistence=True)
            ]),
            html.Div(children=[
                dbc.Label('Password'),
                dbc.Input(id='password', type='password', placeholder="Enter password")
            ]),
        ]
        ),
        dbc.ModalFooter(children=[
            dbc.Button('Login', id='login-button', n_clicks=0),
            dbc.Button('Logout', id='logout-button', n_clicks=0),
        ]
        )
    ]),
])

error_modal = html.Div([
    dbc.Modal(id='error-modal', children=[
        dbc.ModalHeader(dbc.ModalTitle("Error")),
        dbc.ModalBody(children=[
            html.Div(children="Wrong login or password!")
        ])
    ])
])

success_modal = html.Div([
    dbc.Modal(id='success-modal', children=[
        dbc.ModalHeader(dbc.ModalTitle("Success")),
        dbc.ModalBody(children=[
            html.Div(children="Welcome!")
        ])
    ])
])
