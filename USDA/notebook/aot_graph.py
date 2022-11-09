# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 11:59:29 2022

@author: richie bao
"""
from database import cfg_load_yaml,postSQL2gpd
import pandas as pd
pd.set_option('display.max_columns', 500)

def gantt_chart_H(df_,category_field,datatime_field,interval='3h'):
    '''
    指定分类列，给定时间列，按时间间隔提取时间段，并打印数据按时间的分布

    Parameters
    ----------
    df_ : DataFrame
        待打印的数据.
    category_field : string
        分类列字段名.
    datatime_filed : string
        时间列字段名.
    interval : string, optional
        时间周期. The default is '3h'.

    Returns
    -------
    SFT : DataFrame
        用于gantt图打印的DataFrame格式数据.

    '''
    import plotly.figure_factory as ff
    from tqdm import tqdm
    import pandas as pd
    import numpy as np
    from random import randint
    import plotly.io as pio
    pio.renderers.default='browser'
    pd.options.mode.chained_assignment=None 
    
    df=df_.copy(deep=True)  
    category_name=df_[category_field].unique()
    # print(f"category_field number:{len(category_name)}\ncategory_field:\n{category_name}")
    Start_Finish_Task=[]
    for c_n in tqdm(category_name):        
        category_df=df[df[category_field]==c_n]      
        t_interval=category_df.groupby(pd.Grouper(key=datatime_field,axis=0,freq=interval))[datatime_field].agg(['first','last','count'])
        t_interval['count']=t_interval['count']*int(interval[:-1])
        t_interval.columns=['Start', 'Finish', 'Duration_Hours']
        t_interval['Task']=c_n
        Start_Finish_Task.append(t_interval)     
        # print(t_interval[['Start','Finish']])
        # break
    SFT=pd.concat(Start_Finish_Task,ignore_index=True,axis=0)#[:1000] 
    colors=["rgb({},{},{})".format(randint(0,255),randint(0,255),randint(0,255) ) for i in range(len(np.unique(SFT.Task)))]
    fig=ff.create_gantt(SFT,group_tasks=True,index_col='Task',colors=colors)
    fig.update_layout(autosize=False,width=2100,height=1200,)
    fig.show()        
    
    return SFT
    
if __name__=="__main__":
    cfg=cfg_load_yaml('./configuration/cfg_AoT.yml')  
    UN=cfg["postgreSQL"]["myusername"]
    PW=cfg["postgreSQL"]["mypassword"]
    DB=cfg["postgreSQL"]["mydatabase"] 
    GC='geometry'
        
    aot_temperature_gdf=postSQL2gpd(table_name="temperature",geom_col=GC,myusername=UN,mypassword=PW,mydatabase=DB)  
    _=gantt_chart_H(aot_temperature_gdf,"node_id","ts") 

    
    