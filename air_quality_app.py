import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os

# Disable Flask's dotenv loading
os.environ["FLASK_SKIP_DOTENV"] = "1"


class AirQualityDashboard:
    def __init__(self):
        self.poor_air_threshold = 100
        self.load_and_process_data()
        self.initialize_app()

    def load_and_process_data(self):
        # Load Data
        self.ozone_df = pd.read_csv("laOzone.csv")
        self.pm25_df = pd.read_csv("laPMTwoFive.csv")

        # Convert 'Date' to datetime
        for df in [self.ozone_df, self.pm25_df]:
            df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")

        # Process time series data
        self.process_time_series_data()
        # Get latest data
        self.process_latest_data()

    def process_time_series_data(self):
        # Calculate daily averages for both pollutants
        self.ozone_daily = self.ozone_df.groupby('Date')['Daily AQI Value'].mean().reset_index()
        self.pm25_daily = self.pm25_df.groupby('Date')['Daily AQI Value'].mean().reset_index()

    def process_latest_data(self):
        # Filter latest air quality data
        self.ozone_latest = self.ozone_df[self.ozone_df["Date"] == self.ozone_df["Date"].max()]
        self.pm25_latest = self.pm25_df[self.pm25_df["Date"] == self.pm25_df["Date"].max()]

    def initialize_app(self):
        self.app = Dash(__name__)

        self.app.layout = html.Div([
            # Title
            html.Div([
                html.H1("Los Angeles County Air Quality Dashboard",
                        style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.P("Monitor air quality trends and current conditions across LA County.",
                       style={'textAlign': 'center', 'color': '#7f8c8d'}),
            ], style={'margin': '20px'}),

            # Map and Time Series Container
            html.Div([
                # Left Column - Map
                html.Div([
                    html.H3("Current Air Quality Map", style={'textAlign': 'center'}),
                    dcc.Checklist(
                        id="layer-selector",
                        options=[
                            {"label": " Ozone ", "value": "ozone"},
                            {"label": " PM2.5 ", "value": "pm25"}
                        ],
                        value=["ozone", "pm25"],
                        inline=True,
                        style={'textAlign': 'center', 'margin': '10px'}
                    ),
                    dcc.Graph(
                        id="air-quality-map",
                        style={'height': '45vh'}
                    ),
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),

                # Right Column - Time Series
                html.Div([
                    html.H3("Historical Air Quality Trends", style={'textAlign': 'center'}),
                    dcc.Graph(
                        id="time-series-graph",
                        style={'height': '45vh'}
                    ),
                ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top', 'marginLeft': '4%'}),
            ]),

            # Statistics Section
            html.Div([
                html.H4("Current Air Quality Statistics", style={'textAlign': 'center'}),
                html.Div(id="statistics-output", style={'textAlign': 'center'})
            ], style={'margin': '20px'})
        ])

        self.setup_callbacks()

    def setup_callbacks(self):
        @self.app.callback(
            [Output("air-quality-map", "figure"),
             Output("time-series-graph", "figure"),
             Output("statistics-output", "children")],
            Input("layer-selector", "value")
        )
        def update_dashboard(selected_layers):
            # Create map
            map_fig = px.scatter_mapbox(
                lat=[34.05],
                lon=[-118.25],
                zoom=9
            )

            # Initialize statistics text
            stats_text = []

            # Calculate colorbar positions
            colorbar_x_positions = {
                "ozone": 1.02,
                "pm25": 1.12
            }

            # Add layers and collect statistics
            for layer, color_scale in [("ozone", "Reds"), ("pm25", "Blues")]:
                if layer in selected_layers:
                    df = self.ozone_latest if layer == "ozone" else self.pm25_latest

                    map_fig.add_scattermapbox(
                        lat=df["Site Latitude"],
                        lon=df["Site Longitude"],
                        mode='markers',
                        marker=dict(
                            size=12,
                            color=df["Daily AQI Value"],
                            colorscale=color_scale,
                            showscale=True,
                            colorbar=dict(
                                title=f"{layer.upper()} AQI",
                                x=colorbar_x_positions[layer],
                                len=0.75,
                                y=0.5,
                                yanchor='middle'
                            )
                        ),
                        text=df.apply(
                            lambda row: f"{row['Local Site Name']}<br>AQI: {row['Daily AQI Value']:.1f}",
                            axis=1
                        ),
                        hoverinfo='text',
                        name=layer.upper(),
                    )

                    # Add statistics
                    poor_air_count = len(df[df["Daily AQI Value"] > self.poor_air_threshold])
                    total_count = len(df)
                    stats_text.append(
                        html.P(
                            f"{layer.upper()}: {poor_air_count} out of {total_count} sites show poor air quality (AQI > {self.poor_air_threshold})")
                    )

            # Update map layout
            map_fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=dict(lat=34.05, lon=-118.25),
                    zoom=9
                ),
                margin=dict(r=100, t=0, l=0, b=0),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255, 255, 255, 0.8)"
                )
            )

            # Create time series plot
            time_series_fig = go.Figure()

            if "ozone" in selected_layers:
                time_series_fig.add_trace(go.Scatter(
                    x=self.ozone_daily["Date"],
                    y=self.ozone_daily["Daily AQI Value"],
                    name="Ozone",
                    line=dict(color="red")
                ))

            if "pm25" in selected_layers:
                time_series_fig.add_trace(go.Scatter(
                    x=self.pm25_daily["Date"],
                    y=self.pm25_daily["Daily AQI Value"],
                    name="PM2.5",
                    line=dict(color="blue")
                ))

            time_series_fig.update_layout(
                title="Average Daily AQI Values",
                xaxis_title="Date",
                yaxis_title="AQI Value",
                hovermode='x unified',
                margin=dict(l=60, r=30, t=50, b=40),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99,
                    bgcolor="rgba(255, 255, 255, 0.8)"
                )
            )

            # Add threshold line
            time_series_fig.add_hline(
                y=self.poor_air_threshold,
                line_dash="dash",
                line_color="red",
                opacity=0.5,
                annotation_text="Poor Air Quality Threshold"
            )

            return map_fig, time_series_fig, stats_text

    def run_server(self, debug=True):
        self.app.run_server(debug=debug)


if __name__ == "__main__":
    dashboard = AirQualityDashboard()
    dashboard.run_server(debug=True)