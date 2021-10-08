#zemmonitor dash for heroku
import plotly.express as px
from bs4 import BeautifulSoup
import requests
import re
import dash
from dash import dcc
from dash import html
from datetime import datetime, timedelta
import plotly.graph_objs as go
import os

# Блок необходимый для gunicorn
app = dash.Dash(__name__)
server = app.server
mapbox_token = os.environ.get('mapbox_token')

sht=8 # переменная смещения времени

# Парсинг данных со старого сайта
url = "http://seis-bykl.ru/index.php?ma=1"
r = requests.get(url)
r.encoding = r.apparent_encoding # проверка содержимого на кодировку и переключение на неё
soup = BeautifulSoup(r.text, "html.parser") # создаем whole-doc-объект soup

# Скрапинг через marker hovers:
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
    df['Ks'].extend(NN) # Ks нужен для регулировки размеров для scattermapbox, потому что size только int и str(?)
    ll = []
    ll = re.findall(r"[А-Яа-я].+$", gottitle) 
    ll.extend([' ']) # кроме добавления значения в список (оно может быть none) добавляем еще пробел, чтобы хоть что-нибудь было
    ls = ["".join(ll)] # таким образом будет либо пробел, либо значение с пробелом - и list будет сохранять необходимую размерность
    df['affect'].extend(ls)     

# Отрисовка пустой карты
fig=px.scatter_mapbox(
    center={'lat':54,'lon':109},   
    zoom=5,
    # mapbox_style="stamen-terrain",
    ) 

fig.update_layout(mapbox_style="satellite", mapbox_accesstoken=mapbox_token)

# Поочередное нанесение отдельного маркера с отдельной легендой
for i in range(9,-1,-1): # в обратном порядке для того, чтобы последнее событие было на сверху (помещено на plot последним)
    dfdt=datetime.strptime((str(df['date'][i]) + ',' + str(df['time'][i])), "%Y-%m-%d,%H:%M:%S") # расшифровка в формат datetime
    dfdt=dfdt+timedelta(hours=sht) # смещение для проверки местной текущей даты
    tddt=datetime.today()+timedelta(hours=sht) # переменная текущей даты
    if i==0: # содержимое hover для последнего события (лучше переделать в template)
        textif='Последнее землетрясение<br>Дата и время местные: {} <br>Дата и время по Гринвичу: {} <br>Энергетический класс: {} <br>Координаты: {} {}<br>Затронутые населенные пункты: {}'.format(
            (str(dfdt.date()) + ' ' + str(dfdt.strftime("%X"))), # местное
            (df['date'][i] + ' ' + df['time'][i]), # Гринвич
            df['K'][i],df['lat'][i],df['lon'][i],
            (df['affect'][i] if df['affect'][i] != ' ' else 'нет данных') ),
    else: # содержимое hover для остальных событий
        textif='Дата и время местные: {} <br>Дата и время по Гринвичу: {} <br>Энергетический класс: {} <br>Координаты: {} {}<br>Затронутые населенные пункты: {}'.format(
            (str(dfdt.date()) + ' ' + str(dfdt.strftime("%X"))), # местное
            (df['date'][i] + ' ' + df['time'][i]), # Гринвич
            df['K'][i],df['lat'][i],df['lon'][i],
            (df['affect'][i] if df['affect'][i] != ' ' else 'нет данных') ), 
    fig.add_trace(go.Scattermapbox(
        lat=[df['lat'][i]],
        lon=[df['lon'][i]],
        mode='markers+text',
        text=textif,
        hoverinfo=('text'),
        hoverlabel={'bgcolor':('black' if i!=0 else 'yellow'), },  # выделенный цвет только для последнего события       
        marker=go.scattermapbox.Marker(size=((float(df['K'][i])-8)*20), # регулировка размера для go.scattermabpox
                                        color=('red' if i!=0 else 'yellow' ), 
                                        opacity=(0.5 if i!=0 else 0.9),),
        # блок нужно оптимизировать        
        name=('Сегодня' if tddt.date()==dfdt.date() else (str(dfdt.day)+str(dfdt.strftime("%b"))) and 'Вчера' if tddt.date()-timedelta(days=1)==dfdt.date() else (str(dfdt.day)+ " " +str(dfdt.strftime("%b")))) + " "  
                + str(dfdt.strftime("%X")) + " "
                + " Класс: " 
                + df['K'][i] + " ",
    ))


# переменные цвета
colors = {
    'background': '#111111',
    # 'background': '#708090',
    'text': '#A9A9A9',
    # 'text': '#C0C0C0',
}

# для учета глобальных против локальных переменных сначала настройка страницы
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text'],
    margin=dict(t=20, b=20, l=20, r=20), # отступ нужно сохранять для прокрутки экрана в мобильной версии в горизонтальной ориентации
)

# затем настройка элементов
# настройки легенды
fig.update_layout(
    legend_itemclick="toggleothers", legend_itemdoubleclick="toggle",
    legend_bgcolor="#000000", 
    font=dict(family="Arial", size=14, color="#ffffff"), 
    legend=dict(
        yanchor="top", y=0.99,
        xanchor="left", x=0.01),   
    legend_traceorder="reversed", # обратный порядок, чтобы последнее размещаемое (поверх) событие было первым в легенде (как самое актуальное)
    )

# макет страницы; требуется добавление стиля css (отдельный файл в директории) для настройки общего фона страницы в браузере
app.layout = html.Div(
    style={'backgroundColor': colors['background']}, children=[
    html.H1(children='Монитор сейсмической активности на Байкале',
        style={'textAlign': 'center', 'color': colors['text']}), 
    html.Div(children='Сайт находится в режиме разработки', 
        style={'textAlign': 'center', 'color': colors['text']}),

    dcc.Graph(figure=fig,
    style = dict(height = 600), # найти средство автоподгонки высоты к высоте видимого экрана
    )
])

""" # Время сервера
fig.add_annotation(xref="paper", yref="paper",
            x=0, y=0,
            showarrow=False,
            text = 'Текущее время сервера: ' + str(datetime.today()),
            font=dict(family="Arial",
                size=12,
                color="#ffffff"),
            align="left",
            borderpad=4,
            bgcolor="blue",
            opacity=0.8,
            xanchor='left',
            yanchor='bottom',
            ) """


if __name__ == '__main__': # необходимо для heroku
    app.run_server(debug=True) # необходимо для dash