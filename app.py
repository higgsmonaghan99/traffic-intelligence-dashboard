
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# -----------------------------
# Data loading and preparation
# -----------------------------
DATA_PATH = "traffic_clean.csv"

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_MAP = {m: i + 1 for i, m in enumerate(MONTH_ORDER)}

df = pd.read_csv(DATA_PATH)
df.columns = [c.strip().lower() for c in df.columns]

df["traffic"] = (
    df["traffic"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.strip()
)
df["traffic"] = pd.to_numeric(df["traffic"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["month"] = df["month"].astype(str).str.strip().str.title()
df["facility"] = df["facility"].astype(str).str.strip()

df = df.dropna(subset=["traffic", "year", "month", "facility"]).copy()
df["month_no"] = df["month"].map(MONTH_MAP)
df["month"] = pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)
df["year_month"] = pd.to_datetime(
    df["year"].astype(int).astype(str) + "-" + df["month_no"].astype(int).astype(str).str.zfill(2) + "-01"
)

available_years = sorted(df["year"].dropna().astype(int).unique().tolist())
available_facilities = sorted(df["facility"].unique().tolist())

# -----------------------------
# App setup
# -----------------------------
app = Dash(__name__)
server = app.server
app.title = "Traffic Intelligence Dashboard"

def metric_card(title: str, value_id: str, subtitle: str):
    return html.Div(
        [
            html.Div(title, className="metric-title"),
            html.Div(id=value_id, className="metric-value"),
            html.Div(subtitle, className="metric-subtitle"),
        ],
        className="metric-card",
    )

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="hero",
            children=[
                html.Div(
                    [
                        html.Div("Traffic Intelligence Dashboard", className="hero-title"),
                        html.Div(
                            "Interactive BI-style dashboard for facility traffic analysis. "
                            "Built with Dash for portfolio, GitHub, and presentation use.",
                            className="hero-subtitle",
                        ),
                    ]
                ),
            ],
        ),

        html.Div(
            className="filters-panel",
            children=[
                html.Div(
                    [
                        html.Label("Select Year Range", className="filter-label"),
                        dcc.RangeSlider(
                            id="year-range",
                            min=min(available_years),
                            max=max(available_years),
                            value=[min(available_years), max(available_years)],
                            marks={year: str(year) for year in available_years},
                            step=1,
                            allowCross=False,
                            tooltip={"placement": "bottom", "always_visible": False},
                        ),
                    ],
                    className="filter-block full-width",
                ),
                html.Div(
                    [
                        html.Label("Facility", className="filter-label"),
                        dcc.Dropdown(
                            id="facility-dropdown",
                            options=[{"label": f, "value": f} for f in available_facilities],
                            value=available_facilities,
                            multi=True,
                            placeholder="Select facility",
                            className="dash-dropdown",
                        ),
                    ],
                    className="filter-block",
                ),
                html.Div(
                    [
                        html.Label("Month", className="filter-label"),
                        dcc.Dropdown(
                            id="month-dropdown",
                            options=[{"label": m, "value": m} for m in MONTH_ORDER],
                            value=MONTH_ORDER,
                            multi=True,
                            placeholder="Select month",
                            className="dash-dropdown",
                        ),
                    ],
                    className="filter-block",
                ),
                html.Div(
                    className="button-row",
                    children=[
                        html.Button("Select All Facilities", id="all-facilities-btn", n_clicks=0, className="btn"),
                        html.Button("Select All Months", id="all-months-btn", n_clicks=0, className="btn btn-secondary"),
                    ],
                ),
                html.Div(id="selection-summary", className="selection-summary"),
            ],
        ),

        html.Div(
            className="metrics-grid",
            children=[
                metric_card("Total Traffic", "total-traffic", "Sum of filtered traffic"),
                metric_card("Average Monthly Traffic", "avg-traffic", "Mean traffic per record"),
                metric_card("Peak Facility", "top-facility", "Highest traffic in current view"),
                metric_card("Records", "total-records", "Filtered observations"),
            ],
        ),

        html.Div(
            className="charts-grid two-col",
            children=[
                html.Div(
                    className="chart-card",
                    children=[
                        html.Div("Traffic Trend Over Time", className="chart-title"),
                        dcc.Graph(id="trend-chart", config={"displayModeBar": False}),
                    ],
                ),
                html.Div(
                    className="chart-card",
                    children=[
                        html.Div("Traffic by Facility", className="chart-title"),
                        dcc.Graph(id="bar-chart", config={"displayModeBar": False}),
                    ],
                ),
            ],
        ),

        html.Div(
            className="charts-grid two-col",
            children=[
                html.Div(
                    className="chart-card",
                    children=[
                        html.Div("Facility Share", className="chart-title"),
                        dcc.Graph(id="pie-chart", config={"displayModeBar": False}),
                    ],
                ),
                html.Div(
                    className="chart-card",
                    children=[
                        html.Div("Monthly Seasonality", className="chart-title"),
                        dcc.Graph(id="month-chart", config={"displayModeBar": False}),
                    ],
                ),
            ],
        ),

        html.Div(
            className="footer-note",
            children="Tip: Use multiple facilities and months together to compare seasonality, facility mix, and long-term trend shifts.",
        ),
    ],
)

