# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 08:33:58 2022

@author: richie bao
"""
from tqdm.auto import tqdm
from multiprocessing import Pool
from functools import partial
import pandas as pd
import geopandas as gpd
import os
import pickle 

from aot_data_category_pool import AoT_data_category_pool
from database import cfg_load_yaml,postSQL2gpd

def AoT_data_sort(data_fn,category_set,category_column,save_path,chunksize,AoT_nodes=None):
    '''
    多线程。读取AoT-data数据，并存储为.gpkg或者.pkl

    Parameters
    ----------
    data_fn : string
        AoT_data数据，传感器测量数据.
    category_set : list(string)
        data:parameter传感器测量分类字段列表.
    category_column : string
        判断分类的列表，即AoT-data的parameter字段.
    save_path : string
        文件保存的根目录.
    chunksize : int.
        分批读取数据一次读取的文件量（样本行）.
    AoT_nodes : GeoDataFrame, optional
        AoT-nodes节点信息数据，包含节点分布几何点（geometry）。如果给定该参数则保存为GPKG，否则保存为.pkl(pickle保存). The default is None.

    Returns
    -------
    category_none : list(string)
        已经保存的分类数据名列表.
    '''
    
    args=partial(AoT_data_category_pool, args=[data_fn,chunksize,category_column,save_path,AoT_nodes])
    with Pool(8) as p:
        category_none=p.map(args, tqdm(list(category_set))) #[:3]
        
    category_fn_dict={category:os.path.join(save_path,"{}.pkl".format(category)) for category in category_set}
    category_fn_dict_fn= os.path.join(save_path,"category_fn_dict.pkl")  
    with open(category_fn_dict_fn,'wb') as f:
        pickle.dump(category_fn_dict,f)
    return category_none    

def AoT_data_category_single(data_fn,category,category_column,save_path,AoT_nodes=None,chunksize=10**6):
    '''
    读取AoT-data数据，提取单个分类，并存储为.gpkg或者.pkl

    Parameters
    ----------
    data_fn : string
        AoT_data数据，传感器测量数据.
    category : string
        提取单个分类数据的分类名.
    category_column : string
        判断分类的列表，即AoT-data的parameter字段.
    save_path : string
        文件保存的根目录.
    AoT_nodes : GeoDataFrame,optional
        AoT-nodes节点信息数据，包含节点分布几何点（geometry）。如果给定该参数则保存为GPKG，否则保存为.pkl(pickle保存). The default is None.
    chunksize : int, optional
        分批读取数据一次读取的文件量（样本行）. The default is 10**6.

    Returns
    -------
    category : string
        分类名。可以不定义返回值，该返回值即为输入值.

    '''   
    
    count=0
    for chunk in pd.read_csv(data_fn,chunksize=chunksize):
        category_chunk_df=chunk[chunk[category_column]==category]          
        count+= 1  
        
        if category_chunk_df.empty is False:
            if AoT_nodes is not None:
                category_chunk_df=pd.merge(category_chunk_df,AoT_nodes,on="node_id")
                category_chunky_gdf=gpd.GeoDataFrame(category_chunk_df,crs=AoT_nodes.crs)
                category_chunk_fn=os.path.join(save_path,"{}_{}.gpkg".format(category,count))
                category_chunky_gdf.to_file(category_chunk_fn,driver="GPKG")    
            else:
                category_chunk_fn=os.path.join(save_path,"{}_{}.pkl".format(category,count))
                category_chunk_df.to_pickle(category_chunk_fn)
        else:
            return category 
        
if __name__=="__main__":
    cfg=cfg_load_yaml('./configuration/cfg_AoT.yml')  
    UN=cfg["postgreSQL"]["myusername"]
    PW=cfg["postgreSQL"]["mypassword"]
    DB=cfg["postgreSQL"]["mydatabase"] 
    GC='geometry'
    
    aot_data_processed_fp="D:\AoT\AoT_slice_reduced_data_3600\data.csv"    
    AoT_nodes_gdf=postSQL2gpd(table_name="AoT_nodes",geom_col=GC,myusername=UN,mypassword=PW,mydatabase=DB)    
    category_set=['temperature', 'humidity']
    AoT_data_category_save_fp="D:\AoT\AoT_slice_reduced_data_3600_category"
    
    category_none=AoT_data_sort(aot_data_processed_fp,category_set,'parameter',AoT_data_category_save_fp,chunksize=10**6,AoT_nodes=AoT_nodes_gdf) 
    _=AoT_data_category_single(aot_data_processed_fp,'concentration','parameter',AoT_data_category_save_fp,AoT_nodes_gdf,chunksize=10**8)