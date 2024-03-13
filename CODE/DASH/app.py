# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 11:26:23 2024

@author: PC
"""
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os


regime_dat =  pd.read_csv( os.path.join('regime_data.csv') )
#regime_dat = pd.read_csv("C:/Users/PC/Documents/Github/Diamond/DATA/SHINY/regime_data.csv")

regime_colors = {
    "DISINFLATION": "rgb(85, 107, 47)",
    "FIRE": "rgb(178, 34, 34)",
    "ICE": 'rgb(162, 181, 205)',
    "REFLATION": "rgb(255, 222, 173)",
    'BOOM': "rgb(178, 34, 34)",
    'SLUMP': "rgb(85, 107, 47)",
    'RECESSION': "rgb(162, 181, 205)",
    'RECOVERY': "rgb(255, 222, 173)",
    'INVERTED': "rgb(178, 34, 34)",
    'BULL_STEEP': "rgb(85, 107, 47)",
    'BEAR_FLAT': "rgb(162, 181, 205)",
    'BULL_FLAT': "rgb(232, 216, 137)",
    'BEAR_STEEP': "rgb(235, 172, 63)",
    'Contango': "rgb(85, 107, 47)",
    'Backwardation': "rgb(178, 34, 34)"
}
app = Dash(__name__)
server = app.server



app.layout = html.Div([
    html.H1(children='Title of Dash App1', style={'textAlign':'center'}),
    dcc.Dropdown(regime_dat.Country.unique(), 'US', id='dropdown-selection-country'),
    dcc.Dropdown(regime_dat.Field.unique(), 'INF_YOY', id='dropdown-selection-field'),
    dcc.Graph(id='graph-content')
])


@callback(
    Output('graph-content', 'figure'),
    [Input('dropdown-selection-field', 'value'),
    Input('dropdown-selection-country', 'value')]
)
def update_graph(field,country):
    dff = regime_dat[(regime_dat.Field==field) & (regime_dat.Country==country)]
    dff = dff[["Date","Value","Regime"]].dropna().reset_index(drop=True)
    fig= px.line(dff, x="Date", y="Value")
    fig.update_traces(line_color='#000000')

    ply_shapes = {}
    for i in range(1, len(dff)):
        ply_shapes['shape_' + str(i)]=go.layout.Shape(type="rect",
                                                        x0=dff.Date[i-1], x1=dff.Date[i],y0=dff.Value.max(),y1=dff.Value.min(),
                                                        fillcolor=regime_colors[dff["Regime"][i]].replace('rgb', 'rgba').rstrip(')') + ',0.6)',
                                                        layer="below", line_width=0.5,
                                                        line_color=regime_colors[dff["Regime"][i]].replace('rgb', 'rgba').rstrip(')') + ',0.1)'
                                                    )
    lst_shapes=list(ply_shapes.values())
    fig.update_layout(shapes=lst_shapes)
    
    fig.update_layout(
        title="Value Over Time by Regime",
        xaxis_title="Date",
        yaxis_title="Value",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True, use_reloader=False)