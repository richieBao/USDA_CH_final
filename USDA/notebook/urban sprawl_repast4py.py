#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 10:34:57 2023

@author: richie bao
"""
import sys
import math
import numpy as np
from typing import Dict, Tuple
from mpi4py import MPI
from dataclasses import dataclass

import numba
from numba import int32, int64
from numba.experimental import jitclass

from repast4py import core, space, schedule, logging, random
from repast4py import context as ctx
from repast4py.parameters import create_args_parser, init_params

from repast4py.space import ContinuousPoint as cpt
from repast4py.space import DiscretePoint as dpt
from repast4py.space import BorderType, OccupancyType

from scipy.signal import convolve2d
from random import randrange,choice
from matplotlib import pyplot as plt, colors
import argparse

parser=argparse.ArgumentParser(prog='Urban Sprawl_repast4Py(python)version',description='转换NetLogo的Sprawl Effect为Python 的Mesa版本')
parser.add_argument('--width', default=34, type=int,help='模拟网格宽')
parser.add_argument('--height', default=34, type=int,help='模拟网格高')
parser.add_argument('--max_attraction', default=15, type=int,help='吸引力最大值，取值范围 0~30')
parser.add_argument('--smoothness', default=15, type=int,help='卷积（光滑）次数，取值范围 1~20')
parser.add_argument('--share', default=.4, type=float,help='用于卷积核的分配因子（对应NetLogo版的diffuse参数），取值范围 0~1')
parser.add_argument('--population_seeker', default=200, type=int,help='智能体搜寻着（agent_seeker）初始化数量，取值范围 1~750')
parser.add_argument('--seeker_patience', default=60, type=int,help='智能体搜寻者（agent_seeker）的寻找耐心程度，取值范围 0~120')
parser.add_argument('--wait_between_seeking', default=15, type=int,help='智能体搜寻者（agent_seeker）的寻找耐心程度，取值范围 5~60')
parser.add_argument('--agent_house_uniqueIDs', default=list(range(0,100000)), type=list,help='用于智能体房屋（agent_house）的ID标识')

args=parser.parse_args([])

model=None
agent_cache = {}

#def restore_agent(agent_data: Tuple):
#    """Creates an agent from the specified agent_data.
#
#    This is used to re-create agents when they have moved from one MPI rank to another.
#    The tuple returned by the agent's save() method is moved between ranks, and restore_agent
#    is called for each tuple in order to create the agent on that rank. Here we also use
#    a cache to cache any agents already created on this rank, and only update their state
#    rather than creating from scratch.
#
#    Args:
#        agent_data: the data to create the agent from. This is the tuple returned from the agent's save() method
#                    where the first element is the agent id tuple, and any remaining arguments encapsulate
#                    agent state.
#    """
#    uid = agent_data[0]
#    print('+-----+')
#    # 0 is id, 1 is type, 2 is rank
#    if uid[1] == Human.TYPE:
#        if uid in agent_cache:
#            h = agent_cache[uid]
#        else:
#            h = Human(uid[0], uid[2])
#            agent_cache[uid] = h
#
#        # restore the agent state from the agent_data tuple
#        h.infected = agent_data[1]
#        h.infected_duration = agent_data[2]
#        return h
#    else:
#        # note that the zombie has no internal state
#        # so there's nothing to restore other than
#        # the Zombie itself
#        if uid in agent_cache:
#            return agent_cache[uid]
#        else:
#            z = Zombie(uid[0], uid[2])
#            agent_cache[uid] = z
#            return z

@numba.jit((int64[:], int64[:]), nopython=True)
def is_equal(a1, a2):
    return a1[0] == a2[0] and a1[1] == a2[1]

spec=[
    ('mo', int32[:]),
    ('no', int32[:]),
    ('xmin', int32),
    ('ymin', int32),
    ('ymax', int32),
    ('xmax', int32)
]

