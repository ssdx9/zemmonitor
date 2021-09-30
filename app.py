#zemmonitor dash 1
import plotly.express as px
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import dash
from dash import dcc
from dash import html

app = dash.Dash(__name__)
server = app.server

url = "http://seis-bykl.ru/index.php?ma=1"
r = requests.get(url)
r.encoding = r.apparent_encoding # проверка содержимого на кодировку и переключение на неё
soup = BeautifulSoup(r.text, "html.parser") # создаем whole-doc-объект soup

# Скрапинг через ховеры:
areas = soup.map.find_all('area') # достаем всё содержимое по тегу area
df={'Дата':[],'Время':[],'lat':[],'lon':[],'Класс':[],'Ks':[], 'affect':[]} # заготовка словаря под датафрейм
for area in areas: #в каждом элементе списка    
    gottitle = area['title'] #находим string title (это не attr!)
    df['Дата'].extend(re.findall(r"\d{4}-\d{2}-\d{2}", gottitle))
    df['Время'].extend(re.findall(r"\d{2}:\d{2}:\d{2}", gottitle))
    df['lat'].extend(re.findall(r"\b\d{2}[.]\d{2}", gottitle))
    df['lon'].extend(re.findall(r"\b\d{3}[.]\d{2}", gottitle))
    df['Класс'].extend(re.findall(r"\d{1,2}[.]\d{1}\b", gottitle))   
    Ks = re.findall(r"\d{1,2}[.]\d{1}\b", gottitle) # получаем K
    Ks = int(((float(Ks[0])-8.6)**2)*10000) # подбираем размерность для size    
    NN = []
    NN.append(Ks)    
    df['Ks'].extend(NN)
    ll = []
    ll = re.findall(r"[А-Яа-я].+$", gottitle) # из-за того, что size только int и str
    ll.extend([' '])
    ls = ["".join(ll)]
    df['affect'].extend(ls)     

fig=px.scatter_mapbox(df, 
    lat='lat', lon='lon',
    size='Ks', 
    size_max=60,
    # color='K', 
    color_discrete_sequence=["red"],
    opacity=0.5,
    center={'lat':54,'lon':109},   
    zoom=5,
    hover_name='affect',
    hover_data={'lat' : False, 'lon' : False, 'Ks' : False, 
                'Дата' : True, 'Время' : True, 'Класс' : True},    
    # mapbox_style="open-street-map",
    mapbox_style="stamen-terrain",
    )  

n=0
annx=0.01
anny=0.93
op=0.9
for n in range(10):    
    fig.add_annotation(xref="paper", yref="paper",
                x=annx, y=anny,
                showarrow=False,                
                text = df['Дата'][n] + " " + df['Время'][n] + " Класс: " + df['Класс'][n] + " " + df['affect'][n],
                font=dict(family="Arial",
                    size=14,
                    color="#ffffff"),
                align="left",
                # bordercolor="#c7c7c7",
                # borderwidth=2,
                borderpad=4,
                bgcolor="#000000",
                # bgcolor="#808080",
                opacity=op,
                xanchor='left',
                yanchor='bottom',
                )
    anny=round(anny-0.05,2)
    op=round(op-0.05,2)

    
colors = {'background': '#111111','text': '#7FDBFF'}

fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    margin=dict(t=20, b=20, l=20, r=20),
)

# dcc.Graph(figure=fig)
app.layout = html.Div(
    style={'backgroundColor': colors['background']}, children=[
    html.H1(children='Монитор сейсмической активности на Байкале',
        style={'textAlign': 'center', 'color': colors['text']}), 
    html.Div(children='Последние десять землетрясений', 
        style={'textAlign': 'center', 'color': colors['text']}),

    dcc.Graph(figure=fig,
    style = dict(height = 600),
    # responsive=True,
    # style={"min-height":"0","flex-grow":"1"},    
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)