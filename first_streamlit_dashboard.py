import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")

st.title('Where should I buy my secondary home?')
st.markdown("---")

row = st.columns((2, 4, 3), gap='large')

with row[0]:
    st.header('Preferences')

    housing_score = st.slider('Housing KPIs', 0, 5, value=5)
    climate_score = st.slider('Climate KPIs', 0, 5, value=5)
    attractivity_score = st.slider('Attractivity KPIs', 0, 5, value=5)
    dynamism_score = st.slider('Dynamism KPIs', 0, 5, value=5)
    total_score = housing_score + climate_score + attractivity_score + dynamism_score

    if total_score != 0:
        housing_weight = housing_score / total_score
        climate_weight = climate_score / total_score
        dynamism_weight = dynamism_score / total_score
        attractivity_weight = attractivity_score / total_score
    else:
        housing_weight = 1 / 4
        climate_weight = 1 / 4
        dynamism_weight = 1 / 4
        attractivity_weight = 1 / 4

with row[1]:
    st.header('Map')
    
    df = pd.read_csv('data/department_scores.csv')
    df['attr_score'] = df['attr_score'].str.replace(',', '.').astype(float)
    df['climate_score'] = df['climate_score'].str.replace(',', '.').astype(float)
    df['immo_score'] = df['immo_score'].str.replace(',', '.').astype(float)
    df['dyn_score'] = df['dyn_score'].str.replace(',', '.').astype(float)
    df['global_score'] = round((df['attr_score'] * attractivity_weight
                                + df['climate_score'] * climate_weight
                                + df['immo_score'] * housing_weight
                                + df['dyn_score'] * dynamism_weight), 2)

    df_geo = pd.read_csv('data/geo_departments.csv')
    df = pd.merge(df, df_geo, on='department_name')

    geodata = gpd.read_file('data/departements.geojson')
    df_geo = pd.merge(geodata, df, left_on='nom', right_on='department_name', how='inner')

    top_10_departments = df_geo.nlargest(10, 'global_score')
    fig = px.choropleth_mapbox(
        top_10_departments.head(5),
        geojson=top_10_departments.geometry,
        locations=top_10_departments.head(5).index,
        color='global_score',
        mapbox_style="carto-positron",
        center={"lat": 46.8, "lon": 2.4},
        zoom=4.5,
        opacity=0.7,
        labels={'global_score': 'Global Score'},
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig, use_container_width=True)

with row[2]:

    st.header('Top 10 departments')
    st.table(df[['department_name', 'region_name', 'global_score']].nlargest(10, 'global_score'))
