import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas_gbq

st.set_page_config(layout="wide", initial_sidebar_state='expanded')
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = bigquery.Client(credentials=credentials)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Sidebar

# st.sidebar.header('Second Home Finder')

st.sidebar.markdown("---")

st.markdown(
    f'''
        <style>
            .sidebar .sidebar-content {{
                width: 500px;
            }}
        </style>
    ''',
    unsafe_allow_html=True
)

st.sidebar.subheader('parameters')
housing_score = st.sidebar.slider('Profitability', 0, 5, value=5)
climate_score = st.sidebar.slider('Climate', 0, 5, value=5)
tourism_score = st.sidebar.slider('Tourism', 0, 5, value=5)
dev_score = st.sidebar.slider('Development', 0, 5, value=5)
total_score = housing_score + climate_score + tourism_score + dev_score

if total_score != 0:
    housing_weight = housing_score / total_score
    climate_weight = climate_score / total_score
    dev_weight = dev_score / total_score
    tourism_weight = tourism_score / total_score
else:
    housing_weight = 1 / 4
    climate_weight = 1 / 4
    dev_weight = 1 / 4
    tourism_weight = 1 / 4

# st.sidebar.subheader('Map parameters')

st.sidebar.subheader('Metrics')
filter_data = st.sidebar.multiselect('Select data', ['predicted_hot_days', 'temperature_gap', 'secondary_home_rate', 'avg_yield'], default='avg_yield')


st.title('Where should I buy my second home?')
st.markdown("---")


col1, inter_space, col2 = st.columns((2,0.2, 3), gap='small')

# col1.markdown('### Top 10 departments')

query = 'SELECT * FROM `dbt_ghurez_departments.dep_all_kpis`'
df = pd.read_gbq(query, project_id="team-prello-jogaan", credentials=credentials)
df['tourism_score'] = df['tourism_score'].astype(float)
df['climate_score'] = df['climate_score'].astype(float)
df['immo_score'] = df['immo_score'].astype(float)
df['dev_score'] = df['dev_score'].astype(float)
df['global_score'] = round((df['tourism_score'] * tourism_weight
                            + df['climate_score'] * climate_weight
                            + df['immo_score'] * housing_weight
                            + df['dev_score'] * dev_weight), 2)

df_geo = pd.read_csv('data/geo_departments.csv')
df = pd.merge(df, df_geo, on='department_name')

geodata = gpd.read_file('data/departements.geojson')
df_geo = pd.merge(geodata, df, left_on='nom', right_on='department_name', how='inner')

top_10_departments = df_geo.nlargest(10, 'global_score')
fig = px.choropleth_mapbox(
    top_10_departments,
    geojson=top_10_departments.geometry,
    locations=top_10_departments.index,
    color=filter_data[0],
    mapbox_style="carto-positron",
    center={"lat": 46.8, "lon": 1.8},
    zoom=4.2,
    opacity=0.7,
    labels={'global_score': 'Global Score'},
    
)

fig.update_layout(margin={"r": 200, "t": 70, "l": 0, "b": 0}, showlegend=False, legend_itemwidth=35, width=650)

# First line : map and top 10

col1.header('Top 10')
col2.plotly_chart(fig, use_container_width=False)
col1.dataframe(df[['department_name', 'region_name', 'global_score']].nlargest(10, 'global_score'), hide_index=True, width=400)


# Line 2 : Metrics


fig_2 = px.bar(top_10_departments, x=filter_data, y='department_name', barmode='group', orientation='h', text='department_name')
fig_2.update_traces(textposition="inside", insidetextanchor="start", textfont_size=15)
fig_2.update_layout(width=200, margin={"r": 150, "t": 90, "l": 0, "b": 0},showlegend=False, yaxis={'side' : 'right', 'visible' : False, 'categoryorder':'total ascending', 'title' : None,}, xaxis={'title' : filter_data[0], 'side' : 'top'})
col1.header('Metrics')
col2.plotly_chart(fig_2, use_container_width=True)

fig_3 = px.treemap(top_10_departments, path=[px.Constant('All'),'department_name'], values=filter_data[0], color=filter_data[0])
fig_3.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 75}, xaxis={'title' : filter_data[0]})
fig_3.update_traces(root_color="whitesmoke")
fig_3.update(layout_coloraxis_showscale=False)
col1.plotly_chart(fig_3, use_container_width=True)


# st.markdown("---")
top_10_departments.columns