# -----------------------------
# Helpers
# -----------------------------
def format_number(x):
    try:
        return f"{int(round(x)):,}"
    except Exception:
        return "-"

def filtered_frame(year_range, facilities, months):
    dff = df.copy()
    dff = dff[(dff["year"] >= year_range[0]) & (dff["year"] <= year_range[1])]
    if facilities:
        dff = dff[dff["facility"].isin(facilities)]
    if months:
        dff = dff[dff["month"].isin(months)]
    return dff

def empty_figure(title):
    fig = px.scatter(title=title)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="#e5e7eb"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text="No data available for current filter selection",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=16)
            )
        ],
    )
    return fig

# -----------------------------
# Button callbacks
# -----------------------------
@app.callback(
    Output("facility-dropdown", "value"),
    Input("all-facilities-btn", "n_clicks"),
    prevent_initial_call=True,
)
def select_all_facilities(_):
    return available_facilities

@app.callback(
    Output("month-dropdown", "value"),
    Input("all-months-btn", "n_clicks"),
    prevent_initial_call=True,
)
def select_all_months(_):
    return MONTH_ORDER

# -----------------------------
# Main dashboard callback
# -----------------------------
@app.callback(
    Output("total-traffic", "children"),
    Output("avg-traffic", "children"),
    Output("top-facility", "children"),
    Output("total-records", "children"),
    Output("selection-summary", "children"),
    Output("trend-chart", "figure"),
    Output("bar-chart", "figure"),
    Output("pie-chart", "figure"),
    Output("month-chart", "figure"),
    Input("year-range", "value"),
    Input("facility-dropdown", "value"),
    Input("month-dropdown", "value"),
)
def update_dashboard(year_range, facilities, months):
    facilities = facilities or []
    months = months or []
    dff = filtered_frame(year_range, facilities, months)

    if dff.empty:
        empty = empty_figure("No Data")
        return "-", "-", "-", "0", "No selections available.", empty, empty, empty, empty

    total_traffic_value = dff["traffic"].sum()
    avg_traffic_value = dff["traffic"].mean()
    top_facility_series = dff.groupby("facility", as_index=False)["traffic"].sum().sort_values("traffic", ascending=False)
    top_facility_value = top_facility_series.iloc[0]["facility"]
    records_value = len(dff)

    facility_count = len(facilities) if facilities else 0
    month_count = len(months) if months else 0
    selection_summary = (
        f"Years: {year_range[0]}–{year_range[1]} | "
        f"Facilities selected: {facility_count} | "
        f"Months selected: {month_count}"
    )

    # Trend chart
    trend_df = dff.groupby(["year_month", "facility"], as_index=False)["traffic"].sum()
    trend_fig = px.line(
        trend_df,
        x="year_month",
        y="traffic",
        color="facility",
        line_shape="spline",
        markers=True,
    )
    trend_fig.update_traces(line=dict(width=3), marker=dict(size=7))
    trend_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=20, b=20),
        legend_title_text="Facility",
        hovermode="x unified",
        yaxis_title="Traffic",
        xaxis_title="Date",
    )

    # Bar chart
    bar_df = dff.groupby("facility", as_index=False)["traffic"].sum().sort_values("traffic", ascending=False)
    bar_fig = px.bar(
        bar_df,
        x="facility",
        y="traffic",
        text="traffic",
    )
    bar_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    bar_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Facility",
        yaxis_title="Traffic",
    )

    # Pie chart
    pie_fig = px.pie(
        bar_df,
        names="facility",
        values="traffic",
        hole=0.55,
    )
    pie_fig.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>Traffic: %{value:,.0f}<br>Share: %{percent}")
    pie_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
    )

    # Month seasonality
    month_df = (
        dff.groupby(["month", "month_no"], as_index=False)["traffic"]
        .sum()
        .sort_values("month_no")
    )
    month_fig = px.bar(
        month_df,
        x="month",
        y="traffic",
        text="traffic",
    )
    month_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    month_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Month",
        yaxis_title="Traffic",
    )

    return (
        format_number(total_traffic_value),
        format_number(avg_traffic_value),
        top_facility_value,
        format_number(records_value),
        selection_summary,
        trend_fig,
        bar_fig,
        pie_fig,
        month_fig,
    )

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
