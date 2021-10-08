# -*- coding: utf-8 -*-
"""
Created on Mon Sep 08 16:18:00 2021

@author: aiq7
"""


from datetime import datetime, timedelta
import json
import os

class Config:
    params = ['tag_stat', 'choice', 'tag_cv', 'tag_cv', 'pi_server',
              'shut_opt', 'p_ref', 'ip', 'prod_test_m3d', 'bsw', 'sample_sec',
              'date0', 'date1', 'uep', 'well', 'dates']
    
    def __init__(self):
        self.default = None
        self.actual = None
        for key in Config.params:
            setattr(self, key, None)
        self.load()
        self._index = -1

    def get(self, key):
        return self.key

    def __iter__(self):
        return self

    def __next__(self):
        self._index += 1
        if self._index >= len(Config.params):
            self._index = -1
            raise StopIteration
        else:
            return Config.params[self._index]
    
    def __repr__(self):
        tab = ' '*4
        end = '\n'
        out = ''
        for uep in self.default:
            this = '*' if uep == self.uep else ''
            out += uep + this + end
            for well in self.default[uep]:
                this = '*' if well == self.well else ''
                out += tab + well + this + end
                for dates in self.default[uep][well]:
                    this = '*' if dates == '%s - %s' % (self.date0, self.date1) else ''
                    out += tab*2 + dates + this + end
                    for key, value in self.default[uep][well][dates].items():
                        out += tab*3 + '%15s: %s' % (key, value) + end
        return out
    
    def save(self):
        with open('.config', 'w') as f:
            json.dump(self.default, f)

    def save_tmp(self):
        with open('.config_tmp', 'w') as f:
            d = {self.uep: {self.well: {self.dates: self.actual}}}
            json.dump(d, f)

    def reset(self):
        dates = '%s - %s' % (datetime.now().date() - timedelta(days=3),
                             datetime.now().date())
        self.default = {
            'P52': {
                'RO-66': {
                    dates: {
                        'tag_stat': r'SESAUPI01\P52_STSCTRPOCOK',
                        'choice': 'PDG',
                        'tag_cv': r'SESAUPI01\P52_PDGP-1210009K',
                        'pi_server': 'SESAUPI01',
                        'shut_opt': {'tag': r'SESAUPI01\P52_ZSH-1210008KEPT',
                                     'compare': 1,
                                     'val': 0},
                        'p_ref': 145.,
                        'ip': 20.96,
                        'prod_test_m3d': 1158.,
                        'bsw': 31.57,
                        'sample_sec': 60
                    }
                },
                'RO-09': {
                    dates: {
                        'tag_stat': r'SESAUPI01\P52_STSCTRPOCOU',
                        'choice': 'MVM',
                        'tag_cv': r'SESAUPI01\P52_MVM_FI_RO-9',
                        'pi_server': 'SESAUPI01',
                        'shut_opt': {'tag': r'SESAUPI01\P52_ZSH-1210008UEPT',
                                     'compare': 1,
                                     'val': 0},
                        'p_ref': None,
                        'ip': None,
                        'prod_test_m3d': 233.9,
                        'bsw': None,
                        'sample_sec': 60
                    }
                }
            }
        }
        self.uep = 'P52'
        self.well = 'RO-66'
        self.dates = dates
        self.actual = self.default[self.uep][self.well][self.dates]

    def load(self):
        if not os.path.exists('.config'):
            try:
                os.remove('.config_tmp')
            except:
                pass
            self.reset()
            self.save()
        else:
            with open('.config') as f:
                self.default = json.load(f)
        
        if not os.path.exists('.config_tmp'):
            uep = list(self.default)[0]
            well = list(self.default[uep])[0]
            dates = list(self.default[uep][well])[0]
            self.actual = self.default[uep][well][dates]
            self.save_tmp()
        else:
            with open('.config_tmp') as f:
                d = json.load(f)

            get_first = lambda d: list(d.keys())[0]
            uep = get_first(d)
            well = get_first(d[uep])
            dates = get_first(d[uep][well])
            self.actual = d[uep][well][dates]
        self._update_attrs(uep, well, dates)
    
    def update(self, uep, well, dates, values):
        self.actual = values
        self.save_tmp()
        self._update_attrs(uep, well, dates)
    
    def _update_attrs(self, uep, well, dates):
        self.uep = uep
        self.well = well
        self.dates = dates
        date0, date1 = dates.split(' - ')
        
        setattr(self, 'date0', date0)
        setattr(self, 'date1', date1)
        for key, value in self.actual.items():
            setattr(self, key, value)

    def delete(self, uep, well, dates):
        self.default[uep][well].pop(dates)
        if len(self.default[uep][well]) == 0:
            self.default[uep].pop(well)
        if len(self.default[uep]) == 0:
            self.default.pop(uep)
        if len(self.default) == 0:
            self.reset()
        self.save()

    def save_all(self):
        if self.uep not in self.default:
            self.default[self.uep] = dict()
        if self.well not in self.default[self.uep]:
            self.default[self.uep][self.well] = dict()

        self.default[self.uep][self.well][self.dates] = self.actual
        self.save()
        self.save_tmp()
