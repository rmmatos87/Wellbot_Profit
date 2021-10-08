# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:02:40 2020

@author: aiq7
"""

from datetime import datetime, timedelta
from .functions import define_time_interval, new_data
from Interface import Config
import streamlit as st


def reload(mode):
    st.session_state.mode = mode
    if mode == 0:
        start()
    elif mode == 1:
        load_config()
    elif mode == 2:
        new_config()
    elif mode == 3:
        
        loaded()

def start():
    st.sidebar.markdown('# Inicializando')
    st.markdown('Selecione se deseja carregar ou criar um caso.')
    st.sidebar.button('Carregar caso', on_click=reload, args=(1,))
    st.sidebar.button('Novo caso', on_click=reload, args=(2,))

def load_config():
# =============================================================================
# Sidebar: Pré-configurações
# =============================================================================
    st.session_state.mode = 1
    st.sidebar.markdown('# Carregar caso')

    config_uep = st.sidebar.selectbox(label='UEP',
                                      options=st.session_state.config.default.keys(),
                                      key=1000)
    config_well = st.sidebar.selectbox(label='Poço',
                                       options=st.session_state.config.default[config_uep].keys())
    config_dates = st.sidebar.selectbox(label='Datas',
                                        options=st.session_state.config.default[config_uep][config_well].keys())
    config_values = st.session_state.config.default[config_uep][config_well][config_dates]

    st.session_state.config.update(config_uep, config_well, config_dates, config_values)

    b_load = st.sidebar.button('Carregar', on_click=reload, args=(3,))
    st.session_state.config.update(config_uep, config_well, config_dates, config_values)

    b_del = st.sidebar.button('Excluir')

    if b_del:
        st.session_state.data = None
        st.session_state.config.delete(config_uep, config_well, config_dates)
        st.warning('Deletado.')

    st.sidebar.markdown('---')

# =============================================================================
# Sidebar: Configurações
# =============================================================================
def new_config():
    st.sidebar.markdown('# Novo caso')
    load_variables()
    b_back = st.sidebar.button('Voltar')
    if b_back:
        st.session_state.mode = 0
    st.sidebar.markdown('---')

def loaded():
    st.sidebar.markdown('# Carregar caso')
    load_variables(uep=st.session_state.config.uep,
                   well=st.session_state.config.well,
                   **st.session_state.config.actual)

def load_variables(uep=None, well=None, tag_stat=None, choice = None,
                   tag_cv=None, pi_server=None, shut_opt=None,
                   date0=None, date1=None, sample_sec=60, p_ref=0, ip=0,
                   prod_test_m3d=0, bsw=0):

    date0 = date0 if date0 is not None else str(datetime.now().date() -
                                                timedelta(days=3))
    date1 = date1 if date1 is not None else str(datetime.now().date())

# =============================================================================
# Identificação
# =============================================================================
    st.sidebar.markdown('## Identificação')
    st.session_state.config.uep = st.sidebar.text_input('UEP:',
                                                        value=uep)
    st.session_state.config.well = st.sidebar.text_input('Poço:',
                                                         value=well)
# =============================================================================
# PI variables
# =============================================================================
    st.sidebar.markdown('## Variáveis do PI')

    st.session_state.config.pi_server = st.sidebar.text_input(
        'Servidor do PI:', value=pi_server,
        help=('Caso alguma variável esteja em um servidor diferente,' +
              'utilize o formato: **SERVER/TAG**'))
    
    tag_stat = st.sidebar.text_input('TAG do status do controlador:',
                                     value=tag_stat)
    st.session_state.config.tag_stat = tag_stat if '\\' in tag_stat else f"{pi_server}\\{tag_stat}"

    help_equation = r"""$Cálculo=\begin{cases}
    PDG & \Delta Q = IP*(P_{ref} - P_{PDG})*(1 - BSW_\%*100) \\
    MVM & \Delta Q = Q_{MVM} - Q_{ref}
    \end{cases}$"""
    st.session_state.config.choice = st.sidebar.select_slider(
        'Modelo', ('PDG', 'MVM'), value=choice,
        help=help_equation)

    tag_cv = st.sidebar.text_input(f'TAG do {st.session_state.config.choice}:',
                                   value=tag_cv)
    st.session_state.config.tag_cv = tag_cv if '\\' in tag_cv else f"{pi_server}\\{tag_cv}"

    if shut_opt is None:
        tag_shut = None
        val_shut = 0
        opt_shut = 1
        shut = False
    else:
        tag_shut = st.session_state.config.shut_opt['tag']
        opt_shut = st.session_state.config.shut_opt['compare']
        val_shut = st.session_state.config.shut_opt['val']
        shut = True

    shut = st.sidebar.checkbox('Habilitar controle de poço fechado.',
                               value=shut)
    if shut:
        tag_shut = st.sidebar.text_input('TAG poço fechado:',
                                         value=tag_shut)
        tag_shut = tag_shut if '\\' in tag_shut else f"{pi_server}\\{tag_shut}"

        opt_shut = st.sidebar.selectbox('Relação',
                                        ('>=', '==', '<='),
                                        index=opt_shut)

        opt_shut = {'>=': ['\ge', 0],
                    '==': ['=', 1],
                    '<=': ['\le', 2]}[opt_shut]

        val_shut = st.sidebar.number_input('Valor',
                                           value=val_shut)

        st.session_state.config.shut_opt = {'tag': tag_shut,
                                            'compare': opt_shut[1],
                                            'val': val_shut}

        st.sidebar.markdown(f'Quando {tag_shut} ${opt_shut[0]} {val_shut}$' +
                            ' o poço será considerado fechado')
    
    st.sidebar.markdown('---')

# =============================================================================
# Time variables
# =============================================================================
    st.sidebar.markdown('## Variáveis de tempo')
    st.session_state.config.date0 = st.sidebar.date_input(
        "Data início:", datetime.fromisoformat(date0)
    )
    st.session_state.config.date1 = st.sidebar.date_input(
        "Data fim:", datetime.fromisoformat(date1)
    )
    
    # st.sidebar.markdown(f'step = {step_time}')

    # step_time = timedelta(days=st.sidebar.number_input('Range de tempo (dias):',
    #                                                    value=-30))
    st.session_state.config.sample_sec = st.sidebar.number_input('Amostragem (s):',
                                                                 value=sample_sec,
                                                                 min_value=1)
    
    (st.session_state.config.date0,
     st.session_state.config.date1) = define_time_interval(
        st.session_state.config.date0, st.session_state.config.date1)
    
    st.session_state.config.dates = '%s - %s' % (st.session_state.config.date0.date(),
                                                 st.session_state.config.date1.date())
    
    st.sidebar.markdown('---')

# =============================================================================
# Well variables
# =============================================================================
    st.sidebar.markdown('## Variáveis de Poço')
    if st.session_state.config.choice == 'PDG':
        st.session_state.config.p_ref = st.sidebar.number_input(
            'Pressão do ponto de instabilização:',value=p_ref)
        st.session_state.config.ip = st.sidebar.number_input(
            'IP do poço:', value=ip)
        st.session_state.config.bsw = st.sidebar.number_input(
            'BSW do poço (%):', value=bsw)
    else:
        st.session_state.config.p_ref = None
        st.session_state.config.ip = None
        st.session_state.config.bsw = None

    st.session_state.config.prod_test_m3d = st.sidebar.number_input(
        'Produção teste (m³ óleo/d):', value=prod_test_m3d)

    st.sidebar.markdown('---')
    
    b_save = st.sidebar.button('Salvar caso')
    if b_save:
        st.session_state.config.actual = {
            key: getattr(st.session_state.config, key) for key in [
                'tag_stat', 'choice', 'tag_cv', 'pi_server', 'shut_opt',
                'p_ref', 'ip', 'prod_test_m3d', 'bsw', 'sample_sec']
            }
        st.session_state.config.save_all()
        st.warning('Salvo!')
    
    run = st.sidebar.button('Coleta de dados')
    if run:
        st.session_state.df = new_data(**st.session_state.config.actual,
                                       date0=st.session_state.config.date0,
                                       date1=st.session_state.config.date1)
        st.session_state.data = True
