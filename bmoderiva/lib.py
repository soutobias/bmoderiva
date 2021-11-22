import pandas as pd
import numpy as np
import requests
from bmoderiva.distance import haversine
import folium
from streamlit_folium import folium_static
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import timezone
import math

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from dotenv import load_dotenv
load_dotenv()

import psycopg2 as pg


class remobs_db():
    
    _db = None
    def __init__(self, host, db, usr, pwd):
        self._db = pg.connect(host=host, database=db, user=usr, password=pwd)

    def db_exec(self, query):
        try:
            cur = self.cursor()
            cur.execute(query)
            cur.close()
            self._db.commit()
        except:
            return False
        return True

    def db_select(self, query):
        try:
            data = pd.read_sql_query(query, self._db)
        except:
            return False
        return data




def get_data(token):
    time_now = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
    start_time = '2021-10-20'
    url=f'http://remobsapi.herokuapp.com/api/v1/tags?start_date={start_time}&end_date={time_now}&token={token}'

    try:
        response = requests.get(url).json()
        df = pd.DataFrame(response)
        for i in df.columns:
            try:
                df[i] = pd.to_numeric(df[i])
            except:
                pass

        df['date_time'] = pd.to_datetime(df['date_time'], format='%Y-%m-%dT%H:%M:%S.000Z')
        df.sort_values('date_time', inplace=True)
    except:
        return pd.DataFrame()
    return df

def get_data_bmo(token):
    #time_now = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
    #start_time = (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d')
    #start_time = '2021-10-22'
    
    
    try:
        
        db = remobs_db(os.getenv('HOST'), os.getenv('DB'), os.getenv('USR'), os.getenv('PSWD'))
        
        df = db.db_select(os.getenv("QUERY_ALL_DATA"))


    # url=f'http://remobsapi.herokuapp.com/api/v1/data_buoys?buoy=2&start_date={start_time}&end_date={time_now}&token={token}'

    # try:
    #     response = requests.get(url).json()
    #     df = pd.DataFrame(response)
    #     for i in df.columns:
    #         try:
    #             df[i] = pd.to_numeric(df[i])
    #         except:
    #             pass
    
        # for i in df.columns:
        #     try:
        #         df[i] = pd.to_numeric(df[i])
        #     except:
        #         pass

        #df['date_time'] = pd.to_datetime(df['date_time'], format='%Y-%m-%dT%H:%M:%S.000Z')
        df.sort_values('date_time', inplace=True)
    except:
        return pd.DataFrame()

    return df

def calculate_distance(df):
    coordinates = []
    for index, row in df.iterrows():
        coordinate = [row['lat'], row['lon']]
        coordinates.append(coordinate)


    deployment_loc = [-25.508, -42.736]
    df['coordinates'] = coordinates

    df['distance'] = df.apply(lambda row: haversine(row, deployment_loc[1], deployment_loc[0]), axis=1)

    df['veloc'] = df['distance'].diff()/(df['date_time'].diff().dt.total_seconds()/3600)

    return df

def plot_map(df):

    deployment_loc = [-25.508, -42.736]

    m = folium.Map(location=deployment_loc, zoom_start=9)

    for index, row in df.iterrows():
        popup = str(row['date_time']) + ' - veloc ' + str(round(row['veloc'],3)) + 'nós, LAT:' + str(round(row['lat'],4))  + ', LON:' + str(round(row['lon'],4))
        folium.Marker(row['coordinates'], tooltip=popup).add_to(m)

    folium.Marker(
        df['coordinates'].iloc[-1],
        tooltip=popup,
        icon=folium.Icon(icon_color="red", color='red')
    ).add_to(m)

    folium.Circle(deployment_loc, radius=1600).add_to(m)
    folium_static(m)


def df_time_interval(df):
    
    dt = datetime.now(timezone.utc)
    
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    
    df1 = df.copy()
    
    df1.sort_values(by="date_time", inplace=True)
    
    df1['Intervalo de Tempo | HORAS'] = np.round(((df1['date_time'].values.astype(np.int64) // 10 ** 9) - utc_timestamp)/3600,2)
    
    return df1


def meters_to_degree(meters_distance, latitude):
    """Considering distance of 1 degree lat/lon
    as 111.111 meters of distance...
    """


    lat_degrees = meters_distance/111111
    lon_degrees = meters_distance/(111111 * abs(math.cos(latitude)))

    return lat_degrees, lon_degrees

def safe_range_circle(lon_fundeio, lat_fundeio, radius):
    """Transform the Radius from lat/lon of mooring
    to a vector with 360 points locations in lat/lon,
    showing the limits of the buoy movement range."""

    import numpy as np

    pi = math.pi


    r, r_lon = meters_to_degree(radius, lat_fundeio)
    lat = math.radians(lat_fundeio)
    lon = math.radians(lon_fundeio)
    r_radians = math.radians(r)

    points = np.linspace(0, 2*pi, 360)



    circle_points = [(lat + math.sin(x)*r_radians,lon - math.cos(x)*r_radians) for x in points]

    # radians to degree

    circle_coords = [((x[1]*180/pi), (x[0]*180/pi)) for x in circle_points]
    circle_lat = [(x[0]*180/pi) for x in circle_points]
    circle_lon = [(x[1]*180/pi) for x in circle_points]

    return circle_coords, circle_lat, circle_lon

    
def plot_map_time(df, mapbox_token):
    
    deployment_loc = [-25.508, -42.736]
    
   # deployment_loc_df = pd.DataFrame(list(zip([deployment_loc[0]], [deployment_loc[1]])),
    #                                 columns =['lat', 'lon'])


    last_lat = float(df['lat'].iloc[-1])
    last_lon = float(df['lon'].iloc[-1])
    
    circle_coords, circle_lat, circle_lon = safe_range_circle(deployment_loc[1], deployment_loc[0], 1600)
    
    safe_range_df = pd.DataFrame({'lat':circle_lat,
                              'lon':circle_lon})
    
    fig = px.scatter_mapbox(df, lat="lat", lon="lon", color='Intervalo de Tempo | HORAS',
                  color_continuous_scale=["black", "purple", "red" ], size_max=30, zoom=8,
                  hover_data = {'lat':True, 'lon':True, 'date_time':True, 'Intervalo de Tempo | HORAS':True},
                  height = 700, width = 1100, #center = dict(lat = g.center)
                        title='Histórico | Tempo trajetória',
                        mapbox_style="open-street-map"
                       )
    
    fig.add_trace(go.Scattermapbox(
        lat=safe_range_df['lat'],
        lon=safe_range_df['lon'],
        mode='markers',
		#name='Watch Circle',
        marker=go.scattermapbox.Marker(
            size=2,
            color='blue',
            opacity=0.5
        ),
		text = 'none',
        hoverinfo='none',
        showlegend=False
    ))
    
    fig.add_trace(go.Scattermapbox(
        lat=[last_lat],
        lon=[last_lon],
        mode='markers',
		name = 'Posição Atual',
        marker=go.scattermapbox.Marker(
            size=28,
            color='rgb(255, 255, 0)',
			symbol = 'circle'
        ),
        showlegend=False
    ))
    
    fig.update_layout(font_size=16,  title={'xanchor': 'center','yanchor': 'top', 'y':0.9, 'x':0.5,}, 
        title_font_size = 24, mapbox_accesstoken=mapbox_token)

    fig.update_traces(marker=dict(size=12))
    
    
    
    return st.plotly_chart(fig)

if __name__ == "__main__":
    df = get_data()

    df = calculate_distance(df)
    
    plot_map(df)
    