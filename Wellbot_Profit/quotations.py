# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 17:02:31 2020.

@author: aiq7
"""

__author__ = 'Rafael Mendes Matos'
__all__ = ['get_bid', 'get_brent']


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests
import os

from datetime import datetime, timedelta, date
import tkinter as tk


proxy = False

def _set_proxy():
    """
    Configure proxy to get data from internet.

    More in:
        https://realpython.com/python-gui-tkinter/

    Returns
    -------
    dict
        Proxy solving tags.

    """
    def close():
        app.destroy()

    user = os.getlogin()

    """
    Tk(screenName=None, baseName=None,
       className='Tk', useTk=1, sync=0, use=None)
    """
    app = tk.Tk()
    app.title('Login')
    """
    Frame(master=None, cnf={}, **kw):
        background, bd, bg, borderwidth, class,
        colormap, container, cursor, height, highlightbackground,
        highlightcolor, highlightthickness, relief, takefocus, visual,
        width."""
    f1 = tk.Frame(background='white', height='10m', width='10m')

    """
    StringVar(master=None, value=None, name=None)
    """
    password = tk.StringVar(master=f1)
    """
    Label(master=None, cnf={}, **kw):
        activebackground, activeforeground, anchor,
        background, bitmap, borderwidth, cursor,
        disabledforeground, font, foreground,
        highlightbackground, highlightcolor,
        highlightthickness, image, justify,
        padx, pady, relief, takefocus, text,
        textvariable, underline, wraplength
    """
    label0 = tk.Label(master=f1,
                      text='Para configuração do proxy, é necessário coletar' +
                      'a senha do usuário.\n Tenha certeza de que está ' +
                      'conectado ao VPN/Pulse',
                      bg='white',
                      fg='red',
                      pady=3)
    """
    pack_configure(self, cnf={}, **kw):
        after = widget - pack it after you have packed widget
        anchor = NSEW (or subset) - position widget according 2 given direction
        before = widget - pack it before you will pack widget
        expand = bool - expand widget if parent size grows
        fill = [None, 'x', 'y', 'both'] - fill widget if widget grows
        in = master - use master to contain this widget
        in_ = master - see 'in' option description
        ipadx = amount - add internal padding in x direction
        ipady = amount - add internal padding in y direction
        padx = amount - add padding in x direction
        pady = amount - add padding in y direction
        side = TOP or BOTTOM or LEFT or RIGHT -  where to add this widget.
    """
    label0.pack(expand=True, fill= 'both')

    label1 = tk.Label(master=f1, text=f'Entre com a senha do usuário {user}:')
    label1.pack(expand=True, fill='both')

    passEntry = tk.Entry(master=f1, textvariable=password, show='*')
    passEntry.pack(expand=True, fill= 'both')

    f1.pack(expand=True, fill= 'both')

    submit = tk.Button(app, text='Ok', command=close)
    submit.pack()

    app.focus_force()
    app.mainloop()

    out = password.get()

    url = 'inet-sys.petrobras.com.br:804'

    os.environ["HTTP_PROXY"] = f"http://{user}:{out}@{url}"
    os.environ["HTTPS_PROXY"] = f"https://{user}:{out}@{url}"
    proxy = True

def get_from_bd(bid_or_brent: str, date_begin: datetime, date_end: datetime):
    path = os.path.split(__file__)[0] + './bd/' + bid_or_brent
    file1 = "%4d.%02d.csv"%(date_begin.year, date_begin.month)
    file2 = "%4d.%02d.csv"%(date_end.year, date_end.month)
    
    out = False
    if file1 == file2:
        if os.path.exists(os.path.join(path, file1)):
            df = pd.read_csv(os.path.join(path, file1))
    else:
        if os.path.exists(os.path.join(path, file1)):
            df_begin = pd.read_csv(os.path.join(path, file1))
        if os.path.exists(os.path.join(path, file2)):
            df_end = pd.read_csv(os.path.join(path, file2))

def get_bid(date_begin: datetime, date_end: datetime):
    """
    Get Dolar cotations from **awesomeapi**.

    More on:
        * https://docs.awesomeapi.com.br/api-de-moedas

    Parameters
    ----------
    data_lim_inf : Datetime
        Inferior limit to get Dolar quotation.
    data_lim_sup : Datetime
        Superior limit to get Dolar quotation.

    Returns
    -------
    Pandas Series
        pandas.DatetimeIndex, Dolar bid.

    """
    # Initial validation
    if not isinstance(date_begin, (datetime, date)):
        raise TypeError('Data de início não é do tipo "datetime".')
    if not isinstance(date_end, (datetime, date)):
        raise TypeError('Data dinal não é do tipo "datetime".')
    date_begin, date_end = sorted([date_begin, date_end])

    link = r'https://economia.awesomeapi.com.br/json/daily/USD-BRL/?'
    
    try:
        requests.get('http://www.google.com.br')
    except (requests.adapters.ProxyError,
            requests.adapters.ConnectTimeout,
            requests.adapters.ConnectionError):
        _set_proxy()
    except Exception as e:
        print(e)
        _set_proxy()
    

    # Finds the first date with data
    d1 = date_begin
    diff = 0  # days to go back
    while True:
        d0 = d1 - timedelta(days=diff)
        # Monta a query
        query = 'start_date=' + d0.strftime('%Y%m%d') \
                + '&end_date=' + d1.strftime('%Y%m%d')

        session = requests.Session()
#         session.proxies = proxies
        req = session.get(link + query)

        # No response:
        if req.status_code != 200:
            raise ConnectionError('Dolar: Servidor sem resposta.')
        # Sets initial date if found data
        if len(req.json()) > 0:
            quo_0 = req.json()[0]
            d0 = datetime.fromtimestamp(int(quo_0['timestamp'][0:10])).date()
            break
        # Other case goes back in time one day
        diff += 1

    # split on 15 days to solve problems with API
    delta_d = timedelta(days=15)
    date_ranges = np.append(np.arange(d0, date_end, delta_d), date_end)

    bid = dict()
    for i in range(1, len(date_ranges)):
        # Example: start_date=20180901&end_date=20180930
        q = 'start_date=' + date_ranges[i-1].strftime('%Y%m%d') \
           + '&end_date=' + date_ranges[i].strftime('%Y%m%d')

        # https://docs.awesomeapi.com.br/api-de-moedas

        try:
            req = requests.get(link + q)

        except Exception as e:
            print('Problema na coleta de dados entre:',
                  f'{date_ranges[i-1].strftime("%d/%m/%Y")}',
                  f'- {date_ranges[i-1].strftime("%d/%m/%Y")}',
                  '\nErro:', e)
            continue
        quo = req.json()

        date_dict = dict()
        for day_quo in quo:
            date0 = datetime.fromtimestamp(int(day_quo['timestamp'][0:10]))
            # If there is any most recent quotation, skip this one
            if date0.date() in date_dict and date0 <= date_dict[date0.date()]:
                continue
            date_dict[date0.date()] = date0

            bid[date0.date()] = float(day_quo['bid'])

    s1 = pd.Series(bid)
    s1 = s1.reindex(pd.date_range(d0, date_end, freq='D'))
    s1 = s1.ffill()
    s1 = s1.reindex(pd.date_range(date_begin, date_end, freq='D'))

    return s1


def get_brent(date_begin: datetime, date_end: datetime,
              key='04086e93c6722b32f3bc7264d14e4e6a'):
    """
    Getting Brent cotations from **eia**.

    More on:
        * https://www.eia.gov/opendata/qb.php

    Parameters
    ----------
    date_begin : Datetime
        Inferior limit to get Dolar cotation.
    date_end : Datetime
        Superior limit to get Dolar cotation.
    key : str
        Key gotten on **eia** site.

    Returns
    -------
    Pandas Series
        Series with repeated values when None found.

    """
    # Initial validation
    if not isinstance(date_begin, (datetime, date)):
        raise TypeError('Data de início não é do tipo "datetime".')
    if not isinstance(date_end, (datetime, date)):
        raise TypeError('Data dinal não é do tipo "datetime".')
    date_begin, date_end = sorted([date_begin, date_end])

    link = f'http://api.eia.gov/series/?api_key={key}&series_id=PET.RBRTE.D&'
    proxies = dict()
    try:
        requests.get('http://google.com')
    except requests.adapters.ProxyError:
        proxies = _set_proxy()

    # Finds the first date with data
    d1 = date_begin
    diff = 0  # days to go back
    while True:
        d0 = d1 - timedelta(days=diff)
        # Builds the query
        query = 'start=' + d0.strftime('%Y%m%d') + \
                '&end=' + d1.strftime('%Y%m%d')

        session = requests.Session()
        session.proxies = proxies
        req = session.get(link + query)

        # No response:
        if req.status_code != 200:
            raise ConnectionError('Brent: Servidor sem resposta.')
        # Sets initial date if found data
        data = req.json()['series'][0]['data']
        if len(data) > 0:
            d0 = pd.to_datetime(data[0][0]).date()
            break
        # Other case goes back in time one day
        diff += 1

    # Building complete query
    query = 'start=' + d0.strftime('%Y%m%d') + \
            '&end=' + date_end.strftime('%Y%m%d')

    req = requests.get(link + query)

    req = req.json()
    # quo = ['yyyymmdd', $/bbl]
    quo = req['series'][0]['data']

    s1 = pd.Series({pd.to_datetime(i).date(): j for i, j in quo})
    s1 = s1.reindex(pd.date_range(d0, date_end, freq='D'))
    s1 = s1.ffill()
    s1 = s1.reindex(pd.date_range(date_begin, date_end, freq='D'))

    return s1


if __name__ == "__main__":
    # start time
    date_base = datetime.now().date()
    date_base = datetime.fromisoformat(date_base.isoformat())
    # time delta
    step_time = timedelta(days=-5)
    # time range
    total_time = sorted([date_base, date_base + step_time])

    plt.subplot(211)
    s1 = get_bid(total_time[0], total_time[1])

    ax1 = s1.plot(color='black', marker='x', linestyle='--')
    plt.legend(['USD'])
    ax1.get_xaxis().set_visible(False)

    plt.subplot(212)
    s2 = get_brent(total_time[0], total_time[1])
    s2.plot(color='black', marker='o', linestyle='--')
    plt.legend(['Brent'])

    plt.show()
