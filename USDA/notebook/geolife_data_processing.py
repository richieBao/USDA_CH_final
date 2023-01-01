# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 18:18:28 2022

@author: richie bao
"""
import geopandas as gpd
from database import postSQL2gpd,gpd2postSQL,df2postSQL,postSQL2df
from util_misc import AttrDict
__C=AttrDict() 
args=__C

__C.db=AttrDict() 
__C.db.UN='postgres'
__C.db.PW='123456'
__C.db.DB='public_transportation'
__C.db.GC='geometry' 
__C.db.db_info=dict(geom_col=args.db.GC,myusername=args.db.UN,mypassword=args.db.PW,mydatabase=args.db.DB)

__C.gi=AttrDict()
__C.gi.nanjing_epsg=32650
__C.gi.beijing_epsg=32750
__C.gi.epsg_wgs84=4326

__C.data=AttrDict()
__C.data.geolife_gdf='E:\data\geolife.gpkg'

def geolife_transportation_mode(geolife_gdf,geolife_labels,epsg=None):
    import pandas as pd
    from tqdm import tqdm
    from multiprocessing import Pool
    import numpy as np
    from geolife_data_processing_pool import process
    tqdm.pandas()
    
    '''
    function - 基于geolife计算不同通行工具的均速,前期数据处理
    '''    
    geolife_gdf=geolife_gdf.to_crs(epsg=epsg) 
    geolife_gdf['datetime']=pd.to_datetime(geolife_gdf['date_str']+' '+geolife_gdf['time_str'])
    geolife_gdf.sort_values(by='datetime',inplace=True)
    
    geolife_labels['st_dt']=pd.to_datetime(geolife_labels['start_time'])
    geolife_labels['et_dt']=pd.to_datetime(geolife_labels['end_time'])
    geolife_labels.sort_values(by='st_dt',inplace=True)
     
    workers=8
    with Pool(workers) as p:
        pool_results=p.map(process, tqdm(np.array_split(geolife_gdf,workers)))
    t_mode_df=pd.concat(pool_results, axis=0)
    geolife_tm_gdf=pd.concat([geolife_gdf, t_mode_df], axis=1)
    return geolife_tm_gdf,geolife_labels


if __name__=="__main__":
    geolife_beijing_gdf=gpd.read_file(args.data.geolife_gdf)
    print('-'*50)
    geolife_labels_df=postSQL2df('geolife_labels',**args.db.db_info)
    geolife_tm_beijing_gdf,geolife_labels=geolife_transportation_mode(geolife_beijing_gdf,geolife_labels_df,args.gi.beijing_epsg)
    
