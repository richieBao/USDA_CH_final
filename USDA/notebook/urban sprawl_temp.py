import mesa
from random import randrange,choice
import numpy as np
from scipy.signal import convolve2d
from matplotlib import pyplot as plt, colors
import math
import itertools 

agent_seeker_uniqueIDs=list(range(0,10000))
agent_house_uniqueIDs=list(range(10000,20000))

class agent_attraction(mesa.Agent):
    def __init__(self,pos,model,attraction,color):
        super().__init__(pos,model)
        self.attraction=attraction
        self.color=color
        
    def step(self):
        #print(self.unique_id,self.attraction)
        pass    
    
class agent_house(mesa.Agent):
    def __init__(self,pos,unique_id,model,build=0,wait_between_seeking=15):
        super().__init__(unique_id,model)
        self.pos=pos      
        self.build=build
        self.stay_counter=wait_between_seeking  
        self.dropped=0
        # print('@@@@@@@@@@@',self.model)
        
    def stay_counter_reduction(self):
        self.stay_counter-=1
        if self.stay_counter<=0:     
            turtle_seeker=agent_seeker(self.pos,self.model.agent_seeker_uniqueIDs.pop(),self.model)
            self.model.schedule.add(turtle_seeker)  
            self.model.grid.place_agent(turtle_seeker, self.pos)    
            
            self.dropped=1
            #print('+--------------------')
            #print(self)
            self.model.grid.remove_agent(self)
           # print('+###################')
           
    def local_attraction_adjustment(self):
        
        this_cell=self.model.grid.get_cell_list_contents([self.pos]) #[self.pos]
        attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]  
        if attraction_turtle.attraction<=self.model.max_attraction*2:
            attraction_turtle.attraction+=.05
        else:  
            attraction_turtle.attraction=0
            
                
    def step(self):
        
        # try:
        self.local_attraction_adjustment()
        self.stay_counter_reduction()  
        
        # except:
        #     pass
        
