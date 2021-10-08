# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:02:40 2020

@author: aiq7
"""

import streamlit as st
import pandas as pd
import numpy as np
import pandaspi as pdpi
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import requests

from datetime import datetime, timedelta

# DPROD = 21*(152-'P52_PDGP-1210009K')/0.159
# GANHO[%] = 100*(21*(152-'P52_PDGP-1210009K')/1300)
# GANHO[R$/DIA] = 21*(152-'P52_PDGP-1210009K')/0.159*55*4.3

st.title('Wellbot Monetary Gain')

date_base = st.date_input("Data base:",
                          datetime.now())

step_time = timedelta(days=eval(st.text_input('Range de tempo [dia(s)]:',
                                              '-15')
                                )
                      )

total_time = sorted([date_base, date_base + step_time])

datas = np.arange(total_time[0], total_time[1] + timedelta(days=1))

def get_cotation(data_lim_inf, data_lim_sup):
    """
    Gets from **awesomeapi** Dolar cotations and from
    **eia** Brent cotations.
    
    
    More on:
        * https://docs.awesomeapi.com.br/api-de-moedas
        * https://www.eia.gov/opendata/qb.php
    
    Parameters
    ----------
    data_lim_inf : Datetime
        Inferior limit to get Dolar cotation.
    data_lim_sup : Datetime
        Superior limit to get Dolar cotation.

    Returns
    -------
    DataFrame with pd.DatetimeIndex and Dolar bid and Brent price in each day

    """
    days = (data_lim_sup - data_lim_inf).days
    date_ranges = [data_lim_inf + timedelta(days=i*15) for i in range(days//15)]
    date_ranges.append(data_lim_sup)
    
    data = []
    bid = []
    for i in range(1, len(date_ranges)):
        # start_date=20180901&end_date=20180930
        q = 'start_date=' + date_ranges[i-1].strftime('%Y%m%d') \
           + '&end_date=' + date_ranges[i].strftime('%Y%m%d')
        
        # https://docs.awesomeapi.com.br/api-de-moedas
        try:
            req = requests.get('https://economia.awesomeapi.com.br/json/daily/USD-BRL/?'+q)
        except:
            st.write(f'Problema na coleta de dados entre:' \
                     + f' {date_ranges[i-1].strftime("%d/%m/%Y")} ' \
                     + f'- {date_ranges[i-1].strftime("%d/%m/%Y")}')
            continue
        cotacao = req.json()
        
        data += [datetime.fromtimestamp(int(cot_dia['timestamp'][0:10])) \
                 for cot_dia in cotacao]
        bid += [float(cot_dia['bid']) for cot_dia in cotacao]
    
    # Getting Brent price
    key = '04086e93c6722b32f3bc7264d14e4e6a'
    q = 'start=' + data_lim_inf.strftime('%Y%m%d') + '&end=' + data_lim_sup.strftime('%Y%m%d')
    requisicao = requests.get(f'http://api.eia.gov/series/?api_key={key}&series_id=PET.RBRTE.D&'+q)
    req = requisicao.json()
    # $/bbl
    brent = req['series'][0]['data']
    
    data2 = [datetime(int(par[0][0:4]), # year
                      int(par[0][4:6]), # month
                      int(par[0][6:])   # day
                      )
             for par in brent]
    brent = [par[1] for par in brent]
    
    
    # Build Exit
    data = np.array(data)
    data2 = np.array(data2)
    data_ind = np.arange(data_lim_inf, data_lim_sup)
    
    data_val = {'USD/BRL': [0]*(len(data_ind)-1),
                'USD/bbl': [0]*(len(data_ind)-1)}
    day = data_lim_inf
    
    ## day nunca está em datas
    
    for i in range(days):
        day += timedelta(days=i)
        print(i,datetime.isoweekday(day),day in data,data_val['USD/BRL'])
        if day in data:
            ind = data.index(day)
            data_val['USD/BRL'][i] = bid[ind]
        else:
            if day == data_lim_inf:
                if datetime.isoweekday(day) == 6:
                    data_val['USD/BRL'][i] = bid[2]
                else:
                    data_val['USD/BRL'][i] = bid[1]
            else:
                data_val['USD/BRL'][i] = data_val['USD/BRL'][i-1]
        
        if day in data2:
            ind = data.index(day)
            data_val['USD/bbl'][i] = brent[ind]
        else:
            if day == data_lim_inf:
                if datetime.isoweekday(day) == 6:
                    data_val['USD/bbl'][i] = brent[2]
                else:
                    data_val['USD/bbl'][i] = brent[1]
            else:
                data_val['USD/bbl'][i] = data_val['USD/bbl'][i-1]
        
    
    # Create final Dataframe
    df = pd.DataFrame(data_val, index=data_ind)
    df.sort_index(inplace=True)
    
    return df

df = get_cotation(total_time[0], total_time[1])

st.line_chart(df)

ax = plt.subplot(211)
plot = plt.plot(list(dados.keys()),list(dados.values()),'--bx')
ax.set_ylabel('USD/BRL',color='b')
ax.tick_params(axis='y', labelcolor='b')


# https://data.opendatasoft.com/api/v2/console
# https://www.eia.gov/opendata/
# EIA API key = 04086e93c6722b32f3bc7264d14e4e6a
key = '04086e93c6722b32f3bc7264d14e4e6a'
q = 'start=' + total_time[0].strftime('%Y%m%d') + '&end=' + total_time[1].strftime('%Y%m%d')
requisicao = requests.get(f'http://api.eia.gov/series/?api_key={key}&series_id=PET.RBRTE.D&'+q)
brent = requisicao.json()
# $/bbl
brent = brent['series'][0]['data']
# print(brent)

dados = {datetime(int(par[0][0:4]), # year
                  int(par[0][4:6]), # month
                  int(par[0][6:])   # day
                  ):
         par[1] for par in brent
         }
ax2 = ax.twinx()
ax2.plot(list(dados.keys()),list(dados.values()),'--rx')
ax2.set_ylabel('USD/bbl',color='r')
ax2.tick_params(axis='y', labelcolor='r')


ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=range(5,32,5)))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m\n%Y'))
ax.xaxis.set_minor_locator(mdates.DayLocator())
plt.show()
st.pyplot()


def complete_data(df,method):
    '''
    
    More: https://pandas.pydata.org/pandas-docs/stable/user_guide/missing_data.html
    
    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    method : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    return None