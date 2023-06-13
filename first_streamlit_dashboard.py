
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas_gbq


st.set_page_config(layout="wide", initial_sidebar_sate='expanded')
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = bigquery.Client(credentials=credentials)
background_color = '''
    <style>
        body {
            background-color: #f2f2f2;        }
    </style>
'''
st.sidebar.header('Preferences')

housing_score = st.slider('Profitability', 0, 5, value=5)
    climate_score = st.slider('Climate', 0, 5, value=5)
    tourism_score = st.slider('Tourism', 0, 5, value=5)
    dev_score = st.slider('Development', 0, 5, value=5)
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
st.markdown(background_color, unsafe_allow_html=True)


st.title('Where should I buy my secondary home?')
st.markdown("---")

row = st.columns((2, 4, 3), gap='large')

with row[0]:


with row[1]:
    st.header('Map')

    query = 'SELECT * FROM `scoring_tables.scores`'
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
        color='global_score',
        mapbox_style="carto-positron",
        center={"lat": 46.8, "lon": 1.8},
        zoom=4.5,
        opacity=0.7,
        labels={'global_score': 'Global Score'},
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig, use_container_width=True)

with row[2]:
    st.header('Top 10 departments')
    st.table(df[['department_name', 'global_score']].nlargest(10, 'global_score'))
    
