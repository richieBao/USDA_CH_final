# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 08:32:52 2022

@author: richie bao
"""
import pandas as pd
import geopandas as gpd
import os
import pickle

def AoT_data_category_pool(category,args):
    '''
    读取AoT-data数据，并存储为.gpkg或者.pkl

    Parameters
    ----------
    category : string
        分类名.
    args : list
        变量列表.

    Returns
    -------
    category : string
        分类名。可以不定义返回值，该返回值即为输入值.

    '''
    
    data_fn,chunksize,category_column,save_path,AoT_nodes=args    
    category_fn_dict={}
    count=0
    temp=[]
    for chunk in pd.read_csv(data_fn,chunksize=chunksize):
        temp.append(chunk[chunk[category_column]==category])            
        count+= 1
        # if count==3:break
    category_df=pd.concat(temp)    
    # print("+"*50)
    # print(category_df)
    if category_df.empty is False:
        if AoT_nodes is not None:
            category_df=pd.merge(category_df,AoT_nodes,on="node_id")
            category_gdf=gpd.GeoDataFrame(category_df,crs=AoT_nodes.crs)
            category_fn=os.path.join(save_path,"{}.gpkg".format(category))
            category_gdf.to_file(category_fn,driver="GPKG")    
        else:
            category_fn=os.path.join(save_path,"{}.pkl".format(category))
            category_df.to_pickle(category_fn)
    else:
        return category
    
    