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

        # Get latest data
        self.process_latest_data()

    def process_latest_data(self):
        # Filter latest air quality data
        self.ozone_latest = self.ozone_df[self.ozone_df["Date"] == self.ozone_df["Date"].max()]
        self.pm25_latest = self.pm25_df[self.pm25_df["Date"] == self.pm25_df["Date"].max()]

    def initialize_app(self):
        self.app = Dash(__name__)

        self.app.layout = html.Div([
            # Title (smaller size)
            html.Div([
                html.H2("LA County Air Quality Dashboard", style={'textAlign': 'center', 'color': '#2c3e50', 'fontFamily': 'Arial'}),
                html.P("Monitor air quality trends and current conditions across LA County.",
                       style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '14px', 'fontFamily': 'Arial'}),
            ], style={'margin': '10px'}),

            # Map Section (Now on top)
            html.Div([
                html.H4("Current Air Quality Map", style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '22px', 'fontFamily': 'Arial'}),
                dcc.Checklist(
                    id="layer-selector",
                    options=[
                        {"label": " Ozone ", "value": "ozone"},
                        {"label": " PM2.5 ", "value": "pm25"}
                    ],
                    value=["ozone", "pm25"],
                    inline=True,
                    style={'textAlign': 'center', 'marginBottom': '10px', 'fontFamily': 'Arial'}
                ),
                dcc.Graph(
                    id="air-quality-map",
                    style={'height': '50vh'}
                ),
            ], style={'marginBottom': '40px'}),  # Increased spacing

            # Month Selector
            html.Div([
                html.H4("Select a Month for Historical Trends", style={'textAlign': 'center', 'marginBottom': '10px', 'fontSize': '22px', 'fontFamily': 'Arial'}),
                dcc.Dropdown(
                    id="month-selector",
                    options=[
                        {"label": date.strftime("%B %Y"), "value": date.strftime("%Y-%m")}
                        for date in sorted(self.ozone_df["Date"].dt.to_period("M").unique())
                    ],
                    value=self.ozone_df["Date"].max().strftime("%Y-%m"),  # Default to latest month
                    clearable=False,
                    style={'width': '50%', 'margin': 'auto', 'fontFamily': 'Arial'}
                )
            ], style={'marginBottom': '40px'}),  # Increased spacing

            # Historical Trends (Now below the map)
            html.Div([
                html.H4("Historical Air Quality Trends by Location", style={'textAlign': 'center', 'fontSize': '22px', 'fontFamily': 'Arial'}),
                dcc.Graph(
                    id="time-series-graph",
                    style={'height': '50vh'}
                ),
            ], style={'marginBottom': '50px'}),  # Increased spacing

            # Statistics Section
            html.Div([
                html.H4("Current Air Quality Statistics", style={'textAlign': 'center', 'fontSize': '22px', 'fontFamily': 'Arial'}),
                html.Div(id="statistics-output", style={'textAlign': 'center', 'fontFamily': 'Arial'})
            ], style={'margin': '20px'})
        ])

        self.setup_callbacks()

    def setup_callbacks(self):
        @self.app.callback(
            [Output("air-quality-map", "figure"),
             Output("time-series-graph", "figure"),
             Output("statistics-output", "children")],
            [Input("layer-selector", "value"),
             Input("month-selector", "value")]
        )
        def update_dashboard(selected_layers, selected_month):
            selected_month = pd.to_datetime(selected_month)  # Convert to datetime

            # Filter data by selected month for both map and trends
            filtered_ozone = self.ozone_df[self.ozone_df["Date"].dt.to_period("M") == selected_month.to_period("M")]
            filtered_pm25 = self.pm25_df[self.pm25_df["Date"].dt.to_period("M") == selected_month.to_period("M")]

            # Create map figure
            map_fig = px.scatter_mapbox(
                lat=[34.05],
                lon=[-118.25],
                zoom=9
            )

            # Initialize statistics text
            stats_text = []

            # Colorbar positions
            colorbar_x_positions = {"ozone": 1.12, "pm25": 1.22}

            # Add layers and collect statistics
            for layer, color_scale, df in [
                ("ozone", "Reds", filtered_ozone),
                ("pm25", "Blues", filtered_pm25)
            ]:
                if layer in selected_layers:
                    map_fig.add_scattermapbox(
                        lat=df["Site Latitude"],
                        lon=df["Site Longitude"],
                        mode='markers',
                        marker=dict(
                            size=12,
                            color=df["Daily AQI Value"],
                            colorscale=color_scale,
                            opacity=0.7,
                            showscale=True,
                            colorbar=dict(
                                title=f"{layer.upper()} AQI",
                                x=colorbar_x_positions[layer],
                                len=0.75
                            )
                        ),
                        text=df.apply(lambda row: f"{row['Local Site Name']}<br>AQI: {row['Daily AQI Value']:.1f}", axis=1),
                        hoverinfo='text',
                        name=layer.upper(),
                    )

                    # Add statistics
                    poor_air_count = len(df[df["Daily AQI Value"] > self.poor_air_threshold])
                    total_count = len(df)
                    stats_text.append(
                        html.P(
                            f"{layer.upper()}: {poor_air_count} out of {total_count} sites show poor air quality (AQI > {self.poor_air_threshold})"
                        )
                    )

            # Update map layout
            map_fig.update_layout(
                font=dict(family="Arial"),
                mapbox=dict(
                    style="carto-positron",
                    center=dict(lat=34.05, lon=-118.25),
                    zoom=9
                ),
                margin=dict(r=100, t=0, l=0, b=0),
                showlegend=True,
                annotations=[
                    dict(
                        text="Click to toggle view",
                        x=1, y=1.05,  # Position at the top of the legend
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=14, family="Arial", color="black")
                    )
                ]
            )

            # Create time series plot
            time_series_fig = go.Figure()

            for site_name in filtered_ozone["Local Site Name"].unique():
                site_data = filtered_ozone[filtered_ozone["Local Site Name"] == site_name]
                time_series_fig.add_trace(go.Scatter(
                    x=site_data["Date"],
                    y=site_data["Daily AQI Value"],
                    name=f"Ozone - {site_name}"
                ))

            for site_name in filtered_pm25["Local Site Name"].unique():
                site_data = filtered_pm25[filtered_pm25["Local Site Name"] == site_name]
                time_series_fig.add_trace(go.Scatter(
                    x=site_data["Date"],
                    y=site_data["Daily AQI Value"],
                    name=f"PM2.5 - {site_name}"
                ))

            # Update time series layout
            time_series_fig.update_layout(
                font=dict(family="Arial"),
                title=dict(text="Daily AQI Trends by Site", font_size=22),
                xaxis_title="Date",
                yaxis_title="AQI Value",
                showlegend=True,
                annotations=[
                    dict(
                        text="Click to toggle view",
                        x=1, y=1.05,  # Position at the top of the legend
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=14, family="Arial", color="black")
                    )
                ]
            )

            return map_fig, time_series_fig, stats_text

    def run_server(self, debug=True):
        self.app.run_server(debug=debug)


if __name__ == "__main__":
    dashboard = AirQualityDashboard()
    dashboard.run_server(debug=True)
