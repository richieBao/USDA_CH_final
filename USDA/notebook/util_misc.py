# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 23:37:20 2021

@author: Richie Bao-caDesign设计(cadesign.cn)
"""

class DisplayablePath(object):
    '''
    class - 返回指定路径下所有文件夹及其下文件的结构。代码未改动，迁移于'https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python'
    '''
    
    display_filename_prefix_middle = '├──'
    display_filename_prefix_last = '└──'
    display_parent_prefix_middle = '    '
    display_parent_prefix_last = '│   '

    def __init__(self, path, parent_path, is_last):
        from pathlib import Path
        
        self.path = Path(str(path))
        self.parent = parent_path
        self.is_last = is_last
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    @property
    def displayname(self):
        if self.path.is_dir():
            return self.path.name + '/'
        return self.path.name

    @classmethod
    def make_tree(cls, root, parent=None, is_last=False, criteria=None):
        from pathlib import Path
        
        root = Path(str(root))
        criteria = criteria or cls._default_criteria

        displayable_root = cls(root, parent, is_last)
        yield displayable_root

        children = sorted(list(path
                               for path in root.iterdir()
                               if criteria(path)),
                          key=lambda s: str(s).lower())
        count = 1
        for path in children:
            is_last = count == len(children)
            if path.is_dir():
                yield from cls.make_tree(path,
                                         parent=displayable_root,
                                         is_last=is_last,
                                         criteria=criteria)
            else:
                yield cls(path, displayable_root, is_last)
            count += 1

    @classmethod
    def _default_criteria(cls, path):
        return True

    @property
    def displayname(self):
        if self.path.is_dir():
            return self.path.name + '/'
        return self.path.name

    def displayable(self):
        if self.parent is None:
            return self.displayname

        _filename_prefix = (self.display_filename_prefix_last
                            if self.is_last
                            else self.display_filename_prefix_middle)

        parts = ['{!s} {!s}'.format(_filename_prefix,
                                    self.displayname)]

        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.display_parent_prefix_middle
                         if parent.is_last
                         else self.display_parent_prefix_last)
            parent = parent.parent

        return ''.join(reversed(parts))
    
def filePath_extraction(dirpath,fileType):
    import os
    
    '''
    funciton  -以所在文件夹路径为键，值为包含该文件夹下所有文件名的列表。文件类型可以自行定义 
    
    Paras:
        dirpath - 根目录，存储所有待读取的文件
        fileType - 待读取文件的类型
    '''
    filePath_Info={}
    i=0
    for dirpath,dirNames,fileNames in os.walk(dirpath): #os.walk()遍历目录，使用help(os.walk)查看返回值解释
       i+=1
       if fileNames: #仅当文件夹中有文件时才提取
           tempList=[f for f in fileNames if f.split('.')[-1] in fileType]
           if tempList: #剔除文件名列表为空的情况，即文件夹下存在不为指定文件类型的文件时，上一步列表会返回空列表[]
               filePath_Info.setdefault(dirpath,tempList)
    return filePath_Info    

def start_time():
    import datetime
    '''
    function-计算当前时间
    '''
    start_time=datetime.datetime.now()
    print("start time:",start_time)
    return start_time

def duration(start_time):
    import datetime
    '''
    function-计算持续时间
    
    Paras:
    start_time - 开始时间
    '''
    end_time=datetime.datetime.now()
    print("end time:",end_time)
    duration=(end_time-start_time).seconds/60
    print("Total time spend:%.2f minutes"%duration)

def is_outlier(data,threshold=3.5):
    import numpy as np
    '''
    function-判断异常值
        
    Params:
        data - 待分析的数据，列表或者一维数组
        threshold - 判断是否为异常值的边界条件    
    '''
    MAD=np.median(abs(data-np.median(data)))
    modified_ZScore=0.6745*(data-np.median(data))/MAD
    #print(modified_ZScore)
    is_outlier_bool=abs(modified_ZScore)>threshold    
    return is_outlier_bool,data[~is_outlier_bool]

def print_html(df,row_numbers=5):
    from IPython.display import HTML
    '''
    function - 在Jupyter中打印DataFrame格式数据为HTML
    
    Paras:
        df - 需要打印的DataFrame或GeoDataFrame格式数据
        row_numbers - 打印的行数，如果为正，从开始打印如果为负，从末尾打印
     '''
    if row_numbers>0:
        return HTML(df.head(row_numbers).to_html())
    else:
        return HTML(df.tail(abs(row_numbers)).to_html())
    
flatten_lst=lambda lst: [m for n_lst in lst for m in flatten_lst(n_lst)] if type(lst) is list else [lst]

def kneed_lineGraph(x,y):
    import matplotlib.pyplot as plt
    from data_generator import DataGenerator
    from knee_locator import KneeLocator
    '''
    function - 绘制折线图，及其拐点。需调用kneed库的KneeLocator，及DataGenerator文件

    Paras:
    x - 横坐标，用于横轴标签
    y - 纵坐标，用于计算拐点    
    '''
    #如果调整图表样式，需调整knee_locator文件中的plot_knee（）函数相关参数
    kneedle=KneeLocator(x, y, curve='convex', direction='decreasing')
    print('曲线拐点（凸）：',round(kneedle.knee, 3))
    print('曲线拐点（凹）：',round(kneedle.elbow, 3))
    kneedle.plot_knee(figsize=(8,8))
    
def imgs_layoutShow(imgs_root,imgsFn_lst,columns,scale,figsize=(15,10)):
    import math,os
    import matplotlib.pyplot as plt
    from PIL import Image
    '''
    function - 显示一个文件夹下所有图片，便于查看。
    
    Paras:
        imgs_root - 图像所在根目录
        imgsFn_lst - 图像名列表
        columns - 列数
    '''
    rows=math.ceil(len(imgsFn_lst)/columns)
    fig,axes=plt.subplots(rows,columns,sharex=True,sharey=True,figsize=figsize)   #布局多个子图，每个子图显示一幅图像
    ax=axes.flatten()  #降至1维，便于循环操作子图
    for i in range(len(imgsFn_lst)):
        img_path=os.path.join(imgs_root,imgsFn_lst[i]) #获取图像的路径
        img_array=Image.open(img_path) #读取图像为数组，值为RGB格式0-255        
        img_resize=img_array.resize([int(scale * s) for s in img_array.size] ) #传入图像的数组，调整图片大小
        ax[i].imshow(img_resize)  #显示图像
        ax[i].set_title(i+1)
    fig.tight_layout() #自动调整子图参数，使之填充整个图像区域  
    fig.suptitle("images show",fontsize=14,fontweight='bold',y=1.02)
    plt.show()    
    
def imgs_layoutShow_FPList(imgs_fp_list,columns,scale,figsize=(15,10)):
    import math,os
    import matplotlib.pyplot as plt
    from PIL import Image
    '''
    function - 显示一个文件夹下所有图片，便于查看。

    Paras:
        imgs_root - 图像所在根目录
        imgsFn_lst - 图像名列表
        columns - 列数
    '''
    rows=math.ceil(len(imgs_fp_list)/columns)
    fig,axes=plt.subplots(rows,columns,figsize=figsize,)   #布局多个子图，每个子图显示一幅图像 sharex=True,sharey=True,
    ax=axes.flatten()  #降至1维，便于循环操作子图
    for i in range(len(imgs_fp_list)):
        img_path=imgs_fp_list[i] #获取图像的路径
        img_array=Image.open(img_path) #读取图像为数组，值为RGB格式0-255        
        img_resize=img_array.resize([int(scale * s) for s in img_array.size] ) #传入图像的数组，调整图片大小
        ax[i].imshow(img_resize,)  #显示图像 aspect='auto'
        ax[i].set_title(i+1)
    invisible_num=rows*columns-len(imgs_fp_list)
    if invisible_num>0:
        for i in range(invisible_num):
            ax.flat[-(i+1)].set_visible(False)
    fig.tight_layout() #自动调整子图参数，使之填充整个图像区域  
    fig.suptitle("images show",fontsize=14,fontweight='bold',y=1.02)
    plt.show()    
    
class AttrDict(dict):
    """
    # Code adapted from:
    # https://github.com/facebookresearch/Detectron/blob/master/detectron/utils/collections.py

    Source License
    # Copyright (c) 2017-present, Facebook, Inc.
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.
    ##############################################################################
    #
    # Based on:
    # --------------------------------------------------------
    # Fast R-CNN
    # Copyright (c) 2015 Microsoft
    # Licensed under The MIT License [see LICENSE for details]
    # Written by Ross Girshick
    # --------------------------------------------------------
    """
    IMMUTABLE = '__immutable__'

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__[AttrDict.IMMUTABLE] = False

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self:
            return self[name]
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if not self.__dict__[AttrDict.IMMUTABLE]:
            if name in self.__dict__:
                self.__dict__[name] = value
            else:
                self[name] = value
        else:
            raise AttributeError(
                'Attempted to set "{}" to "{}", but AttrDict is immutable'.
                format(name, value)
            )

    def immutable(self, is_immutable):
        """Set immutability to is_immutable and recursively apply the setting
        to all nested AttrDicts.
        """
        self.__dict__[AttrDict.IMMUTABLE] = is_immutable
        # Recursively set immutable state
        for v in self.__dict__.values():
            if isinstance(v, AttrDict):
                v.immutable(is_immutable)
        for v in self.values():
            if isinstance(v, AttrDict):
                v.immutable(is_immutable)

    def is_immutable(self):
        return self.__dict__[AttrDict.IMMUTABLE]
    
def gantt_chart_H(df_,category_field,datatime_filed,interval='3h'):
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
    print(f"category_field number:{len(category_name)}\ncategory_field:\n{category_name}")
    Start_Finish_Task=[]
    for c_n in tqdm(category_name):        
        category_df=df[df[category_field]==c_n]      
        t_interval=category_df.groupby(pd.Grouper(key='ts',axis=0,freq=interval))['ts'].agg(['first','last','count'])
        t_interval['count']=t_interval['count']*int(interval[:-1])
        t_interval.columns=['Start', 'Finish', 'Duration_Hours']
        t_interval['Task']=c_n
        Start_Finish_Task.append(t_interval)   
        
    SFT=pd.concat(Start_Finish_Task,ignore_index=True,axis=0)#[:1000] 
    colors=["rgb({},{},{})".format(randint(0,255),randint(0,255),randint(0,255) ) for i in range(len(np.unique(SFT.Task)))]
    fig=ff.create_gantt(SFT,group_tasks=True,index_col='Task',colors=colors)
    fig.update_layout(autosize=False,width=2100,height=1200,)
    fig.show()        
    
    return SFT    

def df_linking_geometry(df,gdf,key_df,key_gdf,how="inner"):
    '''
    包含有属性的DataFrame格式数据合并包含有地理空间信息的GeoDataFrame格式数据，仅合并“geometry”字段和用于链接的关键字段列

    Parameters
    ----------
    df : DataFrame
        属性数据，含有用于链接的关键字段.
    gdf : GeoDataFrame
        还有地理空间信息geometry字段和用于链接的关键字段.
    key_df : string
        属性数据用于链接的关键字段名.
    key_gdf : string
        含有地理空间信息数据用于链接的关键字段名.
    how : string, optional
        {‘left’, ‘right’, ‘outer’, ‘inner’, ‘cross’}，具体解释参考pandas.DataFrame.merg. The default is "inner".

    Returns
    -------
    gdf_linked : GeoDataFrame
        属性数据合并地理空间信息后的数据.

    '''    
    gdf_linked=gdf[[key_gdf,"geometry"]].merge(df,left_on=key_gdf,right_on=key_df,how=how,)
    
    return gdf_linked

def gdf_plot_annotate(gdf_,value_column,annotate_column,**setting):
    '''
    打印GeoDataFrame格式地理空间信息数据

    Parameters
    ----------
    gdf_ : GeoDataFrame
        待打印的数据.
    value_column : string
        数值显示字段名.
    annotate_column : string
        标注显示字段名.
    **setting : key args
        用于配置图表的参数，键和默认值如下
        setting_dict=dict(annotate_fontsize=8,
                          figsize=(10,10),    
                          legend_position="right",
                          legend_size="5%",
                          legend_pad=0.1,
                          legend_bbox_to_anchor=(1, 1),
                          cmap='OrRd',
                          labelsize=8,
                          scheme=None, # 等值分类图，例如 ‘BoxPlot’, ‘EqualInterval’, ‘FisherJenks’,‘FisherJenksSampled’, ‘HeadTailBreaks’, ‘JenksCaspall’, 
                                                         ‘JenksCaspallForced’, ‘JenksCaspallSampled’, ‘MaxP’, ‘MaximumBreaks’, ‘NaturalBreaks’, ‘Quantiles’, 
                                                         ‘Percentiles’, ‘StdMean’, ‘UserDefined’等
                          k=5, # 分类数量， 对应scheme参数，如果scheme参数为None，则k参数忽略
                          categorical=False # 为True时为分类数据，为False时为数值数据
                         ).

    Returns
    -------
    ax : TYPE
        DESCRIPTION.

    '''     
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    
    gdf=gdf_.copy(deep=True)
    setting_dict=dict(annotate_fontsize=8,
                      figsize=(10,10),    
                      legend_position="right",
                      legend_size="5%",
                      legend_pad=0.1,
                      legend_bbox_to_anchor=(1, 1),
                      cmap='OrRd',
                      labelsize=8,
                      scheme=None,
                      k=5,
                      categorical=False
                     )
    setting_dict.update(setting)
    gdf["index"]=gdf.index
    
    fig, ax=plt.subplots(figsize=setting_dict["figsize"])
    divider=make_axes_locatable(ax) 
    if setting_dict["scheme"]:
        gdf.plot(column=value_column,scheme=setting_dict["scheme"], k= setting_dict["k"],ax=ax,legend=True,cmap=setting_dict["cmap"],legend_kwds={'bbox_to_anchor':setting_dict["legend_bbox_to_anchor"]}) 
    elif setting_dict["categorical"]:
        gdf.plot(column=value_column,categorical=True,ax=ax,legend=True,cmap=setting_dict["cmap"],edgecolor='white',legend_kwds={'bbox_to_anchor':setting_dict["legend_bbox_to_anchor"]}) 
    else:   
        cax=divider.append_axes(setting_dict["legend_position"], size=setting_dict["legend_size"], pad=setting_dict["legend_pad"]) # 配置图例参数
        gdf.plot(column=value_column,scheme=setting_dict["scheme"], k= setting_dict["k"],ax=ax,cax=cax,legend=True,cmap=setting_dict["cmap"]) 
    gdf.apply(lambda x: ax.annotate(text=x[annotate_column], xy=x.geometry.centroid.coords[0], ha='center',fontsize=setting_dict["annotate_fontsize"]),axis=1) # 增加标注
    ax.tick_params(axis='both', labelsize=setting_dict["labelsize"])

    plt.show()