class agent_seeker(mesa.Agent):
    def __init__(self,pos,unique_id,model,seeker_patience=60,seeker_search_angle=[0,1,2,3,4,5,6],seeker_or_house=0):
        super().__init__(unique_id,model)
        self.unique_id=unique_id
        self.pos=pos
        self.build_threshold=math.floor(self.model.max_attraction/2)
        self.seeker_patience=seeker_patience
        self.patience_counter=seeker_patience
        self.seeker_or_house=seeker_or_house # 0:seeker,1:house
        self.seeker_search_angle=seeker_search_angle       
        
        # this_cell=self.model.grid.get_cell_list_contents([self.pos])
        # attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]
        # self.attraction=attraction_turtle.attraction        
        
    def want_to_build(self):
        this_cell=self.model.grid.get_cell_list_contents([self.pos])
        attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]          
        
        selection_lst=[attraction_turtle.attraction >=self.build_threshold,self.patience_counter==0]
        # print(selection_lst)
        return choice(selection_lst)
        # return self.attraction >=self.build_threshold
    
    def turn_toward_attraction(self):        
        self.neighbors=[i for i in self.model.grid.get_neighborhood(self.pos, moore=True,include_center=False,radius=1)]
        #print(self.neighbors)
        #xy_ahead,xy_left,xy_right,xy_behind=self.neighbors
        attraction_neighbors=[]
        for xy in self.neighbors:
            this_cell=self.model.grid.get_cell_list_contents([xy])
            attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]            
            attraction_neighbors.append(attraction_turtle.attraction)
        #print(attraction_neighbors)
        attraction_ahead=attraction_neighbors[1]
        
        orders=[0,3,5,6,7,4,2]
        try:
            attraction_lst=[attraction_neighbors[i] for i in orders]
            neighbors_sorted=[self.neighbors[i] for i in orders]        
            # attraction_left=attraction_lst[self.seeker_search_angle]
            # attraction_right=attraction_lst[-self.seeker_search_angle]              
        
            # if attraction_right>attraction_left and attraction_right>attraction_ahead:
            #     self.model.grid.move_agent(self,neighbors_sorted[-self.seeker_search_angle])
            #     self.pos=neighbors_sorted[-self.seeker_search_angle]
            # elif attraction_left>attraction_ahead:
            #     self.model.grid.move_agent(self,neighbors_sorted[self.seeker_search_angle])
            #     self.pos=neighbors_sorted[self.seeker_search_angle]
            
            next_xy=neighbors_sorted[choice(self.seeker_search_angle)]
            self.model.grid.move_agent(self,next_xy)
            self.pos=next_xy
            
            # new_neighbors=[i for i in self.model.grid.get_neighborhood(self.pos, moore=True,include_center=False,radius=1)]
            # self.model.grid.move_agent(self,new_neighbors[1])
            # self.pos=new_neighbors[1]
        except:
            pass
            # x=self.random.randrange(self.model.width//2-10,self.model.width//2+10,)
            # y=self.random.randrange(self.model.height//2-10,self.model.height//2+10)
            # self.model.grid.move_agent(self,(x,y))
            # self.pos=((x,y))
        
    def seeker4house(self):
        # print( self.attraction,self.build_threshold)
        # print('###',self.want_to_build(),self.seeker_or_house)
        if self.want_to_build() and self.seeker_or_house==0:            
            self.seeker_or_house=1
            # self.stay_counter=self.wait_between_seeking
            #self.model.grid.place_agent(agent_seeker(self.pos,99,seeker_or_house=1),pos=self.pos)
            # print('---',self.stay_counter)
        else:
            if self.patience_counter>0:
                #print('#',self.pos)
                self.turn_toward_attraction()
                #print('-',self.pos)
                self.patience_counter-=1
                this_cell=self.model.grid.get_cell_list_contents([self.pos])
                attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]
                # print('~~~',attraction_turtle.attraction)
                attraction_turtle.attraction+=.01
                # self.attraction=attraction_turtle.attraction
                # this_cell=self.model.grid.get_cell_list_contents([self.pos])
                # attraction_turtle=[i for i in this_cell if type(i) is agent_attraction][0]
                # print('***',attraction_turtle.attraction)

                
            # self.stay_counter-=1
            # if self.stay_counter<=0:
            #     self.seeker_or_house=0
            #     self.patience_counter=self.seeker_patience
     
    def seeker2house(self):
        if self.seeker_or_house==1: #and self.stay_counter>0                          
            turtle_house=agent_house(self.pos,self.model.agent_house_uniqueIDs.pop(),self.model)  
            self.model.schedule.add(turtle_house) 
            self.model.grid.place_agent(turtle_house, self.pos)  
            
            # self.model.grid.remove_agent(self)
            
    
    def step(self):  
        #print(self.unique_id,self.patience_counter)
        # try:
        self.seeker4house()
        self.seeker2house()
        # except:
        #     pass
        # print('-'*50,self.seeker_or_house,self.stay_counter)
        #print(self.pos)
        #self.update_agent_seeker()

flatten_lst=lambda lst: [m for n_lst in lst for m in flatten_lst(n_lst)] if type(lst) is list else [lst]