@jitclass(spec)
class GridNghFinder:

    def __init__(self, xmin, ymin, xmax, ymax):
        self.mo = np.array([-1, 0, 1, -1, 0, 1, -1, 0, 1], dtype=np.int32)
        self.no = np.array([1, 1, 1, 0, 0, 0, -1, -1, -1], dtype=np.int32)
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def find(self, x, y):
        xs = self.mo + x
        ys = self.no + y

        xd = (xs >= self.xmin) & (xs <= self.xmax)
        xs = xs[xd]
        ys = ys[xd]

        yd = (ys >= self.ymin) & (ys <= self.ymax)
        xs = xs[yd]
        ys = ys[yd]

        return np.stack((xs, ys, np.zeros(len(ys), dtype=np.int32)), axis=-1)


@dataclass
class Info:
    """
    Dataclass used by repast4py aggregate logging to record
    the info from agent houses after each tick.
    """
    house_total: int = 0
    seeker_total: int = 0
    
class Patch(core.Agent):
    
    TYPE=0
    
    def __init__(self, a_id: int, rank: int, attraction: float):
        super().__init__(id=a_id, type=Patch.TYPE, rank=rank)
        self.attraction=attraction    
            
class Seeker(core.Agent):
    """The Seeker Agent

    Args:
        a_id: a integer that uniquely identifies this Seeker on its starting rank
        rank: the starting MPI rank of this Seeker.
    """

    TYPE=1

    def __init__(self, a_id: int, rank: int):
        super().__init__(id=a_id, type=Seeker.TYPE, rank=rank)
        self.infected=False
        self.foundit=0
        self.patience_counter=args.seeker_patience        
        
    def seeking(self):
        '''智能体seeker每步（tick）行为'''
        self.grid=model.grid
        self.pt=self.grid.get_location(self) 
        self.objs=self.grid.get_agents(self.pt)

        if self.want_to_build():
            self.foundit=1
            self.generate_agent_house()
        else:
            if self.patience_counter>0:
                neighbors_filtered=self.turn_toward_attraction()
                if neighbors_filtered:
                    neighbors_choice=choice(neighbors_filtered)
                    next_pt=dpt(neighbors_choice[0], neighbors_choice[1])
                    self.grid.move(self, next_pt)

                    for obj in self.grid.get_agents(next_pt):
                        if obj.uid[1]==Patch.TYPE:
                            obj.attraction+=.01                        
        
    def want_to_build(self):  
        '''同NetLogo版的 to-report want-to-build? 部分'''
        patch=[obj for obj in self.objs if obj.uid[1]==Patch.TYPE][0]        
        selection_lst=[patch.attraction >= model.build_threshold, self.patience_counter==0]
        
        return choice(selection_lst)
        
    def generate_agent_house(self):
        '''在智能体seeker当前位置，生成一个智能体房屋（house）'''
        house=House(model.house_id,model.rank)
        model.context.add(house)
        model.move(house, self.pt.x, self.pt.y)        
        
        model.house_id+=1
        
    def turn_toward_attraction(self):       
        '''根据当前位置单元和邻里8个单元的吸引力值，选择大于当前位置吸引力值的邻里单元为智能体seeker的移至位置单元'''
        local_attraction=[obj.attraction for obj in self.objs if obj.uid[1]==Patch.TYPE][0]

        nghs=model.ngh_finder.find(self.pt.x,self.pt.y)
        at=dpt(0,0)
        attraction_neighbors=[]
        for ngh in nghs:
            at._reset_from_array(ngh)
            for obj in self.grid.get_agents(at):
                if obj.uid[1]==Patch.TYPE:
                    attraction_neighbors.append([ngh,obj.attraction])        
  
        neighbors_filter=[i for i in attraction_neighbors if i[1]>local_attraction]      
        neighbors_selection=[i[0] for i in neighbors_filter]
        
        return neighbors_selection       
            
    def step(self):
        self.seeking()         

