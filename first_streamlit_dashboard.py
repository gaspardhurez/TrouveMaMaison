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

st.sidebar.subheader("Critères d'achat")
housing_score = st.sidebar.slider('Rentabilité', 0, 5, value=5)
climate_score = st.sidebar.slider('Prédictions climatiques', 0, 5, value=5)
tourism_score = st.sidebar.slider('Tourisme', 0, 5, value=5)
dev_score = st.sidebar.slider('Développement', 0, 5, value=5)
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

st.sidebar.subheader('Table')
data_table = st.sidebar.multiselect("Sélectionner jusqu'à 3 métriques", ['Jours caniculaires', 'Ecart de temperature (2050)', 'Taux de maisons secondaires', 'Rentabilité locative'], default=['Ecart de temperature (2050)', 'Taux de maisons secondaires', 'Rentabilité locative'], key=1, max_selections=3)

st.sidebar.subheader('Carte proportionnelle')
data_treemap = st.sidebar.selectbox('Sélectionner une métrique', ['Jours caniculaires', 'Ecart de temperature (2050)', 'Taux de maisons secondaires', 'Rentabilité locative'], index = 1, key=2)

st.sidebar.subheader('Graphique à barres')
data_bar = st.sidebar.selectbox('Sélectionner une métrique', ['Jours caniculaires', 'Ecart de temperature (2050)', 'Taux de maisons secondaires', 'Rentabilité locative'], index = 2,  key=3)


#st.title('Où acheter ma deuxième maison?')
# st.markdown("---")


col1, inter_space, col2 = st.columns((2,0.2, 3), gap='small')
blank_space_1 = col1.write('')
blank_space_2 = col2.write('')

# Chargement des données et calculs

query = 'SELECT * FROM `dbt_ghurez_departments.dep_all_kpis`'
df = pd.read_gbq(query, project_id="team-prello-jogaan", credentials=credentials)
df['tourism_score_normalized'] = df['tourism_score_normalized'].astype(float)
df['climate_score_normalized'] = df['climate_score_normalized'].astype(float)
df['immo_score_normalized'] = df['immo_score_normalized'].astype(float)
df['dev_score_normalized'] = df['dev_score_normalized'].astype(float)
df['global_score'] = round((df['tourism_score_normalized'] * tourism_weight
                            + df['climate_score_normalized'] * climate_weight
                            + df['immo_score_normalized'] * housing_weight
                            + df['dev_score_normalized'] * dev_weight), 2)

df_geo = pd.read_csv('data/geo_departments.csv')
df = pd.merge(df, df_geo, on='department_name')

geodata = gpd.read_file('data/departements.geojson')
df_geo = pd.merge(geodata, df, left_on='nom', right_on='department_name', how='inner')

top_10_departments = df_geo.nlargest(10, 'global_score')

top_10_departments['Jours caniculaires'] = top_10_departments['predicted_hot_days']
top_10_departments['Rentabilité locative'] = top_10_departments['avg_yield']
top_10_departments['Ecart de temperature (2050)'] = top_10_departments['temperature_gap']
top_10_departments["Taux de maisons secondaires"] = top_10_departments['secondary_home_rate']


# Line 1 : T op 10

col1.header('Top 10')

    # Column 1

col1.write('')
top_10_departments_df = top_10_departments.loc[:, data_table]
top_10_departments_df['department_name'] = top_10_departments['department_name']
top_10_departments_df = top_10_departments_df.set_index('department_name')
col1.dataframe(top_10_departments_df, hide_index=False, use_container_width=True)


    # Column 2

col2.write('')
col2.write('')
fig = px.choropleth_mapbox(
    top_10_departments,
    geojson=top_10_departments.geometry,
    locations=top_10_departments.index,
    color='global_score',
    mapbox_style="carto-positron",
    center={"lat": 46.8, "lon": 1.8},
    zoom=4.2,
    opacity=0.7,
    labels={'global_score': 'Global Score'},
    
)
fig.update_layout(margin={"r": 200, "t": 70, "l": 0, "b": 0}, showlegend=False, legend_itemwidth=35, width=650)
col2.plotly_chart(fig, use_container_width=False)

# Line 2 : Metrics

col1.header('Métriques')

    # Column 1

col1.write('')
fig_3 = px.treemap(top_10_departments, path=[px.Constant('All'),'department_name'], values=data_treemap, color=data_treemap)
fig_3.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 75}, xaxis={'title' : data_treemap})
fig_3.update_traces(root_color="whitesmoke")
fig_3.update(layout_coloraxis_showscale=False)
col1.plotly_chart(fig_3, use_container_width=True)

    # Column 2

col2.write('')
fig_2 = px.bar(top_10_departments, x=data_bar, y='department_name', barmode='group', orientation='h', text='department_name')
fig_2.update_traces(textposition="inside", insidetextanchor="start", textfont_size=15)
fig_2.update_layout(width=200, margin={"r": 150, "t": 90, "l": 0, "b": 0},showlegend=False, yaxis={'side' : 'right', 'visible' : False, 'categoryorder':'total ascending', 'title' : None,}, xaxis={'title' : data_bar[0], 'side' : 'top'})
col2.plotly_chart(fig_2, use_container_width=True)




# st.markdown("---")
top_10_departments.columns
