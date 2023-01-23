# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 20:05:15 2023

@author: richie bao
"""
import pickle
from util_misc import AttrDict
from database import postSQL2gpd,gpd2postSQL
import warnings
warnings.filterwarnings('ignore')

__C=AttrDict() 
args=__C

__C.db=AttrDict() 
__C.db.UN='postgres'
__C.db.PW='123456'
__C.db.DB='public_transportation'
__C.db.GC='geometry' 
__C.db.db_info=dict(geom_col=args.db.GC,myusername=args.db.UN,mypassword=args.db.PW,mydatabase=args.db.DB)

__C.data=AttrDict()
__C.data.G_bus_stations="./data/network/G_bus_stations.gpickle"
__C.data.G_SB="./data/network/G_SB.gpickle"
__C.data.station2park_mean_time_cost_all_fn=r'E:\data\public_trans_network\station2park_mean_time_cost_all.pickle'


def station2park_mean_time_cost(G_SB,comprehensivePark_adjacentStations):
    from multiprocessing import Pool    
    from functools import partial
    import networkx as nx
    from functools import reduce
    from station2park_mean_time_cost_pool import station2park_mean_time_cost_single
    from tqdm import tqdm
    
    args=partial(station2park_mean_time_cost_single, args=[comprehensivePark_adjacentStations,G_SB])
    print('-'*50)
    with Pool(8) as p:
        results=tqdm(p.map(args,G_SB.nodes))
    
    results_dict=reduce(lambda a, b: {**a, **b}, results)
    
    return results_dict    

    
if __name__=="__main__":   
    comprehensivePark_adjacentStations=postSQL2gpd(table_name='adjacent_stations',**args.db.db_info)
    comprehensivePark_adjacentStations_copy=comprehensivePark_adjacentStations.copy(deep=True)    
    with open(args.data.G_SB,'rb') as f:
        G_SB=pickle.load(f)             
    
    station2park_mean_time_cost_all=station2park_mean_time_cost(G_SB,comprehensivePark_adjacentStations_copy)
    with open(args.data.station2park_mean_time_cost_all_fn,'wb') as f:
         pickle.dump(station2park_mean_time_cost_all,f)   

