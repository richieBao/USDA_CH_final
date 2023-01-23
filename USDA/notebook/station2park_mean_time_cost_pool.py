# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 20:10:18 2023

@author: richie bao
"""
def station2park_mean_time_cost_single(node,args):
    import networkx as nx
    
    comprehensivePark_adjacentStations,G_SB=args
    
    station2park_mean_time_cost_park={}
    station2park_mean_time_cost_park[node]={}
    for idx,row in comprehensivePark_adjacentStations.iterrows():
        adjacentStations=eval(row.adjacent_PointUid)
        node_min_sp_time_cost,_=nx.multi_source_dijkstra(G_SB,adjacentStations,node,weight='time_cost')
        station2park_mean_time_cost_park[node][row.Name_EN]=node_min_sp_time_cost
        
    return station2park_mean_time_cost_park
    
    
