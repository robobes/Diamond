# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 12:17:23 2024

@author: PC
"""
import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('This is our Home page'),
    html.Div('This is our Home page content.'),
])