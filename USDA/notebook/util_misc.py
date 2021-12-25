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
    is_outlier_bool=modified_ZScore>threshold    
    return is_outlier_bool,data[~is_outlier_bool]
