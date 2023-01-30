# -*- coding: utf-8 -*-
"""
Created on Sat Jan 28 08:44:11 2023

@author: richie bao
"""
import mesa
from random import randrange,choice
import numpy as np
from scipy.signal import convolve2d
from matplotlib import pyplot as plt, colors
import math
import itertools 
import argparse
from tqdm import tqdm

parser=argparse.ArgumentParser(prog='Urban Sprawl_mesa(python)version',description='转换NetLogo的Sprawl Effect为Python 的Mesa版本')
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

class agent_patch(mesa.Agent):
    '''用于构建吸引力地图的智能体'''
    def __init__(self,pos,unique_id,attraction,color,model):
        super().__init__(unique_id,model)
        self.pos=pos
        self.attraction=attraction
        self.color=color
        
    def step(self):
        pass  
    
class agent_house(mesa.Agent):
    '''智能体——房屋（house）'''
    def __init__(self,pos,unique_id,model):
        super().__init__(unique_id,model)
        self.pos=pos  
        self.stay_counter=args.wait_between_seeking
        self.dropped=0
        
    def house_state_update(self):     
        '''更新智能体—房屋所在位置的吸引力值'''
        this_cell=self.model.grid.get_cell_list_contents([self.pos]) 
        turtle_attraction=[i for i in this_cell if type(i) is agent_patch][0]  
        if turtle_attraction.attraction <= self.model.max_attraction*2:
            turtle_attraction.attraction+=.05
        else:  
            turtle_attraction.attraction=0        
        
        self.stay_counter-=1
        if self.stay_counter <= 0:  
            # self.model.grid.remove_agent(self)
            self.dropped=1
        
    def step(self):    
        self.house_state_update()
    
class agent_seeker(mesa.Agent):
    '''智能体——搜寻着（seeker）'''
    def __init__(self,pos,unique_id,model):
        super().__init__(unique_id,model)
        self.pos=pos
        self.foundit=0
        self.patience_counter=args.seeker_patience      
                
    def seeking(self):
        '''智能体seeker每步（tick）行为'''
        if self.want_to_build():
            self.foundit=1
            self.generate_agent_house()
        else:
            if self.patience_counter>0:
                neighbors_filtered=self.turn_toward_attraction()
                if neighbors_filtered:
                    neighbors_choice=choice(neighbors_filtered)
                    self.model.grid.move_agent(self,neighbors_choice)
                    self.patience_counter-=1
                    
                    this_cell=self.model.grid.get_cell_list_contents([self.pos])
                    turtle_attraction=[i for i in this_cell if type(i) is agent_patch][0]
                    turtle_attraction.attraction+=.01
        
    def want_to_build(self):
        '''同NetLogo版的 to-report want-to-build? 部分'''
        this_cell=self.model.grid.get_cell_list_contents([self.pos])
        turtle_patch=[i for i in this_cell if type(i) is agent_patch][0]   
        selection_lst=[turtle_patch.attraction >= self.model.build_threshold, self.patience_counter==0]
        
        return choice(selection_lst)
    
    def generate_agent_house(self):
        '''在智能体seeker当前位置，生成一个智能体房屋（agent_house）'''
        turtle_house=agent_house(self.pos,f"house_{args.agent_house_uniqueIDs.pop()}",self.model)  
        self.model.schedule.add(turtle_house) 
        self.model.grid.place_agent(turtle_house, self.pos) 
        
    def turn_toward_attraction(self):
        '''根据当前位置单元和邻里8个单元的吸引力值，选择大于当前位置吸引力值的邻里单元为智能体seeker的移至位置单元'''
        neighbors=[i for i in self.model.grid.get_neighborhood(self.pos, moore=True,include_center=True,radius=1)]
        attraction_neighbors=[]
        for xy in neighbors:
            this_cell=self.model.grid.get_cell_list_contents([xy])
            turtle_attraction=[i for i in this_cell if type(i) is agent_patch][0]            
            attraction_neighbors.append(turtle_attraction.attraction)
            
        local_attraction=attraction_neighbors.pop(4) # 智能体当前位置值
        neighbors.pop(4)        
        neighbors_filter=[i>local_attraction for i in attraction_neighbors]        
        neighbors_selection=list(itertools.compress(neighbors,neighbors_filter))

        return neighbors_selection
    
    def step(self):  
      self.seeking()            

