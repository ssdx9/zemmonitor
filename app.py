#zemmonitor dash 1
import plotly.express as px
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import dash
import dash_core_components as dcc
import dash_html_components as html


url = "http://seis-bykl.ru/index.php?ma=1"
r = requests.get(url)
r.encoding = r.apparent_encoding # проверка содержимого на кодировку и переключение на неё
soup = BeautifulSoup(r.text, "html.parser") # создаем whole-doc-объект soup

# Скрапинг через ховеры:
areas = soup.map.find_all('area') # достаем всё содержимое по тегу area
df={'date':[],'time':[],'lat':[],'lon':[],'K':[], 'affect':[]} # заготовка словаря под датафрейм
for area in areas: #в каждом элементе списка    
    gottitle = area['title'] #находим string title (это не attr!)
    df['date'].extend(re.findall(r"\d{4}-\d{2}-\d{2}", gottitle))
    df['time'].extend(re.findall(r"\d{2}:\d{2}:\d{2}", gottitle))
    df['lat'].extend(re.findall(r"\b\d{2}[.]\d{2}", gottitle))
    df['lon'].extend(re.findall(r"\b\d{3}[.]\d{2}", gottitle))    
    KK = re.findall(r"\d{1,2}[.]\d{1}\b", gottitle) # получаем K    
    KK = int(((float(KK[0])-8.6)**2)*10000) # подбираем размерность для size    
    NN = []
    NN.append(KK)    
    df['K'].extend(NN)
    ll = []
    ll = re.findall(r"[А-Яа-я].+$", gottitle) # из-за того, что size только int и str
    ll.extend([' '])
    ls = ["".join(ll)]
    df['affect'].extend(ls)     

fig=px.scatter_mapbox(df, 
    lat='lat', lon='lon',
    size='K', 
    size_max=60,
    # color='K', 
    color_discrete_sequence=["red"],
    opacity=0.5,
    center={'lat':54,'lon':109},   
    zoom=5,
    hover_name='affect',
    # mapbox_style="open-street-map",
    mapbox_style="stamen-terrain",
    title='Карта эпицентров последних десяти землетрясений'
    )  

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig,
        style={'height': 700
        }),    
])


if __name__ == '__main__':
    app.run_server(debug=True)