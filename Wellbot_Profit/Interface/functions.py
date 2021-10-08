# -*- coding: utf-8 -*-
"""
Created on Mon Sep 08 16:18:00 2021

@author: aiq7
"""


from datetime import datetime, timedelta
from inc_calc import prod_inc

def define_time_interval(date0, date1):
    step_time = timedelta(days=(date1 - date0).days)
    now = datetime.now()
    if (date0 > now.date() or 
        date0 + step_time > now.date()):
        st.warning('Data a frente do dia de hoje.')
        step_time = timedelta(days=0)

    start = timedelta(days=0)
    end = timedelta(days=0)
    if step_time.days < 0:
        start = step_time
    else:
        end = step_time

    start_date = datetime(date0.year,
                          date0.month,
                          date0.day) + start
    end_date = datetime(date0.year,
                        date0.month,
                        date0.day,
                        23, 59, 59) + end
    if end_date > now:
        end_date = now

    return start_date, end_date

# =============================================================================
# Getting data
# =============================================================================
def new_data(tag_cv, tag_stat, pi_server, shut_opt, p_ref, ip, prod_test_m3d,
             date0, date1, sample_sec, bsw, choice):
    # 'pdgp', 'stat', 'dolar', 'barril', 'acc_online', 'inc_bpd',
    # 'inc_oil_percent', 'inc_barril', 'acc_barril', 'money', 'acc_money']
    df = prod_inc(tag_cv=tag_cv, tag_stat=tag_stat, pi_server=pi_server,
                  shut_opt=shut_opt, p_ref=p_ref, ip=ip,
                  prod_test_m3d=prod_test_m3d, date_range=(date0, date1),
                  sample_sec=sample_sec, bsw=bsw, choice=choice)
    return df