class House(core.Agent):
    
    TYPE=2
    
    def __init__(self, a_id: int, rank: int):
        super().__init__(id=a_id, type=House.TYPE, rank=rank)
        self.stay_counter=args.wait_between_seeking
        self.dropped=0
        
    def house_state_update(self):     
        '''更新智能体—房屋所在位置的吸引力值'''
        grid=model.grid
        pt=grid.get_location(self)        
        patch=[obj for obj in grid.get_agents(pt) if obj.uid[1]==Patch.TYPE][0]

        if patch.attraction <= args.max_attraction*2:
            patch.attraction+=.05
        else:
            patch.attraction=0

        self.stay_counter-=1
        if self.stay_counter <= 0:
            self.dropped=1           
                    
    def step(self):
        self.house_state_update()       
        
class Model:

    def __init__(self, comm, params):
        
        self.build_threshold=math.floor(args.max_attraction/2)
        
        self.comm=comm
        self.context=ctx.SharedContext(comm)
        self.rank=self.comm.Get_rank() # Get the rank that is executing this code, the current process rank
        
        self.runner=schedule.init_schedule_runner(comm)
        self.runner.schedule_repeating_event(1, 1, self.step)   
        self.runner.schedule_stop(params['stop.at'])
        self.runner.schedule_end_event(self.at_end)        
        
        # BoundingBox(xmin=0, xextent=34 ymin=0, yextent=34, zmin=0, zextent=0)
        box=space.BoundingBox(0, params['world.width'], 0, params['world.height'], 0, 0)
        self.grid=space.SharedGrid('grid', 
                                    bounds=box, 
                                    borders=BorderType.Sticky, 
                                    occupancy=OccupancyType.Multiple,
                                    buffer_size=2, 
                                    comm=comm)   
        self.context.add_projection(self.grid)        
        self.space=space.SharedCSpace('space', 
                                      bounds=box, 
                                      borders=BorderType.Sticky, 
                                      occupancy=OccupancyType.Multiple,
                                      buffer_size=2, 
                                      comm=comm, 
                                      tree_threshold=100)        
        self.context.add_projection(self.space)        
        self.ngh_finder=GridNghFinder(0, 0, box.xextent, box.yextent)
        
        self.info=Info()
        loggers=logging.create_loggers(self.info, op=MPI.SUM, rank=self.rank)
        self.data_set=logging.ReducingDataSet(loggers, self.comm, params['info_file'])
        
        self.house_pts_set=open(params['house_pts_file'],'wb')
        
        world_size=comm.Get_size() # Get the number of process ranks over which the simulation is distributed
        total_seeker_count=params['seeker.count']
        pp_seeker_count=int(total_seeker_count / world_size)

        if self.rank < total_seeker_count % world_size:
            pp_seeker_count += 1 
            
        attractiveness=self.diffuse_attractiveness(params['world.width'],params['world.height'],args.max_attraction,args.smoothness,args.share) 
#        attraction_colors=self.generate_attraction_colors(attractiveness,reverse=True)
        with open(params['attraction_file'],'wb') as f:
            np.save(f,attractiveness)
        
        
        local_bounds=self.space.get_local_bounds()      
        
        x_lst=range(0,local_bounds.xextent,1)
        y_lst=range(0,local_bounds.yextent,1)
        xy_meshgrid=np.stack(np.meshgrid(x_lst,y_lst),axis=-1)
        for i,xy in enumerate(xy_meshgrid.reshape(-1,2)):
            patch=Patch(i,self.rank,attractiveness[xy[0],xy[1]])
            self.context.add(patch)
            self.move(patch, xy[0],xy[1])
        
        for i in range(pp_seeker_count):
            seeker=Seeker(i, self.rank)
            self.context.add(seeker)
            x=local_bounds.xextent//2
            y=local_bounds.yextent//2
            self.move(seeker, x, y)
        
#        house=House(0,self.rank)
#        self.context.add(house)
#        self.move(house, 0, 0)
        self.house_id=1            
        
        

    def step(self):
        tick = self.runner.schedule.tick 
        self.log_info(tick)
