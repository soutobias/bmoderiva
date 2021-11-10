import streamlit as st
from bmoderiva import lib
from dotenv import load_dotenv
import os

load_dotenv()

df = lib.get_data(os.getenv('REMOBS_TOKEN'))

df = lib.calculate_distance(df)

st.write("# BMO-BR DERIVA")
st.write(f"### {(df['date_time'].min())} até {(df['date_time'].max())}")
st.write(f"### Última posição: LAT {(df['lat'].iloc[-1])}, LON {(df['lon'].iloc[-1])}")
lib.plot_map(df)