class sprawl_model(mesa.Model):
    def __init__(self,width=34,height=34,smoothness=14,max_attraction=30,share=0.4,population=200):
        self.width=width
        self.height=height
        self.smoothness=smoothness
        self.max_attraction=max_attraction
        self.share=share
        self.population=population
        self.agent_seeker_uniqueIDs=list(range(0,100000))
        self.agent_house_uniqueIDs=list(range(100000,200000))
        
        self.grid=mesa.space.MultiGrid(width,height,torus=False)
        self.schedule=mesa.time.RandomActivation(self)   
        
        diffusion_attraction=self.diffuse_array(self.width,self.height,self.max_attraction,self.smoothness,self.share)  
        attraction_colors=self.generate_colors(diffusion_attraction)
        # print(diffusion_attraction)
        self.setup_agent_attraction(diffusion_attraction,attraction_colors)        
        self.setup_agent_seeker()     
        
        # agent_build_turtule=agent_house((20,20),'agent_build',self)
        # self.schedule.add(agent_build_turtule)
        # self.grid.place_agent(agent_build_turtule, (20, 20))
        #self.datacollector=mesa.DataCollector(model_reporters={},
                                              #agent_reporters={'attraction_attraction':lambda agent_attraction:agent_attraction.attraction,
                                                              # 'attraction_color':lambda agent_attraction:agent_attraction.color,               
            #'seekers_patience_counter':lambda agent_seeker:agent_seeker.patience_counter
             #}) 
             
        
        
    def generate_colors(self,array):
        cmap=plt.cm.Greens
        norm=colors.Normalize() # vmin=0,vmax=100
        color=[colors.to_hex(c) for c in  cmap(norm(array.reshape(-1)))]
        color.reverse()
        return np.reshape(color,array.shape)    
        
    def diffuse_array(self,width,height,max_attraction=30,smoothness=14,share=0.4):  
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
        #print(np.sum(attraction),np.sum(diffusion_attraction))
        #print(attraction.shape,diffusion_attraction.shape)   
        #print('-'*50)
        return diffusion_attraction        

    def setup_agent_attraction(self,attraction,colors):
        for _, x, y in self.grid.coord_iter():
            turtle_attraction=agent_attraction((x,y),self,attraction[x,y],colors[x,y])
            self.schedule.add(turtle_attraction) 
            self.grid.place_agent(turtle_attraction, (x,y))
              
            
    def setup_agent_seeker(self):
        x=self.width//2
        y=self.height//2
        for i in range(self.population):
            turtle_seeker=agent_seeker((x,y),self.agent_seeker_uniqueIDs.pop(),self)       
            self.schedule.add(turtle_seeker)  
            self.grid.place_agent(turtle_seeker, (x,y))          
        
    def update_agent_seeker(self):        
        contents=self.grid.coord_iter()        
        for content in contents:
            pos_=content[-2:]
            agent_seeker_turtle=None
            agent_house_turtle=None
            for i in content[:-2]:
                for j in i:
                    if type(j) is agent_seeker: 
                        agent_seeker_turtle=j
                    elif type(j) is agent_house: 
                        agent_house_turtle=j       
                if agent_seeker_turtle: 
                    if agent_seeker_turtle.seeker_or_house==1 and agent_seeker_turtle.stay_counter>0:       #  and agent_house_turtle.build==0                      
                        turtle_house=agent_house(pos_,self.agent_house_uniqueIDs.pop(),self,build=1)  
                        self.schedule.add(turtle_house) 
                        self.grid.place_agent(turtle_house, pos_)                              
                        # print('!!!!!!')             
                        
                elif agent_seeker_turtle and agent_house_turtle:   
                    print('+---------------')  
                    if agent_seeker_turtle.seeker_or_house==1 and agent_seeker_turtle.stay_counter<=0:                        
                        self.grid.remove_agent(pos_)
                        turtle_seeker=agent_seeker(pos_,self.agent_seeker_uniqueIDs.pop(),self) 
                        self.schedule.add(turtle_seeker)  
                        self.grid.place_agent(turtle_seeker, pos_)                             
                        print('??????')

   

    def step(self):
        #self.datacollector.collect(self)        
        self.schedule.step()
        #self.update_agent_seeker()
        
        
def agent_portrayal(agent):
    seeker_house_colors={1:'red',0:'blue'}
    dropped_colors={0:'yellow',1:'grey'}
    
    if agent is None:
        return 
    if type(agent) is agent_attraction:
        portrayal = {
            "Shape": "rect",
            "Color": agent.color,
            "Filled": "true",
            "Layer": 0,
            "w": 1,
            "h": 1,
        }          
    elif type(agent) is agent_seeker:
        portrayal = {
            "Shape": "circle",
            "Color": seeker_house_colors[agent.seeker_or_house],
            "Filled": "true",
            "Layer": 2,
            #"text": agent.unique_id,
            "r": 0.5,
            "scale": 2,
        }    
        
    elif type(agent) is agent_house:
        portrayal = {
            "Shape": "circle", #arrowHead
            "Color": dropped_colors[agent.dropped],
            "Filled": "true",
            "Layer": 1,
            #"text": agent.unique_id,
            "r": 1,
            "scale": 2,
        }        
        
    return portrayal        
        

if __name__=="__main__":
    width=34#100#34
    height=34#100#34
    
    grid=mesa.visualization.CanvasGrid(agent_portrayal, height, width, 1000, 1000)
    server=mesa.visualization.ModularServer(
        sprawl_model,
        [grid],
        "Sprawl Model",
        {"width":width, "height":height}
        )
    
    server.launch(port=8525)            
    
    #%%
    # model=sprawl_model()
    # for i in range(300):
    #     model.step()    
    #%%
    