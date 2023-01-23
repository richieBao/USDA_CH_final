# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 15:09:29 2023

@author: richie bao
"""
import pickle
from util_misc import AttrDict
from database import postSQL2gpd,gpd2postSQL

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

comprehensivePark_adjacentStations=postSQL2gpd(table_name='adjacent_stations',**args.db.db_info)
with open(args.data.G_SB,'rb') as f:
    G_SB=pickle.load(f)   
    
flatten_lst=lambda lst: [m for n_lst in lst for m in flatten_lst(n_lst)] if type(lst) is list else [lst]  
    
def comprehensivePark_adjacentStations_shortest_path(G_SB,comprehensivePark_adjacentStations):
    from multiprocessing import Pool    
    from functools import partial
    from functools import reduce
    from comprehensivePark_adjacentStations_shortest_path_pool import comprehensivePark_adjacentStations_shortest_path_unique
    import numpy as np
    import networkx as nx
    
    comprehensivePark_adjacentStations_unique_list=np.unique(flatten_lst([eval(i) for i in comprehensivePark_adjacentStations.adjacent_PointUid.to_list()]))
    w_dijkstra=nx.all_pairs_dijkstra(G_SB,weight='time_cost')
    
    args=partial(comprehensivePark_adjacentStations_shortest_path_unique, args=[comprehensivePark_adjacentStations_unique_list])
    print('-'*50)
    with Pool(8) as p:
        results=p.imap(args,w_dijkstra,chunksize=8)
    
    results_dict=reduce(lambda a, b: {**a, **b}, results)
    return results_dict
    

if __name__=="__main__":
    comprehensivePark_adjacentStations_shortest_path_dict=comprehensivePark_adjacentStations_shortest_path(G_SB,comprehensivePark_adjacentStations)