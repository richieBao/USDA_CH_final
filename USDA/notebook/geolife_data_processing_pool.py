# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 18:25:14 2022

@author: richie bao
"""
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool
import numpy as np
from database import df2postSQL,postSQL2df
from util_misc import AttrDict
__C=AttrDict() 
args=__C

__C.db=AttrDict() 
__C.db.UN='postgres'
__C.db.PW='123456'
__C.db.DB='public_transportation'
__C.db.GC='geometry' 
__C.db.db_info=dict(geom_col=args.db.GC,myusername=args.db.UN,mypassword=args.db.PW,mydatabase=args.db.DB)

geolife_labels=postSQL2df('geolife_labels',**args.db.db_info)
geolife_labels['st_dt']=pd.to_datetime(geolife_labels['start_time'])
geolife_labels['et_dt']=pd.to_datetime(geolife_labels['end_time'])
geolife_labels.sort_values(by='st_dt',inplace=True)
geolife_labels['label_idx']=range(1, len(geolife_labels)+1)

def trans_mode(row):
    dt=row.datetime
    t_mode=None
    
    for idx_label,row_label in geolife_labels.iterrows():
        transportation_mode=row_label.transportation_mode
        st_dt=row_label.st_dt
        et_dt=row_label.et_dt
        label_idx=row_label.label_idx
        if (dt>=st_dt) & (dt<=et_dt):
            t_mode=transportation_mode
            return pd.Series({"trans_mode":t_mode,"label_idx":label_idx})
    return pd.Series({"trans_mode":t_mode,"label_idx":None})

def process(df):
    results=df.apply(trans_mode, axis=1)
    return results




