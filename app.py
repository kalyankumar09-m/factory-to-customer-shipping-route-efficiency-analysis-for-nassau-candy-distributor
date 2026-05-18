import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Shipping Efficiency Dashboard", layout="wide")
# Title
st.title("Nassau Candy Dashboard")


# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    file_path ="Nassau Candy Distributor.csv"

    df = pd.read_csv(file_path)
    return df


# ---------------- PREPROCESS ----------------
def preprocess(df):

    # Convert to datetime (handle errors safely)
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')

    # Drop invalid dates
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    # Lead time calculation
    df['Lead_Time'] = (df['Ship Date'] - df['Order Date']).dt.days

    # Remove negative lead times
    df = df[df['Lead_Time'] >= 0]

    # Factory mapping
    factory_map = {
        "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
        "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
        "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
        "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
        "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
        "Laffy Taffy": "Sugar Shack",
        "SweeTARTS": "Sugar Shack",
        "Nerds": "Sugar Shack",
        "Fun Dip": "Sugar Shack",
        "Fizzy Lifting Drinks": "Sugar Shack",
        "Everlasting Gobstopper": "Secret Factory",
        "Hair Toffee": "The Other Factory",
        "Lickable Wallpaper": "Secret Factory",
        "Wonka Gum": "Secret Factory",
        "Kazookles": "The Other Factory"
    }

    # Map factory safely
    df['Factory'] = df['Product Name'].map(factory_map).fillna("Unknown")

    # Route
    df['Route'] = df['Factory'] + " → " + df['State/Province']

    # Delay flag
    df['Delayed'] = df['Lead_Time'] > 5

    return df


# ---------------- SUMMARY ----------------
def route_summary(df):
    summary = df.groupby('Route').agg(
        Avg_Lead_Time=('Lead_Time', 'mean'),
        Volume=('Order ID', 'count'),
        Delay_Percentage=('Delayed', 'mean')
    ).reset_index()

    summary['Delay_Percentage'] = summary['Delay_Percentage'] * 100
    summary['Efficiency_Rank'] = summary['Avg_Lead_Time'].rank()

    return summary


# ---------------- MAIN ----------------
df = load_data()
df = preprocess(df)

st.sidebar.header("Filters")

region = st.sidebar.multiselect(
    "Region",
    options=df['Region'].dropna().unique(),
    default=df['Region'].dropna().unique()
)

ship_mode = st.sidebar.multiselect(
    "Ship Mode",
    options=df['Ship Mode'].dropna().unique(),
    default=df['Ship Mode'].dropna().unique()
)

start_date = st.sidebar.date_input("Start Date", df['Order Date'].min())
end_date = st.sidebar.date_input("End Date", df['Order Date'].max())


# ---------------- FILTER ----------------
filtered = df[
    (df['Region'].isin(region)) &
    (df['Ship Mode'].isin(ship_mode)) &
    (df['Order Date'] >= pd.to_datetime(start_date)) &
    (df['Order Date'] <= pd.to_datetime(end_date))
]


# ---------------- DASHBOARD ----------------
st.title("Shipping Route Efficiency Dashboard")

st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg Lead Time", round(filtered['Lead_Time'].mean(), 2) if not filtered.empty else 0)
col2.metric("Total Orders", filtered.shape[0])
col3.metric("Delay %", f"{round(filtered['Delayed'].mean()*100,2) if not filtered.empty else 0}%")
col4.metric("Unique Routes", filtered['Route'].nunique())


# ---------------- LEADERBOARD ----------------
st.subheader("Route Efficiency Leaderboard")

leaderboard = route_summary(filtered)

st.dataframe(leaderboard.sort_values('Avg_Lead_Time'))


# ---------------- TOP / BOTTOM ----------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Routes")
    st.dataframe(leaderboard.nsmallest(10, 'Avg_Lead_Time'))

with col2:
    st.subheader("Bottom 10 Routes")
    st.dataframe(leaderboard.nlargest(10, 'Avg_Lead_Time'))


# ---------------- SHIP MODE ----------------
st.subheader("Ship Mode Performance")

ship_perf = filtered.groupby('Ship Mode')['Lead_Time'].mean().reset_index()

fig1 = px.bar(ship_perf, x='Ship Mode', y='Lead_Time',
              title="Lead Time by Ship Mode")

st.plotly_chart(fig1, use_container_width=True)


# ---------------- STATE ANALYSIS ----------------
st.subheader("State Bottleneck Analysis")

state_perf = filtered.groupby('State/Province').agg(
    Avg_Lead_Time=('Lead_Time', 'mean'),
    Volume=('Order ID', 'count')
).reset_index()

fig2 = px.scatter(
    state_perf,
    x='Volume',
    y='Avg_Lead_Time',
    size='Volume',
    color='Avg_Lead_Time',
    hover_name='State/Province',
    title="High Volume vs Delay States"
)

st.plotly_chart(fig2, use_container_width=True)


# ---------------- TREND ----------------
st.subheader("Shipping Trend Over Time")

trend = filtered.groupby(
    filtered['Order Date'].dt.to_period('M')
)['Lead_Time'].mean().reset_index()

trend['Order Date'] = trend['Order Date'].astype(str)

fig3 = px.line(trend, x='Order Date', y='Lead_Time',
               title="Monthly Avg Lead Time")

st.plotly_chart(fig3, use_container_width=True)


# ---------------- RAW DATA ----------------
st.subheader("Raw Dataset")
st.dataframe(filtered)
