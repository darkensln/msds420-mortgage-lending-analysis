"""
MSDS 420 Final Project — Interactive Dashboard
Team 4: Mortgage & Lending Analysis in Formerly Redlined Areas
Run: pip install dash plotly pandas numpy scipy scikit-learn
Then: python dashboard.py
Open: http://127.0.0.1:8050
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

# ========== CONFIG ==========
# UPDATE THESE PATHS to your local file locations
BASE = "/content/drive/MyDrive/MSDS420_Final_Project/"  # Google Colab path
# BASE = "./"  # Uncomment if running locally with CSVs in same folder

# ========== LOAD DATA ==========
try:
    loans_fnma = pd.read_csv(BASE + "fact_loans_chicago_fnma.csv")
    loans_fhlmc = pd.read_csv(BASE + "fact_loans_chicago_fhlmc.csv")
except FileNotFoundError:
    # Fallback: try current directory
    loans_fnma = pd.read_csv("fact_loans_chicago_fnma.csv")
    loans_fhlmc = pd.read_csv("fact_loans_chicago_fhlmc.csv")

loans = pd.concat([loans_fnma, loans_fhlmc], ignore_index=True)

try:
    dim_tract = pd.read_csv(BASE + "dim_tract_chicago.csv")
except FileNotFoundError:
    dim_tract = pd.read_csv("dim_tract_chicago.csv")

try:
    delinq_30 = pd.read_csv(BASE + "fact_delinquency_30_89_final.csv")
    delinq_90 = pd.read_csv(BASE + "fact_delinquency_90_plus_final.csv")
except FileNotFoundError:
    delinq_30 = pd.read_csv("fact_delinquency_30_89_final.csv")
    delinq_90 = pd.read_csv("fact_delinquency_90_plus_final.csv")

# ========== TRANSFORM ==========
loans = loans.merge(dim_tract, on=["tract_2020", "county_fips"], how="left")

county_map_fips = {
    31: "Cook", 43: "DuPage", 89: "Kane", 93: "Kendall",
    97: "Lake", 111: "McHenry", 197: "Will", 63: "Grundy", 37: "DeKalb"
}
county_map_id = {1:"Cook",2:"DuPage",3:"Grundy",4:"Will",5:"Kane",6:"Kendall",7:"Lake",8:"McHenry",9:"DeKalb"}

loans["county_name"] = loans["county_fips"].map(county_map_fips)
loans["enterprise_name"] = loans["enterprise"].map({1: "FNMA", 2: "FHLMC"})
loans["underserved"] = loans["area_concentrated_poverty"].map({0: "Non-Underserved", 1: "Underserved"})

delinq_90["year_month"] = pd.to_datetime(delinq_90["year_month"])
delinq_30["year_month"] = pd.to_datetime(delinq_30["year_month"])
delinq_90["county_name"] = delinq_90["county_id"].map(county_map_id)
delinq_30["county_name"] = delinq_30["county_id"].map(county_map_id)

# ========== REGRESSION ==========
reg_data = loans[["rate_orig","ltv","dti_cat","income_annual","area_concentrated_poverty","tract_minority_pct","tract_income_ratio","enterprise"]].dropna()
X = reg_data[["income_annual","ltv","dti_cat","area_concentrated_poverty","tract_minority_pct","tract_income_ratio","enterprise"]].copy()
X["income_annual"] = X["income_annual"] / 1000
y = reg_data["rate_orig"]

X_np = np.column_stack([np.ones(len(X)), X.values])
feature_names = ["const","Income ($K)","LTV","DTI","Underserved Tract","Minority %","Income Ratio","Enterprise"]
XtX_inv = np.linalg.inv(X_np.T @ X_np)
beta = XtX_inv @ X_np.T @ y.values
y_pred = X_np @ beta
residuals = y.values - y_pred
n, k = X_np.shape
mse = np.sum(residuals**2) / (n - k)
se = np.sqrt(np.diag(mse * XtX_inv))
t_stats_arr = beta / se
p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats_arr), df=n-k))
r2 = 1 - np.sum(residuals**2) / np.sum((y.values - np.mean(y.values))**2)

reg_df = pd.DataFrame({
    "Variable": feature_names[1:],
    "Coefficient": [round(b, 5) for b in beta[1:]],
    "Std Error": [round(s, 5) for s in se[1:]],
    "t-statistic": [round(t, 3) for t in t_stats_arr[1:]],
    "p-value": [f"{p:.2e}" for p in p_values[1:]],
    "Significant": ["Yes ***" if p < 0.001 else "Yes **" if p < 0.01 else "Yes *" if p < 0.05 else "No" for p in p_values[1:]]
})

# ========== COLORS ==========
NAVY = "#1E2761"
TEAL = "#028090"
CORAL = "#E85D4A"
LIGHT = "#F0F4F8"
WHITE = "#FFFFFF"

# ========== APP ==========
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Team 4 — Mortgage Lending Dashboard"

# Navigation tabs
tabs = dcc.Tabs(id="tabs", value="overview", children=[
    dcc.Tab(label="Project Overview", value="overview"),
    dcc.Tab(label="Underserved vs Non-Underserved", value="comparison"),
    dcc.Tab(label="County Delinquency", value="delinquency"),
    dcc.Tab(label="Regression Analysis", value="regression"),
    dcc.Tab(label="Enterprise Comparison", value="enterprise"),
], style={"fontFamily": "Georgia"})

app.layout = html.Div([
    html.Div([
        html.H1("Mortgage & Lending Analysis in Formerly Redlined Areas",
                 style={"color": WHITE, "fontFamily": "Georgia", "margin": "0", "fontSize": "28px"}),
        html.P("Team 4: Abdullah Abdul Sami | Qifan Yang | Selin — MSDS 420 Final Project",
               style={"color": "#A0AEC0", "margin": "5px 0 0 0", "fontSize": "14px"})
    ], style={"backgroundColor": NAVY, "padding": "20px 30px", "borderBottom": f"4px solid {TEAL}"}),
    html.Div([tabs], style={"padding": "0 20px"}),
    html.Div(id="tab-content", style={"padding": "20px 30px", "backgroundColor": LIGHT, "minHeight": "80vh"})
], style={"fontFamily": "Calibri, sans-serif"})

@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "overview":
        return render_overview()
    elif tab == "comparison":
        return render_comparison()
    elif tab == "delinquency":
        return render_delinquency()
    elif tab == "regression":
        return render_regression()
    elif tab == "enterprise":
        return render_enterprise()

def stat_card(title, value, color=TEAL):
    return html.Div([
        html.H3(value, style={"color": color, "margin": "0", "fontSize": "32px", "fontFamily": "Georgia"}),
        html.P(title, style={"color": "#64748B", "margin": "5px 0 0 0", "fontSize": "13px"})
    ], style={"backgroundColor": WHITE, "padding": "20px", "borderRadius": "8px",
              "textAlign": "center", "boxShadow": "0 2px 4px rgba(0,0,0,0.08)", "flex": "1", "margin": "0 8px"})

# ===== TAB 1: OVERVIEW =====
def render_overview():
    total = len(loans)
    tracts = loans["tract_2020"].nunique()
    counties = loans["county_name"].nunique()
    underserved = (loans["area_concentrated_poverty"] == 1).sum()

    return html.Div([
        html.Div([
            stat_card("Total Loans", f"{total:,}"),
            stat_card("Census Tracts", f"{tracts:,}"),
            stat_card("Counties", str(counties)),
            stat_card("Underserved Tracts", f"{loans[loans['area_concentrated_poverty']==1]['tract_2020'].nunique()}", CORAL),
        ], style={"display": "flex", "marginBottom": "20px"}),

        html.Div([
            html.Div([
                html.H3("Pipeline: Source → Transform → Load → Analyze", style={"color": NAVY}),
                html.Div([
                    html.Span("FHFA + CFPB CSVs", style={"backgroundColor": TEAL, "color": WHITE, "padding": "8px 16px", "borderRadius": "4px", "margin": "4px"}),
                    html.Span("→", style={"fontSize": "20px", "margin": "0 8px"}),
                    html.Span("Python / Pandas ETL", style={"backgroundColor": TEAL, "color": WHITE, "padding": "8px 16px", "borderRadius": "4px", "margin": "4px"}),
                    html.Span("→", style={"fontSize": "20px", "margin": "0 8px"}),
                    html.Span("PostgreSQL 3NF", style={"backgroundColor": NAVY, "color": WHITE, "padding": "8px 16px", "borderRadius": "4px", "margin": "4px"}),
                    html.Span("→", style={"fontSize": "20px", "margin": "0 8px"}),
                    html.Span("Dash Dashboard", style={"backgroundColor": CORAL, "color": WHITE, "padding": "8px 16px", "borderRadius": "4px", "margin": "4px"}),
                ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "margin": "15px 0"}),
            ], style={"backgroundColor": WHITE, "padding": "20px", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.08)"}),
        ]),

        html.Div([
            html.Div([
                dcc.Graph(figure=px.bar(
                    loans.groupby("county_name").size().reset_index(name="count").sort_values("count"),
                    x="count", y="county_name", orientation="h", color_discrete_sequence=[TEAL],
                    title="Loan Volume by County", labels={"count": "Number of Loans", "county_name": ""}
                ).update_layout(showlegend=False, plot_bgcolor=WHITE, paper_bgcolor=WHITE))
            ], style={"flex": "1", "margin": "0 8px"}),
            html.Div([
                dcc.Graph(figure=px.pie(
                    loans, names="underserved", color="underserved",
                    color_discrete_map={"Non-Underserved": TEAL, "Underserved": CORAL},
                    title="Underserved vs Non-Underserved Loans"
                ).update_layout(paper_bgcolor=WHITE))
            ], style={"flex": "1", "margin": "0 8px"}),
        ], style={"display": "flex", "marginTop": "20px"})
    ])

# ===== TAB 2: COMPARISON =====
def render_comparison():
    metrics = ["rate_orig", "ltv", "dti_cat", "income_annual"]
    labels = ["Interest Rate (%)", "LTV Ratio (%)", "DTI Category", "Borrower Income ($)"]

    fig = make_subplots(rows=1, cols=4, subplot_titles=labels)
    for i, (col, label) in enumerate(zip(metrics, labels)):
        for j, (group, color) in enumerate(zip(["Non-Underserved", "Underserved"], [TEAL, CORAL])):
            data = loans[loans["underserved"] == group][col].dropna()
            fig.add_trace(go.Bar(
                x=[group], y=[data.mean()], name=group if i == 0 else None,
                marker_color=color, showlegend=(i == 0),
                text=[f"${data.mean():,.0f}" if col == "income_annual" else f"{data.mean():.2f}"],
                textposition="outside"
            ), row=1, col=i+1)
    fig.update_layout(title="Underserved vs Non-Underserved: Key Metrics", height=450,
                      plot_bgcolor=WHITE, paper_bgcolor=WHITE, barmode="group")

    # Distribution
    fig2 = px.histogram(loans, x="rate_orig", color="underserved", nbins=50, barmode="overlay",
                        color_discrete_map={"Non-Underserved": TEAL, "Underserved": CORAL},
                        title="Interest Rate Distribution by Tract Type", opacity=0.7,
                        labels={"rate_orig": "Interest Rate (%)", "underserved": "Tract Type"})
    fig2.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE)

    # T-test results
    ttest_rows = []
    for col, label in zip(metrics, labels):
        u = loans[loans["area_concentrated_poverty"]==1][col].dropna()
        n = loans[loans["area_concentrated_poverty"]==0][col].dropna()
        t_stat, p_val = stats.ttest_ind(u, n)
        ttest_rows.append({"Metric": label, "Non-Underserved": f"{n.mean():.2f}", "Underserved": f"{u.mean():.2f}",
                          "Difference": f"{u.mean()-n.mean():.3f}", "t-statistic": f"{t_stat:.3f}", "p-value": f"{p_val:.2e}",
                          "Significant": "Yes ***" if p_val < 0.001 else "No"})

    return html.Div([
        dcc.Graph(figure=fig),
        html.Div([
            html.Div([dcc.Graph(figure=fig2)], style={"flex": "1"}),
        ], style={"display": "flex"}),
        html.H3("Statistical Significance Tests (Independent t-tests)", style={"color": NAVY, "marginTop": "20px"}),
        dash_table.DataTable(
            data=ttest_rows,
            columns=[{"name": c, "id": c} for c in ttest_rows[0].keys()],
            style_header={"backgroundColor": NAVY, "color": WHITE, "fontWeight": "bold"},
            style_cell={"textAlign": "center", "padding": "10px", "fontFamily": "Calibri"},
            style_data_conditional=[{"if": {"column_id": "Significant"}, "color": CORAL, "fontWeight": "bold"}]
        )
    ])

# ===== TAB 3: DELINQUENCY =====
def render_delinquency():
    return html.Div([
        html.Div([
            html.Label("Select Counties:", style={"fontWeight": "bold", "color": NAVY}),
            dcc.Dropdown(
                id="county-dropdown",
                options=[{"label": c, "value": c} for c in sorted(delinq_90["county_name"].dropna().unique())],
                value=["Cook", "DuPage", "Will"],
                multi=True
            ),
        ], style={"marginBottom": "15px"}),
        html.Div([
            html.Div([dcc.Graph(id="delinq-90-chart")], style={"flex": "1", "margin": "0 8px"}),
            html.Div([dcc.Graph(id="delinq-30-chart")], style={"flex": "1", "margin": "0 8px"}),
        ], style={"display": "flex"}),
        html.Div([dcc.Graph(id="delinq-heatmap")]),
    ])

@app.callback(
    [Output("delinq-90-chart", "figure"), Output("delinq-30-chart", "figure"), Output("delinq-heatmap", "figure")],
    Input("county-dropdown", "value")
)
def update_delinquency(counties):
    d90 = delinq_90[delinq_90["county_name"].isin(counties)]
    d30 = delinq_30[delinq_30["county_name"].isin(counties)]

    fig90 = px.line(d90, x="year_month", y="delinquency_rate", color="county_name",
                    title="90+ Day Delinquency Rate", labels={"delinquency_rate": "Rate (%)", "year_month": ""},
                    color_discrete_sequence=px.colors.qualitative.Bold)
    fig90.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE)

    fig30 = px.line(d30, x="year_month", y="delinquency_rate", color="county_name",
                    title="30-89 Day Delinquency Rate", labels={"delinquency_rate": "Rate (%)", "year_month": ""},
                    color_discrete_sequence=px.colors.qualitative.Bold)
    fig30.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE)

    # Heatmap
    d90["year"] = d90["year_month"].dt.year
    pivot = d90.pivot_table(index="county_name", columns="year", values="delinquency_rate", aggfunc="mean")
    heatmap = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="YlOrRd",
                                    colorbar=dict(title="Rate %")))
    heatmap.update_layout(title="90+ Delinquency by County & Year", plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=350)

    return fig90, fig30, heatmap

# ===== TAB 4: REGRESSION =====
def render_regression():
    fig = go.Figure(go.Bar(
        y=reg_df["Variable"], x=reg_df["Coefficient"], orientation="h",
        marker_color=[CORAL if "Yes" in s else "#94A3B8" for s in reg_df["Significant"]],
        text=[f"{c:.4f}" for c in reg_df["Coefficient"]], textposition="outside"
    ))
    fig.update_layout(title=f"OLS Regression Coefficients (R² = {r2:.4f}, N = {n:,})",
                      xaxis_title="Effect on Interest Rate (%)", plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=400)

    return html.Div([
        html.H3("Complex Q1: Does tract location predict rate after controlling for income, DTI, LTV?", style={"color": NAVY}),
        html.Div([
            html.P([html.B("Answer: YES."), f" After controlling for income, LTV, DTI, minority %, income ratio, and enterprise, "
                    f"being in an underserved tract adds {beta[4]:.3f} percentage points to the interest rate (p < 0.001)."],
                   style={"fontSize": "16px", "backgroundColor": WHITE, "padding": "15px", "borderLeft": f"4px solid {CORAL}",
                          "borderRadius": "4px"}),
        ]),
        dcc.Graph(figure=fig),
        html.H3("Full Regression Results", style={"color": NAVY}),
        dash_table.DataTable(
            data=reg_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in reg_df.columns],
            style_header={"backgroundColor": NAVY, "color": WHITE, "fontWeight": "bold"},
            style_cell={"textAlign": "center", "padding": "10px", "fontFamily": "Calibri"},
            style_data_conditional=[
                {"if": {"filter_query": '{Significant} contains "Yes"'}, "backgroundColor": "#FEF2F2"},
            ]
        ),
        html.P(f"Model: rate_orig ~ income + LTV + DTI + underserved + minority% + income_ratio + enterprise",
               style={"color": "#64748B", "fontStyle": "italic", "marginTop": "10px"})
    ])

# ===== TAB 5: ENTERPRISE =====
def render_enterprise():
    ent_data = loans.groupby(["enterprise_name", "underserved"]).agg(
        avg_rate=("rate_orig", "mean"), avg_ltv=("ltv", "mean"),
        avg_dti=("dti_cat", "mean"), avg_income=("income_annual", "mean"),
        count=("rate_orig", "count")
    ).reset_index()

    fig = make_subplots(rows=1, cols=3, subplot_titles=["Avg Interest Rate", "Avg LTV", "Avg DTI"])
    for i, col in enumerate(["avg_rate", "avg_ltv", "avg_dti"]):
        for group, color in zip(["Non-Underserved", "Underserved"], [TEAL, CORAL]):
            d = ent_data[ent_data["underserved"] == group]
            fig.add_trace(go.Bar(
                x=d["enterprise_name"], y=d[col], name=group if i == 0 else None,
                marker_color=color, showlegend=(i == 0),
                text=[f"{v:.2f}" for v in d[col]], textposition="outside"
            ), row=1, col=i+1)
    fig.update_layout(title="FNMA vs FHLMC: Both Enterprises Show Same Disparities",
                      height=450, barmode="group", plot_bgcolor=WHITE, paper_bgcolor=WHITE)

    return html.Div([
        dcc.Graph(figure=fig),
        html.Div([
            html.P("Both Fannie Mae and Freddie Mac show the same pattern: higher rates, higher LTV, and higher DTI "
                   "in underserved tracts. Geographic and socioeconomic factors dominate over enterprise-specific pricing.",
                   style={"fontSize": "14px", "backgroundColor": WHITE, "padding": "15px", "borderLeft": f"4px solid {TEAL}",
                          "borderRadius": "4px"})
        ])
    ])

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  MSDS 420 — Mortgage Lending Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*50 + "\n")
    app.run(debug=True, port=8050)