#        self.context.synchronize(restore_agent)
        for seeker in self.context.agents(Seeker.TYPE):
            seeker.step()    
            
        for house in self.context.agents(House.TYPE):
            house.step()              
            
#        try:   
#            for house in self.context.agents(House.TYPE):
#                house.step()      
#                if house.dropped==1:
#                    model.remove_agent(house)
#        except:
#            print('No agent House~')
        
    def log_info(self,tick):
        try:
            num_agents=self.context.size([Seeker.TYPE, House.TYPE])    
            self.info.house_total=num_agents[House.TYPE]
            self.info.seeker_total=num_agents[Seeker.TYPE]
            pt_house_lst=[]
            for house in self.context.agents(House.TYPE):
                pt_house=self.grid.get_location(house)
                pt_house_lst.append([pt_house.x,pt_house.y])     
            self.data_set.log(tick)      
            
            pt_house_lst_unique=list(set(tuple(sub) for sub in pt_house_lst))
            pt_house_array=np.array(pt_house_lst_unique)
            np.save(self.house_pts_set,pt_house_array)
            
            # Do the cross-rank reduction manually and print the result
            if tick % 1 == 0:              
                house_total=np.zeros(1, dtype='int64')
                seeker_total=np.zeros(1, dtype='int64')   
                self.comm.Reduce(np.array([self.info.house_total], dtype='int64'), house_total, op=MPI.SUM, root=0)
                self.comm.Reduce(np.array([self.info.seeker_total], dtype='int64'), seeker_total, op=MPI.SUM, root=0)
                if (self.rank == 0):
                    print("Tick: {}, house_total: {}, seeker_total: {}".format(tick, house_total[0], seeker_total[0]),
                          flush=True)      
        except:
            print('No agent House~')            

    def at_end(self):
        self.data_set.close()
        self.house_pts_set.close()

    def move(self, agent, x, y):
        # timer.start_timer('space_move')
        self.space.move(agent, cpt(x, y))
        # timer.stop_timer('space_move')
        # timer.start_timer('grid_move')
        self.grid.move(agent, dpt(int(math.floor(x)), int(math.floor(y))))
        # timer.stop_timer('grid_move')

    def diffuse_attractiveness(self,width,height,max_attraction,smoothness,share):  
        '''用二维卷积的方式实现NetLogo中的diffuse方法；用循环的方式实现NetLogo中的repeat方法，完成吸引力地图二维矩阵值的随机生成'''
        attraction=np.random.randint(0,max_attraction,size=(width,height),dtype=np.uint32)
        share_percent=share/8
        kernel=np.array([[share_percent,share_percent,share_percent],
                         [share_percent, 1-share,share_percent],
                         [share_percent,share_percent,share_percent]]) 
        diffusion_attraction=np.copy(attraction)
        i=0
        
        while i<smoothness:
            diffusion_attraction=convolve2d(diffusion_attraction,kernel,mode='same',boundary='wrap')
            i+=1

        return diffusion_attraction 

    def generate_attraction_colors(self,array,cmap=plt.cm.Greens,reverse=False):
        '''根据矩阵值对应生成颜色值'''
        norm=colors.Normalize() # vmin，vmax配置为默认值
        color=[colors.to_hex(c) for c in cmap(norm(array.reshape(-1)))]
        if reverse:
            color.reverse()
        return np.reshape(color,array.shape) 
          
    def run(self):
        self.runner.execute()


def run(params: Dict):
    """Creates and runs the urban sprawl Model.

    Args:
        params: the model input parameters
    """
    global model
    model=Model(MPI.COMM_WORLD, params)
    model.run()

if __name__ == "__main__":
    params={
            'random.seed': 42,
            'stop.at': 600.0, 
            'seeker.count': 200,
            'world.width': 34,
            'world.height': 34,
            'run.number': 1,
            'info_file': 'output/agent_house.csv',
            'house_pts_file': 'output/house_pts.npy',
            'attraction_file': 'output/attraction.npy',
            }
    run(params)        