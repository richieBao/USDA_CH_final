# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 15:09:29 2023

@author: richie bao
"""

def comprehensivePark_adjacentStations_shortest_path_unique(w_dijkstra_item,args):
    comprehensivePark_adjacentStations_unique_list=args[0]
    node_id,(sp_length,sp_path)=w_dijkstra_item
    print(node_id)
    if node_id in comprehensivePark_adjacentStations_unique_list:        
        return {node_id:(sp_length,sp_path)}