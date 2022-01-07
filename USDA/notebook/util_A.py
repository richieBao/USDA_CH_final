# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 21:21:38 2021

@author: Richie Bao-caDesign设计(cadesign.cn)
"""

def baiduPOI_dataCrawler(query_dic,bound_coordinate,partition,page_num_range,poi_fn_list=False):
    import coordinate_transformation as cc
    import urllib,json,csv,os,pathlib
    '''
    function - 百度地图开放平台POI数据爬取
    
    Paras:
        query_dic - 请求参数配置字典，详细参考上文或者百度服务文档
        bound_coordinate - 以字典形式配置下载区域
        partition - 检索区域切分次数
        page_num_range - 配置页数范围
        poi_fn_list=False - 定义的存储文件名列表
    '''
    urlRoot='http://api.map.baidu.com/place/v2/search?' #数据下载网址，查询百度地图服务文档
    #切分检索区域
    if bound_coordinate:
        xDis=(bound_coordinate['rightTop'][0]-bound_coordinate['leftBottom'][0])/partition
        yDis=(bound_coordinate['rightTop'][1]-bound_coordinate['leftBottom'][1])/partition    
    #判断是否要写入文件
    if poi_fn_list:
        for file_path in poi_fn_list:
            fP=pathlib.Path(file_path)
            if fP.suffix=='.csv':
                poi_csv=open(fP,'w',encoding='utf-8')
                csv_writer=csv.writer(poi_csv)    
            elif fP.suffix=='.json':
                poi_json=open(fP,'w',encoding='utf-8')
    num=0
    jsonDS=[] #存储读取的数据，用于.json格式数据的保存
    #循环切分的检索区域，逐区下载数据
    print("Start downloading data...")
    for i in range(partition):
        for j in range(partition):
            leftBottomCoordi=[bound_coordinate['leftBottom'][0]+i*xDis,bound_coordinate['leftBottom'][1]+j*yDis]
            rightTopCoordi=[bound_coordinate['leftBottom'][0]+(i+1)*xDis,bound_coordinate['leftBottom'][1]+(j+1)*yDis]
            for p in page_num_range:  
                #更新请求参数
                query_dic.update({'page_num':str(p),
                                  'bounds':str(leftBottomCoordi[1]) + ',' + str(leftBottomCoordi[0]) + ','+str(rightTopCoordi[1]) + ',' + str(rightTopCoordi[0]),
                                  'output':'json',
                                 })
                
                url=urlRoot+urllib.parse.urlencode(query_dic)
                data=urllib.request.urlopen(url)
                responseOfLoad=json.loads(data.read())     
                #print(url,responseOfLoad.get("message"))
                if responseOfLoad.get("message")=='ok':
                    results=responseOfLoad.get("results") 
                    for row in range(len(results)):
                        subData=results[row]
                        baidu_coordinateSystem=[subData.get('location').get('lng'),subData.get('location').get('lat')] #获取百度坐标系
                        Mars_coordinateSystem=cc.bd09togcj02(baidu_coordinateSystem[0], baidu_coordinateSystem[1]) #百度坐标系-->火星坐标系
                        WGS84_coordinateSystem=cc.gcj02towgs84(Mars_coordinateSystem[0],Mars_coordinateSystem[1]) #火星坐标系-->WGS84
                        
                        #更新坐标
                        subData['location']['lat']=WGS84_coordinateSystem[1]
                        subData['detail_info']['lat']=WGS84_coordinateSystem[1]
                        subData['location']['lng']=WGS84_coordinateSystem[0]
                        subData['detail_info']['lng']=WGS84_coordinateSystem[0]   
                        print(subData)
                        if csv_writer:
                            csv_writer.writerow([subData]) #逐行写入.csv文件
                        jsonDS.append(subData)
            num+=1       
            print("No."+str(num)+" was written to the .csv file.")
    if poi_json:       
        json.dump(jsonDS,poi_json)
        poi_json.write('\n')
        poi_json.close()
    if poi_csv:
        poi_csv.close()
    print("The download is complete.")

def csv2df(poi_fn_csv):
    import pandas as pd
    from benedict import benedict #benedict库是dict的子类，支持键列表（keylist）/键路径（keypath），应用该库的flatten方法展平嵌套的字典，准备用于DataFrame数据结构
    import csv
    
    '''
    function-转换.csv格式的POI数据为pandas的DataFrame
    
    Paras:
        poi_fn_csv - 存储有POI数据的.csv格式文件路径                
    '''
    n=0
    with open(poi_fn_csv, newline='',encoding='utf-8') as csvfile:
        poi_reader=csv.reader(csvfile)
        poi_dict={}    
        poiExceptions_dict={}
        for row in poi_reader:    
            if row:
                try:
                    row_benedict=benedict(eval(row[0])) #用eval方法，将字符串字典"{}"转换为字典{}
                    flatten_dict=row_benedict.flatten(separator='_') #展平嵌套字典
                    poi_dict[n]=flatten_dict
                except:                    
                    print("incorrect format of data_row number:%s"%n)                    
                    poiExceptions_dict[n]=row
            n+=1
            #if n==5:break #因为循环次数比较多，在调试代码时，可以设置停止的条件，节省时间与方便数据查看
    poi_df=pd.concat([pd.DataFrame(poi_dict[d_k].values(),index=poi_dict[d_k].keys(),columns=[d_k]).T for d_k in poi_dict.keys()], sort=True,axis=0)
    #print("_"*50)
    for col in poi_df.columns:
        try:
            poi_df[col]=pd.to_numeric(poi_df[col])
        except:
            #print("%s data type is not converted..."%(col))
            pass
    print("_"*50)
    print(".csv to DataFrame completed!")
    #print(poi_df.head()) #查看最终DataFrame格式下POI数据
    #print(poi_df.dtypes) #查看数据类型
    return poi_df

def coefficient_of_determination(observed_vals,predicted_vals):
    import pandas as pd
    import numpy as np
    import math
    '''
    function - 回归方程的判定系数
    
    Paras:
        observed_vals - 观测值（实测值）
        predicted_vals - 预测值
    '''
    vals_df=pd.DataFrame({'obs':observed_vals,'pre':predicted_vals})
    #观测值的离差平方和(总平方和，或总的离差平方和)
    obs_mean=vals_df.obs.mean()
    SS_tot=vals_df.obs.apply(lambda row:(row-obs_mean)**2).sum()
    #预测值的离差平方和
    pre_mean=vals_df.pre.mean()
    SS_reg=vals_df.pre.apply(lambda row:(row-pre_mean)**2).sum()
    #观测值和预测值的离差积和
    SS_obs_pre=vals_df.apply(lambda row:(row.obs-obs_mean)*(row.pre-pre_mean), axis=1).sum()
    
    #残差平方和
    SS_res=vals_df.apply(lambda row:(row.obs-row.pre)**2,axis=1).sum()
    
    #判断系数
    R_square_a=(SS_obs_pre/math.sqrt(SS_tot*SS_reg))**2
    R_square_b=1-SS_res/SS_tot
            
    return R_square_a,R_square_b

def vector_plot_3d(ax_3d,C,origin_vector,vector,color='r',label='vector',arrow_length_ratio=0.1):
    '''
    funciton - 转换SymPy的vector及Matrix数据格式为matplotlib可以打印的数据格式
    
    Paras:
        ax_3d - matplotlib的3d格式子图
        C - /coordinate_system - SymPy下定义的坐标系
        origin_vector - 如果是固定向量，给定向量的起点（使用向量，即表示从坐标原点所指向的位置），如果是自由向量，起点设置为坐标原点
        vector - 所要打印的向量
        color - 向量色彩
        label - 向量标签
        arrow_length_ratio - 向量箭头大小     
    '''
    origin_vector_matrix=origin_vector.to_matrix(C)
    x=origin_vector_matrix.row(0)[0]
    y=origin_vector_matrix.row(1)[0]
    z=origin_vector_matrix.row(2)[0]
    
    vector_matrix=vector.to_matrix(C)
    u=vector_matrix.row(0)[0]
    v=vector_matrix.row(1)[0]
    w=vector_matrix.row(2)[0]
    ax_3d.quiver(x,y,z,u,v,w,color=color,label=label,arrow_length_ratio=arrow_length_ratio)
    
def LandsatMTL_info(fp):
    import os,re
    '''
    function - 读取landsat *_MTL.txt文件，提取需要的信息
    
    Paras:
        fp - Landsat 文件根目录
    
    return:
        band_fp_dic - 返回各个波段的路径字典
        Landsat_para - 返回Landsat 参数 
    '''
    fps=[os.path.join(root,file) for root, dirs, files in os.walk(fp) for file in files] #提取文件夹下所有文件的路径
    MTLPattern=re.compile(r'_MTL.txt',re.S) #匹配对象模式，提取_MTL.txt遥感影像的元数据文件
    MTLFn=[fn for fn in fps if re.findall(MTLPattern,fn)][0]
    with open(MTLFn,'r') as f: #读取所有元数据文件信息
        MTLText=f.read()
    bandFn_Pattern=re.compile(r'FILE_NAME_BAND_[0-9]\d* = "(.*?)"\n',re.S)  #Landsat 波段文件
    band_fn=re.findall(bandFn_Pattern,MTLText)
    band_fp=[[(re.findall(r'B[0-9]\d*',fn)[0], re.findall(r'.*?%s$'%fn,f)[0]) for f in fps if re.findall(r'.*?%s$'%fn,f)] for fn in band_fn] #(文件名，文件路径)
    band_fp_dic={i[0][0]:i[0][1] for i in band_fp}
    #需要数据的提取标签/根据需要读取元数据信息
    values_fields=["RADIANCE_ADD_BAND_10",
                   "RADIANCE_ADD_BAND_11",
                   "RADIANCE_MULT_BAND_10",
                   "RADIANCE_MULT_BAND_11",
                   "K1_CONSTANT_BAND_10",
                   "K2_CONSTANT_BAND_10",
                   "K1_CONSTANT_BAND_11",
                   "K2_CONSTANT_BAND_11",
                   "DATE_ACQUIRED",
                   "SCENE_CENTER_TIME",
                   "MAP_PROJECTION",
                   "DATUM",
                   "UTM_ZONE"]

    Landsat_para={field:re.findall(re.compile(r'%s = "*(.*?)"*\n'%field),MTLText)[0] for field in values_fields} #（参数名，参数值）
    return  band_fp_dic,Landsat_para #返回所有波段路径和需要的参数值    

def NDVI(RED_band,NIR_band):
    import numpy as np
    '''
    function - 计算NDVI指数
    
    Paras:
        RED_band - 红色波段
        NIR_band - 近红外波段
    '''
    RED_band=np.ma.masked_where(NIR_band+RED_band==0,RED_band)
    NDVI=(NIR_band-RED_band)/(NIR_band+RED_band)
    NDVI=NDVI.filled(-9999)
    print("NDVI"+"_min:%f,max:%f"%(NDVI.min(),NDVI.max()))
    return NDVI

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

def demo_con_style(a_coordi,b_coordi,ax,connectionstyle):
    '''
    function - 在matplotlib的子图中绘制连接线
    reference - matplotlib官网Connectionstyle Demo
    
    Paras:
    a_coordi - a点的x，y坐标
    b_coordi - b点的x，y坐标
    ax - 子图
    connectionstyle - 连接线的形式
    '''
    x1, y1=a_coordi[0],a_coordi[1]
    x2, y2=b_coordi[0],b_coordi[1]

    ax.plot([x1, x2], [y1, y2], ".")
    ax.annotate("",
                xy=(x1, y1), xycoords='data',
                xytext=(x2, y2), textcoords='data',
                arrowprops=dict(arrowstyle="->", color="0.5",
                                shrinkA=5, shrinkB=5,
                                patchA=None, patchB=None,
                                connectionstyle=connectionstyle,
                                ),
                )

    ax.text(.05, .95, connectionstyle.replace(",", ",\n"),
            transform=ax.transAxes, ha="left", va="top")
    
def raster_clip(raster_fp,clip_boundary_fp,save_path):
    import earthpy.spatial as es
    import geopandas as gpd
    from pyproj import CRS
    import rasterio as rio
    '''
    function - 给定裁切边界，批量裁切栅格数据
    
    Paras:
    raster_fp - 待裁切的栅格数据文件路径（.tif）,具有相同的坐标投影系统
    clip_boundary - 用于裁切的边界（.shp，WGS84，无投影）
    
    return:
    rasterClipped_pathList - 裁切后的文件路径列表
    '''
    clip_bound=gpd.read_file(clip_boundary_fp)
    with rio.open(raster_fp[0]) as raster_crs:
        raster_profile=raster_crs.profile
        clip_bound_proj=clip_bound.to_crs(raster_profile["crs"])
    
    rasterClipped_pathList=es.crop_all(raster_fp, save_path, clip_bound_proj, overwrite=True) #对所有波段band执行裁切
    print("finished clipping.")
    return rasterClipped_pathList    