class sprawl_model(mesa.Model):
    def __init__(self,
                 width=args.width,
                 height=args.height,
                 max_attraction=args.max_attraction,
                 smoothness=args.smoothness,
                 share=args.share,
                 population_seeker=args.population_seeker):
        
        self.max_attraction=max_attraction
        self.build_threshold=math.floor(max_attraction/2)
        
        # 定义模拟网格为MultiGrid类型，每个单元格（cell）可以包含多个智能体对象
        self.grid=mesa.space.MultiGrid(width,height,torus=False)
        # 定义调度器（scheduler）类型为RandomActivation。每一步以随机顺序激活一个智能体，且每一步都会重新随机排序。
        # 等同于NetLogo的'ask agents'，且通常为默认行为
        self.schedule=mesa.time.RandomActivation(self)  

        # 以智能体方式，构建吸引力地图（topography of attractiveness ）。首先建立随机吸引子值2d数组（矩阵）
        attractiveness=self.diffuse_attractiveness(width,height,self.max_attraction,smoothness,share) 
        # 生成吸引力地图颜色值（对应吸引力二维矩阵值）
        attraction_colors=self.generate_attraction_colors(attractiveness,reverse=True)
        # 生成吸引力地图（即智能体agent_patch）
        self.setup_agent_patch(attractiveness,attraction_colors) 
        # 初始化智能体搜寻者（seeker）
        self.setup_agent_seeker(population_seeker,pos=(width//2,height//2))   

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

    def setup_agent_patch(self,attraction,colors):
        '''以智能体形式生成吸引力地图'''
        i=0
        for _, x, y in self.grid.coord_iter():
            pos=(x,y)
            turtle_attraction=agent_patch(pos,f"attraction_{i}",attraction[x,y],colors[x,y],self)
            self.schedule.add(turtle_attraction) 
            self.grid.place_agent(turtle_attraction,pos)
            i+=1
            
    def setup_agent_seeker(self,population,pos):
        '''初始化智能体搜寻者（seeker）'''
        for i in range(population):
            turtle_seeker=agent_seeker(pos,i,self)       #f"seeker_{i}"
            self.schedule.add(turtle_seeker)  
            self.grid.place_agent(turtle_seeker,pos)          

    def step(self):
        # self.datacollector.collect(self)        
        self.schedule.step()       
        
def agent_portrayal(agent):
    seekers_colors={0:'blue',1:'red'}
    dropped_colors={0:'yellow',1:'grey'}
    
    if agent is None:
        return 
    if type(agent) is agent_patch:
        portrayal={
            "Shape": "rect",
            "Color": agent.color,
            "Filled": "true",
            "Layer": 0,
            "w": 1,
            "h": 1,
            "text":agent.attraction,
            # "text_color":'grey',
        }         
        
    elif type(agent) is agent_seeker:
        portrayal = {
            "Shape": "circle",
            "Color": seekers_colors[agent.foundit],
            "Filled": "true",
            "Layer": 2,
            "text": agent.patience_counter,
            "r": 0.5,
            "scale": 2,
        }   
        
    elif type(agent) is agent_house:
        portrayal = {
            "Shape": "circle", 
            "Color": dropped_colors[agent.dropped],
            "Filled": "true",
            "Layer": 1,
            "text": agent.stay_counter,
            "r": 1,
            "scale": 2,
        }        
        
    return portrayal     

if __name__=="__main__":    
    grid=mesa.visualization.CanvasGrid(agent_portrayal,args.height,args.width,1000,1000)
    server=mesa.visualization.ModularServer(
        sprawl_model,
        [grid],
        "Sprawl Model_by Mesa",
        # {"width":args.width, "height":args.height}
        )
    server.launch(port=8526)    
    #%%
    # model=sprawl_model()
    # for i in tqdm(range(10)):
    #     model.step() 
    #%%
    