# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 10:35:13 2020.

@author: Rafael Matos - aiq7
"""
import clr
clr.AddReference('OSIsoft.AFSDK')

import pandas as pd
import numpy as np
import pandaspi as pdpi
import matplotlib.pyplot as plt

from quotations import get_bid, get_brent
from datetime import datetime, timedelta

__version__ = 0.2
__author__ = "aiq7"

def prod_inc(tag_cv, tag_stat, pi_server,
             p_ref, ip, prod_test_m3d,
             date_range, sample_sec=60,
             bsw=0, shut_opt=None, choice="PDG"):

    m3d_to_bpd = lambda value: value/0.159
    sec_to_day = lambda sec: sec/24/60/60

    # extracting shut_opt
    shut_pdgp = False
    shut_stat = False
    shut = False
    if shut_opt is not None:
        shut = True
        tag_shut = shut_opt['tag']
        val_shut = shut_opt['val']
        opt_shut = shut_opt['compare']
        if tag_shut == tag_cv:
            shut_pdgp = True
        if tag_shut == tag_stat:
            shut_stat = True
    
    
    # Changing units
    prod_test_bpd = m3d_to_bpd(prod_test_m3d)
    sample_day = sec_to_day(sample_sec)

    # Variable checkup
    date_range = tuple(sorted(date_range))
    time_range = (f'{date_range[0]}', f'{date_range[1]}')

    # Get PI data
    tags = dict()
    if shut_pdgp or shut_stat or not shut:
        tag_list = [tag_cv, tag_stat]
    else:
        tag_list = [tag_cv, tag_stat, tag_shut]
    
    for tag in tag_list:
        server, tag = tag.split('\\')
        if server in tags:
            tags[server].append(tag)
        else:
            tags[server] = [tag]

    ## Recovering only TAGs, without servers
    tag_cv, tag_stat, tag_shut = map(lambda s: s.split('\\')[1] if s is not None else None,
                                     [tag_cv, tag_stat, tag_shut])

    data = []
    for server, tag_list in tags.items():
        session = pdpi.Session(server_name=server,
                               tags=tag_list,
                               time_range=time_range,
                               time_span=f'{sample_sec}s')
        data.append(session.df.dropna())

    # Get brent and dolar quotations
    dolar = get_bid(date_range[0], date_range[1])
    barril = get_brent(date_range[0], date_range[1])

    # Numeric treatment
    df = data[0].join(data[1:])
    df[tag_stat] = df[tag_stat].apply(pd.to_numeric, errors='coerce').fillna(0)
    df[tag_shut] = df[tag_shut].apply(lambda x: 1 if x in ['On', 'ON'] else 0)
    df = df.apply(pd.to_numeric, errors='coerce').ffill()

    # Closed well control
    if shut:
        if opt_shut == 0:    # option greater equal
            df.loc[df[tag_shut] >= val_shut, tag_stat] = -2
        elif opt_shut == 1: # option equal
            df.loc[df[tag_shut] == val_shut, tag_stat] = -2
        elif opt_shut == 2: # option lower equal
            df.loc[df[tag_shut] <= val_shut, tag_stat] = -2
    # status translating
    # TODO modificar a contabilização para que entre 1001 e 1006 o status seja 1, ok?
    df.loc[(df[tag_stat] >= 1001) & (df[tag_stat] < 1006), tag_stat] = 1  # controlling openning
    df.loc[df[tag_stat] == 1006, tag_stat] = 2  # searching lower SP
    df.loc[df[tag_stat] == 9999, tag_stat] = -1 # lost comm
    df.loc[(df[tag_stat] != 1) &
           (df[tag_stat] != 2) &
           (df[tag_stat] != -1) &
           (df[tag_stat] != -2),
           tag_stat] = 0                        # o.c. transition point or off status (9001), defining off

    df['dolar'] = dolar
    df['barril'] = barril
    df.ffill(inplace=True)

    # # Accumulated time online (points)
    # df['acc_online'] = 0
    # df.loc[df[tag_stat] > 0, 'acc_online'] = 1
    # df.loc[:, 'acc_online'] = df.acc_online.cumsum()

    df['inc_bpd'] = 0
    if choice == "PDG":
        df.loc[df[tag_stat] > 0,
               'inc_bpd'] = m3d_to_bpd((p_ref - df[tag_cv]) * ip)*(1 - bsw/100)
    else:
        df.loc[df[tag_stat] > 0,
               'inc_bpd'] = m3d_to_bpd(df[tag_cv]) - prod_test_bpd
    df.loc[df.inc_bpd < 0, 'inc_bpd'] = 0

    # Oil production increases percentage (unitary)
    df['inc_oil_percent'] = 0
    df.loc[df.inc_bpd > 0, 'inc_oil_percent'] = df.inc_bpd/prod_test_bpd

    # Increased barrils
    df['inc_barril'] = 0
    df.loc[df[tag_stat] > 0, 'inc_barril'] = df.inc_bpd * sample_day

    # Accumulated barrils
    df['acc_barril'] = df.inc_barril.cumsum()

    # Monetary gain
    df['money'] = 0
    df.loc[df.inc_bpd > 0, 'money'] = df.inc_barril * df.dolar * df.barril

    # Accumulated monetary gain
    df['acc_money'] = df.money.cumsum()

    return df


if __name__ == "__main__":
    # PI parameters
    tag_cv = 'SESAUPI01\\P52_PDGP-1210009K'
    tag_stat = 'SESAUPI01\\P52_STSCTRPOCOK'
    pi_server = 'SESAUPI01'
    shut_opt = {'tag': 'SESAUPI01\\P52_ZSH-1210008KEPT',
                'compare': 1, # '>=' -> 0, '==' -> 1, '<=' -> 2
                'val': 0}

    # Well parameters
    p_ref = 147.2
    ip = 19.14
    prod_test_m3d = 1250
    bsw = 34

    # date parameters
    day_1 = datetime.now()
    n_days = timedelta(days=5)
    date_range = (day_1, day_1 - n_days)
    sample_sec = 60

    df = prod_inc(tag_cv, tag_stat, pi_server,
                  p_ref, ip, prod_test_m3d,
                  date_range, sample_sec,
                  bsw, shut_opt)
    print(df.describe())

    tag_cv = 'SESAUPI01\\P52_MVM_FI_RO-9'
    tag_stat = 'SESAUPI01\\P52_STSCTRPOCOU'
    pi_server = 'SESAUPI01'
    shut_opt = {'tag': 'SESAUPI01\\P52_ZSH-1210008UEPT',
                'compare': 1, # '>=' -> 0, '==' -> 1, '<=' -> 2
                'val': 0}

    # Well parameters
    p_ref = 147.2
    ip = 19.14
    prod_test_m3d = 1250
    bsw = 34

    # date parameters
    day_1 = datetime.now()
    n_days = timedelta(days=5)
    date_range = (day_1, day_1 - n_days)
    sample_sec = 60

    df = prod_inc(tag_cv, tag_stat, pi_server,
                  p_ref, ip, prod_test_m3d,
                  date_range, sample_sec,
                  bsw, shut_opt)
    print(df.describe())