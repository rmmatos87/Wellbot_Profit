# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:02:40 2020

@author: aiq7
"""

import base64
import json
import requests
import os

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime, timedelta
from Interface import Config, define_time_interval, sidebar
__version__ = '0.1.5'
__author__ = 'aiq7'

# rev 0.1.4: Download da tabela transformado para csv e unidades jogadas
#            para a descrição

# rev 0.1.5: Controle de salvar e carregar configurações

# TODO incluir página com as fórmulas
# TODO incluir modo de adicionar e remover análise

# v 0.66
# st.beta_set_page_config(page_title="Wellbot Gain",
#                         page_icon=None,
#                         layout='centered',
#                         initial_sidebar_state='auto')




plt.style.use('default')

m3d_to_bpd = lambda value: value/0.159
sec_to_day = lambda sec: sec/24/60/60



# =============================================================================
# Funções principais
# =============================================================================
def get_table_download_link_pi(df):
    """
    Generate a link to download data in a given panda dataframe.

    Parameters
    ----------
    df : DataFrame
        DataFrame containing all data.

    Returns
    -------
    href : str
        HTML reference to download DataFrame as csv.

    """
    svg = '(csv)'
    try:
        with open('../../../src/icon/file-download-solid.svg') as f:
            svg = f.read()
            svg = svg.replace('>',
                              ' style="width:32px;height:32px;">', 1)
    except:
        pass
    csv = st.session_state.df.to_csv()
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'Download dos **dados do PI** (csv) <a href="data:file/csv;base64,{b64}">{svg}</a>'
    return href


def money_str(n, short=False):
    n = round(n, 2)
    if isinstance(n, float):
        int0, dec0 = ('%.2f'%n).split('.')
    elif isinstance(n, int):
        int0, dec0 = str(n), '00'
    else:
        raise TypeError('"n" must be int or float.')
    nn = len(int0)
    add_0 = nn//3 * 3 + (3 if nn % 3 != 0 else 0) - nn
    int1 = '0' * add_0 + int0
    int2 = ''.join([int1[i:i+3]+',' for i in range(0, nn, 3)])[add_0:-1]

    num = 'R$ ' + int2 + '.' + dec0
    if short:
        leg = ['mi', 'bi', 'tri']
        int3 = int2.split(',')
        l0 = len(int2.split(','))
        if l0 > 1:
            num = int(int3[0]) + float('0.'+''.join(int3[1:]))
            return 'R$ %.2f %s' % (num, leg[l0 - 1])

    return num

def table():
    """
    Gera a tabela de relatório da análise

    FUT (Fator de Utilização):
    incluir um KPI que seria o tempo que a aplicação ficou ligada em relação ao
    tempo que o poço esteve aberto. Calculei o FUT de agosto e ficamos com
    FUT = 75% (Tempo ligado / tempo poço aberto). Fórmula:
        FUT = 100 * (Tempo no status 1006 / Tempo de poço P > 200 bar)
    Considerando que você já fez a classificação (gráfico abaixo), eu acho que a
    implementação do KPI no relatório é simples.
    FUT = [ 1 – 20,5 / ( 20,5 + 62,7 ) ] * 100 = 75 %.

    Returns
    -------
    s1 : TYPE
        DESCRIPTION.
    cv_lim_out : TYPE
        DESCRIPTION.

    """
    # Tempo para cálculo de menor pressão
    # t_min * sample_time
    status = df[tag_stat].value_counts() # pd.series - índice: diferentes status [-2, -1, 0, 1, 2]
                                                          #           - valores: a contagem de quantas vezes cada índice aparece no df
    # Para 
    window = 1 * 60
    cv_min = df[tag_cv].loc[
        df[tag_stat]>0].rolling(window).median().min()
    cv_max = df[tag_cv].loc[
        df[tag_stat]>0].rolling(window).median().max()
    
    not_found = False
    if np.isnan(cv_min):
        if choice == "PDG":
            cv_min = p_ref
        elif choice == "MVM":
            cv_max = prod_test_m3d
        not_found = True
        cv_lim_out = None

    if choice == "PDG":
        pr_inc_pot = m3d_to_bpd(ip * (p_ref - cv_min))
        cv_lim_out = cv_min
        cv_txt = 'Pressão mínima alcançada (bar)'
    elif choice == "MVM":
        pr_inc_pot = m3d_to_bpd(cv_max) - prod_test_m3d
        cv_lim_out = cv_max
        cv_txt = 'Vazão máxima alcançada (m3d)'

    pr_potential = (abs((date0-date1).days) + 1) * pr_inc_pot
    money_potential = (pr_inc_pot *
                       df.dolar.resample('1d').mean() *
                       df.barril.resample('1d').mean()).sum()
    data = [
        date0.strftime(r'%d/%m/%Y %H:%M:%S'),
        date1.strftime(r'%d/%m/%Y %H:%M:%S'),
        '%.1f' % (df[tag_stat][df[tag_stat] > 0].count()*sample_sec/24/60/60),
        '%.1f' % ((status.get(2, default=0)+status.get(1, default=0))/(status.sum() - status.get(-2, default=0))*100),
        df[tag_stat].loc[(df[tag_stat]<0) & (df[tag_stat]!=df[tag_stat].shift())].count(),
        '%.2f' % (df.inc_oil_percent.mean() * 100),
        '%.2f' % (df.inc_oil_percent.max() * 100),
        'Não aplicável.' if not_found else '%.1f' % (cv_lim_out),
        '%d' % (df.acc_barril.max()),
        '%d' % (pr_potential),
        'Não aplicável.' if not_found else '%.2f' % (df.acc_barril.max()/pr_potential*100),
        '%.2f' % (df.acc_money.max()),
        '%.2f' % money_potential
    ]
    
    index = ['Data Inicial', 'Data Final','Tempo Online (dias)',
             'Fator de Utilização (%)', 'Perda de conexão com o servidor',
             'Aumento de produção (% Média)', 'Aumento de produção (% Máximo)',
             cv_txt, 'Produção acumulada (barril)',
             'Potencial de produção (barril)', 'Potencial de aumento desbloqueado (%)',
             'Ganho (R$)','Potencial de ganho (R$)']
    
    s1 = pd.DataFrame(data, index=index, columns=['Índices']).fillna(0).T
        
    return s1, cv_lim_out



def get_table_download_link_table(df=None, s=None):
    """
    Generate a link to download data in a given panda dataframe.

    Parameters
    ----------
    df : DataFrame
        DataFrame containing all data.

    Returns
    -------
    href : str
        HTML reference to download DataFrame as csv.

    """
    if df is not None:
        status = df[tag_stat].value_counts()
        window = 1*60
        cv_min = df[tag_cv].loc[df[tag_stat]>0].rolling(window).median().min()
        cv_min_out = cv_min
        not_found = False
        if np.isnan(cv_min):
            cv_min = p_ref
            not_found = True
            cv_min_out = None
        pr_potential = m3d_to_bpd((abs((date0-date1).days) + 1) *
                                ip *
                                (p_ref - cv_min))
        description = {
                'Data Inicial':
                    date0,
                'Data Final':
                    date1.strftime(r'%d/%m/%Y %H:%M:%S'),
                'Tempo Online (dias)':
                    '%.1f'%(df[tag_stat][df[tag_stat] > 0].count()*sample_sec/24/60/60),
                'Fator de Utilização (%)':
                    '%.1f'%((status.get(2, default=0)+status.get(1, default=0))/(status.sum() - status.get(-2, default=0))*100),
                'Perda de conexão com o servidor':
                    df[tag_stat].loc[(df[tag_stat]<0) & (df[tag_stat]!=df[tag_stat].shift())].count(),
                'Aumento de produção (% Média)':
                    '%.2f'%(df.inc_oil_percent.mean() * 100),
                'Aumento de produção (% Máximo)':
                    '%.2f'%(df.inc_oil_percent.max() * 100),
                'Pressão mínima alcançada (bar)':
                    'Não aplicável.' if not_found else '%.1f'%(cv_min),
                'Produção acumulada (barril)':
                    '%d'%(df.acc_barril.max()),
                'Potencial de produção (barril)':
                    '%d'%(pr_potential),
                'Potencial de aumento desbloqueado (%)':
                    'Não aplicável.' if not_found else '%.2f'%(
                        df.acc_barril.max()/pr_potential*100),
                'Ganho (R$)':
                    '%.2f'%(df.acc_money.max()),
                'Potencial de ganho (R$)':
                    '%.2f'%((m3d_to_bpd(ip * (p_ref - cv_min)) *
                            df.dolar.resample('1d').mean() *
                            df.barril.resample('1d').mean()).sum())
                    }
        s = pd.Series(description, name='Tabela')

    svg = '(clipboard)'
    try:
        with open('../../../src/icon/file-download-solid.svg') as f:
            svg = f.read()
            svg = svg.replace('>',
                              ' style="width:32px;height:32px;">', 1)
    except:
        pass
    txt = s.to_csv()
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(txt.encode()).decode()
    href = f'Download da **tabela** (csv) <a href="data:file/csv;base64,{b64}">{svg}</a>'
    return href

# graph = st.selectbox('Grafico para visualização:',
#                      ('Online Status', 'Barrils', ))
def status(figsize=(5,5)):
    """
    Create a half pie to show controller online proportion.

    Status:
        * -2 - Well Shut
        * -1 - Lost Communication
        * 0 - Offline
        * 1 - Online
        * 2 - Online with Auto Settling

    Returns
    -------
    None.

    """
    stat = df[tag_stat].value_counts().sort_index()
    on = ((stat.loc[stat.index > 0])/stat.sum()).sum()
    off = ((stat.loc[stat.index <= 0])/stat.sum()).sum()
    
    rot = 30
    green = on*(180 + 2*rot)/360
    red = off*(180 + 2*rot)/360
    white = (180 - 2*rot)/360
    
    off_rot = off - 2*rot/180
    fig = plt.figure(figsize=figsize)
    plt.pie([red, green, white],
            colors=['red', 'green', 'white'],
            labels=['OFF [%.1f%%]'%(off*100),
                    'ON [%.1f%%]'%(on*100),
                    ''],
            wedgeprops=dict(width=.3,
                            edgecolor='w'),
            startangle=-rot)
    plt.title('Online Status')
    
    # Creates base line
    radius = np.array([1.1, .6]) # [internal, external]
    theta = [180 + rot, - rot] # [left, right]
    x_l = radius * np.cos(np.pi*theta[0]/180)
    y_l = radius * np.sin(np.pi*theta[0]/180)
    x_r = radius * np.cos(np.pi*theta[1]/180)
    y_r = radius * np.sin(np.pi*theta[1]/180)
    plt.plot(x_l, y_l, 'k')
    plt.plot(x_r, y_r, 'k')

    # Creates the arrow pointer
    r_arrow = 1.2 # pointer radius
    b_arrow = 0.05 # base width
    theta = off*(180 + 2*rot) - rot
    x_arrow_point = r_arrow*np.cos(np.pi*theta/180)
    y_arrow_point = r_arrow*np.sin(np.pi*theta/180)
    x_arrow_b_e = +b_arrow*np.cos(np.pi*theta/180 + np.pi/2)
    y_arrow_b_e = +b_arrow*np.sin(np.pi*theta/180 + np.pi/2)
    x_arrow_b_d = +b_arrow*np.cos(np.pi/2 - np.pi*theta/180)
    y_arrow_b_d = -b_arrow*np.sin(np.pi/2 - np.pi*theta/180)
    plt.plot([x_arrow_b_e, x_arrow_point, x_arrow_b_d],
             [y_arrow_b_e, y_arrow_point, y_arrow_b_d],
             'k',
             linewidth=3)

    st.pyplot(fig)

def dual_plot(s1, s2, alpha=.6, figsize=(10,5)):
    fig, ax1 = plt.subplots(figsize=figsize);

    color = 'darkblue'
    ax1.set_ylabel(s1.name, color=color);
    s1.plot(ax=ax1, color=color, alpha=alpha, grid=True);
    ax1.tick_params(axis='y', labelcolor=color);
    
    # ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'darkred'
    s2.plot(ax=ax1, color=color, secondary_y=True, alpha=alpha);
    ax2 = plt.gca();
    ax2.set_ylabel(s2.name, color=color);  # we already handled the x-label with ax1
    ax2.tick_params(axis='y', labelcolor=color);
    
    return fig, ax1, ax2

def hist_online():
    fig, ax = plt.subplots()
    
    counts = df[tag_stat].value_counts()*sample_sec/3600

    ws = counts.get(-2, default=0)
    lc = counts.get(-1, default=0)
    off = counts.get(0, default=0)
    on = counts.get(1, default=0)
    ast = counts.get(2, default=0)
    cnt = ws + lc + off + on + ast
    vec = [ws, lc, off, on, ast]
    
    category = {'well shut': ws,
                'lost comm': lc,
                'offline': off,
                'online': on,
                'online\nauto-settling': ast}
    ax.bar(category.keys(), category.values())
    plt.ylabel('horas')
    for x in range(len(vec)):
        ax.text(x, vec[x]/2,
                '%5.1f%%'%(vec[x]/cnt*100),
                horizontalalignment='center',
                color='red')

    st.pyplot(fig, bbox_inches="tight")



# =============================================================================
# Principal
# =============================================================================
def main():
    st.markdown('# Wellbot Profit')
    st.markdown('<img src="https://www.nicepng.com/png/full/' +
            '18-184050_clipart-robot-png.png" ' +
            'style="width:64px;height:64px;">' +
                f'Versão: {__version__}',
                unsafe_allow_html=True)
    st.markdown('Em caso de problemas, enviar para ' +
                f'<a href="mailto:{__author__}">' +
                f'{__author__}</a>', unsafe_allow_html=True)
    
    # st.markdown('<img src="https://www.osisoft.com/-/jssmedia/osi_logo.ashx?iar=0&hash=3B9E40A3003883D80077122CFD17B70D" width=10%>' + \
                # get_table_download_link(df),
                # unsafe_allow_html=True)
    st.markdown(get_table_download_link_pi(df),
                unsafe_allow_html=True)
    
    description, cv_min = table()
    st.table(description)
    
    st.markdown(get_table_download_link_table(s=description),
                unsafe_allow_html=True)

    try:
        status()
    except Exception as e:
        st.write(e)
        
    fig, ax1, ax2 = dual_plot(df.inc_barril,
                              df.acc_barril)
    plt.title('Acréscimo de Barris: Instantâneo vs. Acumulado')
    st.pyplot(fig, bbox_inches="tight")

    fig, ax1, ax2 = dual_plot(df.money,
                              df.acc_money)
    plt.title('Ganho monetário (R$): Instantâneo vs. Acumulado')
    st.pyplot(fig, bbox_inches="tight")

    fig, ax1, ax2 = dual_plot(df.dolar,
                              df.barril)
    plt.title('Dolar vs. Barril')
    st.pyplot(fig, bbox_inches="tight")
    st.markdown('**Fontes:**\n' +
                '* Dolar: https://docs.awesomeapi.com.br/api-de-moedas\n' +
                '* Brent: https://www.eia.gov/opendata/qb.php');


# =============================================================================
# PDG-P vs. STATUS
# =============================================================================
    fig, ax1, ax2 = dual_plot(df[tag_cv],
                              df[tag_stat])
    if cv_min:
        variable = 'Q_{max}' if choice == "MVM" else 'P_{min}'
        measure = 'm3d' if choice == "MVM" else 'bar'

        pd.DataFrame(
            [cv_min, cv_min],
            index=[df[tag_cv].index[i] for i in (0, -1)],
            columns=['$%s=%.2f$ %s' % (variable,
                                        cv_min,
                                        measure)]).plot(ax=ax1,
                                                        style='--k',
                                                        alpha=.5,
                                                        zorder=.5)
    ylim1 = ax1.axes.get_ylim()
    # Resize to upper 75% of the figure
    dy1 = (ylim1[1] - ylim1[0]) * .25
    ax1.axes.set_ylim(ylim1[0] - dy1, ylim1[1])
    # Resize to lower 25% of the figure
    inf_lim = -2.1
    dy2 = (3 - (inf_lim))/.25
    ax2.axes.set_ylim(inf_lim, 3 + dy2);
    ax2.axes.set_yticks([-2, -1, 0, 1, 2])
    ax2.axes.set_yticklabels(['well\nshut',
                              'comm\nerror',
                              'off',
                              'on',
                              'AS'],
                             fontsize=6,
                             linespacing=.8);
    ax2.grid(linestyle=':', alpha=.7)
    ax2.set_ylabel(None)
    plt.title(f'{choice} vs. Status')
    st.pyplot(fig, bbox_inches="tight")

# =============================================================================
# Colored PDG-P
# =============================================================================
    fig, ax = plt.subplots(figsize=(10, 5))
    list_stat = [-2, -1, 0, 1, 2]
    list_str_stat = ['well\nshut', 'comm\nerror', 'off', 'on', 'on\nAS']
    n_color = df[tag_stat].value_counts().shape[0]
    # plottind dasshed PDG-P values
    df[tag_cv].plot(style='--w', alpha=.8, legend=True)
    # Auxiliar DataFrame to group and plot
    df1 = pd.DataFrame(
        {tag_cv: df[tag_cv].values,
         tag_stat:
         df[tag_stat].apply(lambda x: list_str_stat[int(x)+2])},
        index=df.index)

    df1.groupby(by=tag_stat)[tag_cv].plot(style='+', markersize=3, legend=True);
    plt.xlim([df[tag_cv].index[i] for i in (0, -1)])
    if cv_min:
        variable = 'Q_{max}' if choice == "MVM" else 'P_{min}'
        measure = 'm3d' if choice == "MVM" else 'bar'
        pd.DataFrame([cv_min, cv_min],
                     index=[df[tag_cv].index[i] for i in (0, -1)],
                     columns=['$%s=%.2f$ %s' % (variable,
                                                cv_min,
                                                measure)]).plot(ax=ax,
                                                                style='--k',
                                                                alpha=0.5);
    plt.title(f'{choice} categorizado')
    plt.legend(fontsize=8)
    st.pyplot(fig, bbox_inches="tight")
    
    hist_online()

    if tag_shut not in (tag_cv, tag_stat):
        fig, ax1, ax2 = dual_plot(df[tag_cv],
                                  df[tag_shut])
        plt.title(f'{choice} vs. TAG de controle de poço fechado')
        ylim1 = ax1.axes.get_ylim()
        # Resize to upper 75% of the figure
        dy1 = (ylim1[1] - ylim1[0]) * .25
        ax1.axes.set_ylim(ylim1[0] - dy1, ylim1[1])
        # Resize to lower 25% of the figure
        inf_lim = -0.1
        dy2 = (1 - (inf_lim))/.25
        ax2.axes.set_ylim(inf_lim, 1 + dy2);
        ax2.axes.set_yticks([0, 1])
        ax2.axes.set_yticklabels(['Closed',
                                  'Openned'],
                                 fontsize=6,
                                 linespacing=.8);
        ax2.grid(linestyle=':', alpha=.7)
        # ax2.set_ylabel(None)
        st.pyplot(fig, bbox_inches="tight")

# =============================================================================
# Inicializações
# =============================================================================
if 'config' not in st.session_state:
    st.session_state.config = Config()

# mode: 0 - config
#       1 - load config
#       2 - run
if 'mode' not in st.session_state:
    st.session_state.mode = 0
if 'data' not in st.session_state:
    st.session_state.data = False

# =============================================================================
# Chamadas
# =============================================================================
home = st.button('Principal')
if home:
    st.session_state.mode = 0

sidebar.reload(st.session_state.mode)

if st.session_state.data:
    (tag_stat, choice, tag_cv, pi_server, shut_opt, p_ref,
     ip, prod_test_m3d, bsw, sample_sec) = list(st.session_state.config.actual.values())
    df = st.session_state.df
    date0 = st.session_state.config.date0
    date1 = st.session_state.config.date1
    tag_shut = st.session_state.config.shut_opt['tag']
    ## Recovering only TAGs, without servers
    tag_cv, tag_stat, tag_shut = map(lambda s: s.split('\\')[1] if s is not None else None,
                                     [tag_cv, tag_stat, tag_shut])
    main()