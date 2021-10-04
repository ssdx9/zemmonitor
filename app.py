#zemmonitor dash 1
import plotly.express as px
from bs4 import BeautifulSoup
import requests
import re
import dash
from dash import dcc
from dash import html
from datetime import datetime, timedelta
import plotly.graph_objs as go

app = dash.Dash(__name__)
server = app.server

url = "http://seis-bykl.ru/index.php?ma=1"
r = requests.get(url)
r.encoding = r.apparent_encoding # проверка содержимого на кодировку и переключение на неё
soup = BeautifulSoup(r.text, "html.parser") # создаем whole-doc-объект soup

# Скрапинг через ховеры:
areas = soup.map.find_all('area') # достаем всё содержимое по тегу area
df={'date':[],'time':[],'lat':[],'lon':[],'K':[],'Ks':[], 'affect':[]} # заготовка словаря под датафрейм
for area in areas: #в каждом элементе списка    
    gottitle = area['title'] #находим string title (это не attr!)
    df['date'].extend(re.findall(r"\d{4}-\d{2}-\d{2}", gottitle))
    df['time'].extend(re.findall(r"\d{2}:\d{2}:\d{2}", gottitle))
    df['lat'].extend(re.findall(r"\b\d{2}[.]\d{2}", gottitle))
    df['lon'].extend(re.findall(r"\b\d{3}[.]\d{2}", gottitle))
    df['K'].extend(re.findall(r"\d{1,2}[.]\d{1}\b", gottitle))   
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

fig=px.scatter_mapbox(
    center={'lat':54,'lon':109},   
    zoom=5,
    mapbox_style="stamen-terrain",
    ) 

for i in range(9,-1,-1):
    dfdatetime=datetime.strptime((str(df['date'][i]) + ',' + str(df['time'][i])), "%Y-%m-%d,%H:%M:%S") 
    dfdatetime=dfdatetime+timedelta(hours=8)
    if i==0:
        textif='Последнее землетрясение<br>Дата: {} <br>Время: {} <br>Энергетический класс: {} <br>Координаты: {} {}<br>Затронутые населенные пункты: {}'.format(
            df['date'][i],df['time'][i],df['K'][i],df['lat'][i],df['lon'][i],
            (df['affect'][i] if df['affect'][i] != ' ' else 'нет данных') ),
    else:
        textif='Дата: {} <br>Время: {} <br>Энергетический класс: {} <br>Координаты: {} {}<br>Затронутые населенные пункты: {}'.format(
            df['date'][i],df['time'][i],df['K'][i],df['lat'][i],df['lon'][i],
            (df['affect'][i] if df['affect'][i] != ' ' else 'нет данных') ), 
    fig.add_trace(go.Scattermapbox(
        lat=[df['lat'][i]],
        lon=[df['lon'][i]],
        mode='markers',
        text=textif,
        # hoverinfo=('text' if i!=0 else 'none'),
        hoverinfo=('text'),
        hoverlabel={'bgcolor':('black' if i!=0 else 'yellow'), },
        # marker=go.scattermapbox.Marker(size=((float(df['K'][i])-9)*30), color='red', opacity=0.5,),
        marker=go.scattermapbox.Marker(size=((float(df['K'][i])-8)*20), color=('red' if i!=0 else 'yellow' ), opacity=(0.5 if i!=0 else 0.9),),        
        name= str(dfdatetime.day) + " "  
                + str(dfdatetime.strftime("%b")) + " "
                + str(dfdatetime.strftime("%X")) + " "
                + " Класс: " 
                + df['K'][i] + " ",
))


colors = {
    'background': '#111111',
    # 'background': '#708090',
    'text': '#A9A9A9',
    # 'text': '#C0C0C0',
}

fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    margin=dict(t=20, b=20, l=20, r=20),
)

fig.update_layout(
    legend_itemclick="toggleothers", legend_itemdoubleclick="toggle",
    legend_bgcolor="#000000", 
    font=dict(family="Arial", size=14, color="#ffffff"), #шрифт в легенде    
    legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=0.01),   
    legend_traceorder="reversed",
    )

app.layout = html.Div(
    style={'backgroundColor': colors['background']}, children=[
    html.H1(children='Монитор сейсмической активности на Байкале',
        style={'textAlign': 'center', 'color': colors['text']}), 
    html.Div(children='Сайт находится в режиме разработки', 
        style={'textAlign': 'center', 'color': colors['text']}),

    dcc.Graph(figure=fig,
    style = dict(height = 600),
    # responsive=True,
    # style={"min-height":"0","flex-grow":"1"},    
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)