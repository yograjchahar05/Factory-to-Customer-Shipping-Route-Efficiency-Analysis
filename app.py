import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Nassau Shipping Intelligence Dashboard",
    layout="wide"
)

st.title("Nassau Candy Distributor")
st.subheader("Shipping Route Efficiency Intelligence Dashboard")

# --------------------------------------------------
# Data Loading
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("nassau.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True)
    df["Lead_Time"] = (df["Ship Date"] - df["Order Date"]).dt.days
    return df

df = load_data()

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Order Date Range",
    [df["Order Date"].min(), df["Order Date"].max()]
)

region_filter = st.sidebar.multiselect(
    "Region",
    df["Region"].unique(),
    default=df["Region"].unique()
)

shipmode_filter = st.sidebar.multiselect(
    "Ship Mode",
    df["Ship Mode"].unique(),
    default=df["Ship Mode"].unique()
)

delay_threshold = st.sidebar.slider(
    "Delay Threshold (Days)",
    int(df["Lead_Time"].min()),
    int(df["Lead_Time"].max()),
    int(df["Lead_Time"].mean())
)

# --------------------------------------------------
# Apply Filters
# --------------------------------------------------
filtered_df = df[
    (df["Order Date"] >= pd.to_datetime(date_range[0])) &
    (df["Order Date"] <= pd.to_datetime(date_range[1])) &
    (df["Region"].isin(region_filter)) &
    (df["Ship Mode"].isin(shipmode_filter))
]

# --------------------------------------------------
# KPI Section
# --------------------------------------------------
st.markdown("## Key Performance Indicators")

total_shipments = len(filtered_df)
avg_lead = filtered_df["Lead_Time"].mean()
total_profit = filtered_df["Gross Profit"].sum()
delay_percent = (filtered_df["Lead_Time"] > delay_threshold).mean() * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Shipments", f"{total_shipments:,}")
col2.metric("Average Lead Time", f"{avg_lead:.2f} days")
col3.metric("Total Profit", f"${total_profit:,.2f}")
col4.metric("Delay Percentage", f"{delay_percent:.2f}%")

st.markdown("---")

# --------------------------------------------------
# State-Level Analysis
# --------------------------------------------------
st.markdown("## State-Level Performance")

state_analysis = filtered_df.groupby("State/Province").agg(
    Total_Shipments=("Order ID", "count"),
    Avg_Lead_Time=("Lead_Time", "mean"),
    Total_Profit=("Gross Profit", "sum")
).reset_index()

top_10 = state_analysis.sort_values("Avg_Lead_Time").head(10)
bottom_10 = state_analysis.sort_values("Avg_Lead_Time", ascending=False).head(10)

colA, colB = st.columns(2)

with colA:
    fig_top = px.bar(
        top_10,
        x="Avg_Lead_Time",
        y="State/Province",
        orientation="h",
        color="Avg_Lead_Time",
        color_continuous_scale="Greens",
        title="Top 10 Efficient States"
    )
    fig_top.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_top, use_container_width=True)

with colB:
    fig_bottom = px.bar(
        bottom_10,
        x="Avg_Lead_Time",
        y="State/Province",
        orientation="h",
        color="Avg_Lead_Time",
        color_continuous_scale="Reds",
        title="Top 10 High-Delay States"
    )
    fig_bottom.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bottom, use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# Regional Analysis
# --------------------------------------------------
st.markdown("## Regional Performance")

region_analysis = filtered_df.groupby("Region").agg(
    Avg_Lead_Time=("Lead_Time", "mean"),
    Total_Shipments=("Order ID", "count")
).reset_index()

fig_region = px.bar(
    region_analysis,
    x="Region",
    y="Avg_Lead_Time",
    color="Region",
    title="Average Lead Time by Region"
)

st.plotly_chart(fig_region, use_container_width=True)

# --------------------------------------------------
# Ship Mode Analysis
# --------------------------------------------------
st.markdown("## Ship Mode Performance")

shipmode_analysis = filtered_df.groupby("Ship Mode").agg(
    Avg_Lead_Time=("Lead_Time", "mean"),
    Total_Shipments=("Order ID", "count")
).reset_index()

fig_ship = px.bar(
    shipmode_analysis,
    x="Ship Mode",
    y="Avg_Lead_Time",
    color="Ship Mode",
    title="Average Lead Time by Ship Mode"
)

st.plotly_chart(fig_ship, use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# US Heatmap
# --------------------------------------------------
st.markdown("## US State Shipping Heatmap")

us_state_abbrev = {
    'Alabama': 'AL','Alaska': 'AK','Arizona': 'AZ','Arkansas': 'AR',
    'California': 'CA','Colorado': 'CO','Connecticut': 'CT',
    'Delaware': 'DE','Florida': 'FL','Georgia': 'GA','Hawaii': 'HI',
    'Idaho': 'ID','Illinois': 'IL','Indiana': 'IN','Iowa': 'IA',
    'Kansas': 'KS','Kentucky': 'KY','Louisiana': 'LA','Maine': 'ME',
    'Maryland': 'MD','Massachusetts': 'MA','Michigan': 'MI',
    'Minnesota': 'MN','Mississippi': 'MS','Missouri': 'MO',
    'Montana': 'MT','Nebraska': 'NE','Nevada': 'NV',
    'New Hampshire': 'NH','New Jersey': 'NJ','New Mexico': 'NM',
    'New York': 'NY','North Carolina': 'NC','North Dakota': 'ND',
    'Ohio': 'OH','Oklahoma': 'OK','Oregon': 'OR',
    'Pennsylvania': 'PA','Rhode Island': 'RI',
    'South Carolina': 'SC','South Dakota': 'SD',
    'Tennessee': 'TN','Texas': 'TX','Utah': 'UT',
    'Vermont': 'VT','Virginia': 'VA','Washington': 'WA',
    'West Virginia': 'WV','Wisconsin': 'WI','Wyoming': 'WY'
}

us_data = state_analysis[state_analysis["State/Province"].isin(us_state_abbrev.keys())].copy()
us_data["State_Code"] = us_data["State/Province"].map(us_state_abbrev)

if not us_data.empty:
    fig_map = px.choropleth(
        us_data,
        locations="State_Code",
        locationmode="USA-states",
        color="Avg_Lead_Time",
        scope="usa",
        color_continuous_scale="Reds",
        hover_name="State/Province",
        hover_data={
            "Avg_Lead_Time": True,
            "Total_Shipments": True,
            "Total_Profit": True
        },
        title="State-wise Average Lead Time"
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No US state data available for selected filters.")

st.markdown("---")

# --------------------------------------------------
# Drill Down Table
# --------------------------------------------------
st.markdown("## Detailed State Performance")

st.dataframe(
    state_analysis.sort_values("Avg_Lead_Time"),
    use_container_width=True
)

# --------------------------------------------------
# Executive Summary
# --------------------------------------------------
st.markdown("## Executive Summary")

if not state_analysis.empty:
    fastest_state = state_analysis.sort_values("Avg_Lead_Time").iloc[0]["State/Province"]
    slowest_state = state_analysis.sort_values("Avg_Lead_Time", ascending=False).iloc[0]["State/Province"]
else:
    fastest_state = "N/A"
    slowest_state = "N/A"

st.markdown(f"""
Most Efficient State: **{fastest_state}**  
Highest Delay State: **{slowest_state}**  
Total Shipments Analyzed: **{total_shipments:,}**  
Overall Average Lead Time: **{avg_lead:.2f} days**  
Shipments Above Threshold: **{delay_percent:.2f}%**
""")

st.caption("Developed for Unified Mentor Internship | Logistics Intelligence Analytics")
