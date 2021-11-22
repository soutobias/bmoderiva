import streamlit as st
from bmoderiva import lib
from dotenv import load_dotenv
import os

load_dotenv()


df = lib.get_data(os.getenv('REMOBS_TOKEN'))
df1 = lib.get_data_bmo(os.getenv('REMOBS_TOKEN'))
mapbox_token = os.getenv("MAPBOX_TOKEN")



st.write("# BMO-BR DERIVA")
st.write(f"## DADO TAG")
if df.empty:
    st.write('#### Não há dados da TAG')
else:
    st.write(f"#### {(df['date_time'].min())} até {(df['date_time'].max())}")
    st.write(f"#### Última posição: LAT {(df['lat'].iloc[-1])}, LON {(df['lon'].iloc[-1])}")
    df = lib.calculate_distance(df)
    lib.plot_map(df)

st.write(f"## DADO BMO")
if df.empty:
    st.write('#### Não há dados da antena da BMO')
else:
    st.write(f"#### {(df1['date_time'].min())} até {(df1['date_time'].max())}")
    st.write(f"#### Última posição: LAT {(df1['lat'].iloc[-1])}, LON {(df1['lon'].iloc[-1])}")
    df1 = lib.calculate_distance(df1)
    df2 = lib.df_time_interval(df1)
    #lib.plot_map(df1)
    #st.write("## Histórico de Tempo")
    lib.plot_map_time(df2, mapbox_token)