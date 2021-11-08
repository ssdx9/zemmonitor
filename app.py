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
import pandas as pd
import locale

# Локализация 
locale.setlocale(locale.LC_ALL, "ru") 

# Блок необходимый для gunicorn
app = dash.Dash(__name__)
server = app.server
mapbox_token = os.environ.get('mapbox_token') # из переменной среды
# mapbox_token = open(".mapbox_token").read() # локально

app.title = "Монитор землетрясений"

sht=8 # переменная смещения времени

# Парсинг данных со старого сайта
url = "http://seis-bykl.ru/index.php?ma=1"
try:
    r = requests.get(url) 
    r.encoding = r.apparent_encoding # проверка содержимого на кодировку и переключение на неё
    soup = BeautifulSoup(r.text, "html.parser") # создаем whole-doc-объект soup 
except requests.exceptions.ConnectionError as error: # подавление exception в случае недоступности url
    print("Can't complete request! Message: ", error)
    pass

# Скрапинг через marker hovers:
try:
    areas = soup.map.find_all('area')  # достаем всё содержимое по тегу area
except Exception:
    areas = [] # в случае отсутствия тега map (пустая страница) подменяем данные на None 
df={'date':[],'time':[],'lat':[],'lon':[],'K':[],'Ks':[], 'affect':[], 'op':[]} # заготовка словаря под датафрейм
for area in areas: 
    gottitle = area['title'] #находим string title (это не attr!)
    df['date'].extend(re.findall(r"\d{4}-\d{2}-\d{2}", gottitle))
    df['time'].extend(re.findall(r"\d{2}:\d{2}:\d{2}", gottitle))
    coords = re.findall(r"\b\d{2,}[.]\d{2,}\b", gottitle)
    df['lat'].append(coords[0])
    df['lon'].append(coords[1])        
    K = re.findall(r"\d{1,2}[.|,]\d{1}\b", gottitle) # распознание K
    K = K[0].replace(",",".") # защита от ошибки ввода через запятую
    df['K'].append(float(K))
    Ks = int(((float(K)-8.6)**2)*10000) # подбираем размерность для size    
    NN = []
    NN.append(Ks)    
    df['Ks'].extend(NN) # Ks нужен для регулировки размеров для scattermapbox, потому что size только int и str(?)
    ll = []
    ll = re.findall(r"[А-Яа-я].+$", gottitle) 
    ll.extend([' ']) # кроме добавления значения в список (оно может быть none) добавляем еще пробел, чтобы хоть что-нибудь было
    ls = ["".join(ll)] # таким образом будет либо пробел, либо значение с пробелом - и list будет сохранять необходимую размерность
    df['affect'].extend(ls)     


""" # Динамичный opacity для старых событий
op = 1 # стартовое значение opacity для снижения
for n in range(10):
    op = round(op-0.07, 2)
    df['op'].append(op) # подготовленный набор значений opacity
 """

# Отрисовка пустой карты
fig=px.scatter_mapbox(
    center={'lat':54,'lon':108},   
    zoom=4.7,
    # mapbox_style="stamen-terrain",
    ) 
fig.update_layout(mapbox_style="satellite", mapbox_accesstoken=mapbox_token)

# Слой населенных пунктов
dfcities = pd.read_excel("cities.xls")
for l in range(len(dfcities)-1,-1,-1): # обратное нанесение, чтобы начальные пункты оказались поверх
    fig.add_trace(go.Scattermapbox(
        lat=[dfcities['lat'][l]],
        lon=[dfcities['lon'][l]],
        mode='markers+text',
        text=dfcities['name'][l],
        textposition="top center",
        textfont=dict(
            family="sans serif",
            size=dfcities['sign'][l],
            color="white"
        ),
        hoverinfo='none', showlegend=False,
        marker=go.scattermapbox.Marker(size=dfcities['sign'][l], color='#242424', opacity=1),
    ))

if df['date'] != []: # проверка на непустой dataframe
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
            mode='markers',
            text=textif,
            hoverinfo=('text'),
            hoverlabel={'bgcolor':('black' if i!=0 else 'yellow'), },  # выделенный цвет только для последнего события       
            marker=go.scattermapbox.Marker(size=((float(df['K'][i])-8)*15), # регулировка размера для go.scattermabpox - нужно сделать логарифмически
                                            color=('red' if i!=0 else 'yellow' ), 
                                            # opacity=df['op'][i]), # динамичный opacity
                                            opacity=(0.5 if i!=0 else 0.9),), # статичный opacity  
            # блок нужно оптимизировать        
            name=('Сегодня' if tddt.date()==dfdt.date() else (str(dfdt.day)+str(dfdt.strftime("%b"))) and 'Вчера' if tddt.date()-timedelta(days=1)==dfdt.date() else (str(dfdt.day)+ " " +str(dfdt.strftime("%b")))) + " "  
                    + str(dfdt.strftime("%X")) + " "
                    + " Класс: " 
                    + str(df['K'][i]) + " ",
        ))
else: # обработка exception (отсутствие нормальных входящих данных)
    fig.add_annotation(xref="paper", yref="paper",
                x=0.2, y=0.45,
                showarrow=False,
                text = 'Отсутствуют данные на источнике',                
                font=dict(family="Arial", size=40, color="#ffffff"),
                align="left",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="#000000",
                opacity=1,
                xanchor='left',
                yanchor='bottom',
                )

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
    font=dict(family="Arial", size=14, color="#ffffff"), #шрифт в легенде    
    legend=dict(
    yanchor="top",
    y=0.92,
    xanchor="left",
    x=0.01),   
    legend_traceorder="reversed",
    )

# строка про местное время
fig.add_annotation(xref="paper", yref="paper",
            x=0.01, y=0.92,
            showarrow=False,
            text = 'По местному времени Иркутска и Улан-Удэ (GMT+8):',
            font=dict(family="Arial", size=14, color="#ffffff"),
            align="left",
            borderpad=4,
            bgcolor="#000000",
            opacity=1.0,
            xanchor='left',
            yanchor='bottom',
            )

# макет страницы; требуется добавление стиля css (отдельный файл в директории) для настройки общего фона страницы в браузере
app.layout = html.Div(
    style={'backgroundColor': colors['background']}, children=[
    html.H1(children='Монитор сейсмической активности на Байкале',
        style={'textAlign': 'center', 'color': colors['text']}), 
    html.Div(children=['Данный сайт не является официальным источником информации. Официальная информация геофизической службы представлена по адресу: ', html.A('seis-bykl.ru', href='http://seis-bykl.ru/index.php', target='_blank')], 
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