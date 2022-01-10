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

class feature_builder_BOW:
    '''
    class - 根据所有图像关键点描述子聚类建立图像视觉词袋，获取每一图像的特征（码本）映射的频数统计
    '''   
    def __init__(self,num_cluster=32):
        self.num_clusters=num_cluster

    def extract_features(self,img):
        import cv2 as cv
        '''
        function - 提取图像特征
        
        Paras:
            img - 读取的图像
        '''
        star_detector=cv.xfeatures2d.StarDetector_create()
        key_points=star_detector.detect(img)
        img_gray=cv.cvtColor(img,cv.COLOR_BGR2GRAY)
        kp,des=cv.xfeatures2d.SIFT_create().compute(img_gray, key_points) #SIFT特征提取器提取特征
        return des
    
    def visual_BOW(self,des_all):
        from sklearn.cluster import KMeans
        '''
        function - 聚类所有图像的特征（描述子/SIFT），建立视觉词袋
        
        Paras:
            des_all - 所有图像的关键点描述子
        '''
        print("start KMean...")
        kmeans=KMeans(self.num_clusters)
        kmeans=kmeans.fit(des_all)
        #centroids=kmeans.cluster_centers_
        print("end KMean...")
        return kmeans         
    
    def get_visual_BOW(self,training_data):
        import cv2 as cv
        from tqdm import tqdm
        '''
        function - 提取图像特征，返回所有图像关键点聚类视觉词袋
        
        Paras:
            training_data - 训练数据集
        '''
        des_all=[]
        #i=0        
        for item in tqdm(training_data):            
            classi_judge=item['object_class']
            img=cv.imread(item['image_path'])
            #print(item['image_path'])
            #print(img)
            des=self.extract_features(img)
            des_all.extend(des)           
            #print(des.shape)
            #if i==10:break
            #i+=1        
        kmeans=self.visual_BOW(des_all)      
        return kmeans
    
    def normalize(self,input_data):
        import numpy as np
        '''
        fuction - 归一化数据
        
        Paras:
            input_data - 待归一化的数组
        '''
        sum_input=np.sum(input_data)
        if sum_input>0:
            return input_data/sum_input #单一数值/总体数值之和，最终数值范围[0,1]
        else:
            return input_data               
    
    def construct_feature(self,img,kmeans):
        import numpy as np
        '''
        function - 使用聚类的视觉词袋构建图像特征（构造码本）
        
        Paras:
            img - 读取的单张图像
            kmeans - 已训练的聚类模型
        '''
        des=self.extract_features(img)
        labels=kmeans.predict(des.astype(float)) #对特征执行聚类预测类标
        feature_vector=np.zeros(self.num_clusters)
        for i,item in enumerate(feature_vector): #计算特征聚类出现的频数/直方图
            feature_vector[labels[i]]+=1
        feature_vector_=np.reshape(feature_vector,((1,feature_vector.shape[0])))
        return self.normalize(feature_vector_)
    
    def get_feature_map(self,training_data,kmeans):
        import cv2 as cv
        '''
        function - 返回每个图像的特征映射（码本映射）
        
        Paras:
            training_data - 训练数据集
            kmeans - 已训练的聚类模型
        '''
        feature_map=[]
        for item in training_data:
            temp_dict={}
            temp_dict['object_class']=item['object_class']
            #print("Extracting feature for",item['image_path'])
            img=cv.imread(item['image_path'])
            temp_dict['feature_vector']=self.construct_feature(img,kmeans)
            if temp_dict['feature_vector'] is not None:
                feature_map.append(temp_dict)
        #print(feature_map[0]['feature_vector'].shape,feature_map[0])
        return feature_map
    
def evaluate_accuracy(data_iter, net):
    '''
    funtion - 平均模型net在数据集data_iter上的准确率
    '''
    accu_sum,n=0.0,0
    for X,y in data_iter:
        accu_sum+=(net(X).argmax(dim=1)==y).float().sum().item()
        n+=y.shape[0]
    return accu_sum/n

def sgd_v1(params,lr):
    '''
    funtion - 梯度下降，v1版
    '''
    for param in params:
        param.data-=lr*param.grad    

def train_v1(net,train_iter, test_iter, loss, num_epochs,params=None, lr=None, optimizer=None,interval_print=100):
    from tqdm.auto import tqdm
    '''
    function - 训练模型，v1版
    
    Paras:
        net - 构建的模型结构
        train_iter - 可迭代训练数据集
        test_iter - 可迭代测试数据集
        loss - 损失函数
        num_epochs - 训练迭代次数
        params=None - 初始化模型参数，以列表形式表述，例如[W,b]
        lr=None, - 学习率
        optimizer=None - 优化函数
        intervation - 训练模型，v1版
    '''
    for epoch in tqdm(range(num_epochs)):
        train_l_sum, train_acc_sum, n=0.0, 0.0, 0
        for X, y in train_iter:
            y_pred=net(X)
            l=loss(y_pred,y).sum()
            
            #梯度清零
            if optimizer is not None:
                optimizer.zero_grad()
            elif params is not None and params[0].grad is not None:
                for param in params:
                    param.grad.data.zero_()
            
            l.backward()
            if optimizer is None:
                sgd_v1(params,lr) #应用自定义的梯度下降法
            else:
                optimizer.step() #应用torch.optim.SGD库的梯度下降法
                
            train_l_sum += l.item()
            train_acc_sum += (y_pred.argmax(dim=1) == y).sum().item()
            n += y.shape[0]
        if test_iter is not None:        
            test_acc = evaluate_accuracy(test_iter, net)
        if epoch%interval_print==0:
            print('epoch %d, loss %.4f, train acc %.3f, test acc %.3f'%(epoch + 1, train_l_sum / n, train_acc_sum / n, test_acc))
            
def KITTI_info(KITTI_info_fp,timestamps_fp):
    import util_misc
    import pandas as pd
    import os    
    '''
    function - 读取KITTI文件信息，1-包括经纬度，惯性导航系统信息等的.txt文件，2-包含时间戳的.txt文件
    '''
    drive_fp=util_misc.filePath_extraction(KITTI_info_fp,['txt'])
    '''展平列表函数'''
    flatten_lst=lambda lst: [m for n_lst in lst for m in flatten_lst(n_lst)] if type(lst) is list else [lst]
    drive_fp_list=flatten_lst([[os.path.join(k,f) for f in drive_fp[k]] for k,v in drive_fp.items()])

    columns=["lat","lon","alt","roll","pitch","yaw","vn","ve","vf","vl","vu","ax","ay","ay","af","al","au","wx","wy","wz","wf","wl","wu","pos_accuracy","vel_accuracy","navstat","numsats","posmode","velmode","orimode"]
    drive_info=pd.concat([pd.read_csv(item,delimiter=' ',header=None) for item in drive_fp_list],axis=0)
    drive_info.columns=columns
    drive_info=drive_info.reset_index()

    timestamps=pd.read_csv(timestamps_fp,header=None)
    timestamps.columns=['timestamps_']
    drive_info=pd.concat([drive_info,timestamps],axis=1,sort=False)
    #drive_29_0071_info.index=pd.to_datetime(drive_29_0071_info["timestamps_"]) #用时间戳作为行(row)索引
    return drive_info              

class dynamicStreetView_visualPerception:
    '''
    class - 应用Star提取图像关键点，结合SIFT获得描述子，根据特征匹配分析特征变化（视觉感知变化），即动态街景视觉感知
    
    Paras:
    imgs_fp - 图像路径列表
    knnMatch_ratio - 图像匹配比例，默认为0.75
    '''
    def __init__(self,imgs_fp,knnMatch_ratio=0.75):
        self.knnMatch_ratio=knnMatch_ratio
        self.imgs_fp=imgs_fp
    
    def kp_descriptor(self,img_fp):
        import cv2 as cv
        '''
        function - 提取关键点和获取描述子
        '''
        img=cv.imread(img_fp)
        star_detector=cv.xfeatures2d.StarDetector_create()        
        key_points=star_detector.detect(img) #应用处理Star特征检测相关函数，返回检测出的特征关键点
        img_gray=cv.cvtColor(img,cv.COLOR_BGR2GRAY) #将图像转为灰度
        kp,des=cv.xfeatures2d.SIFT_create().compute(img_gray, key_points) #SIFT特征提取器提取特征
        return kp,des
        
     
    def feature_matching(self,des_1,des_2,kp_1=None,kp_2=None):
        import cv2 as cv
        '''
        function - 图像匹配
        '''
        bf=cv.BFMatcher()
        matches=bf.knnMatch(des_1,des_2,k=2)
        
        '''
        可以由匹配matches返回关键点（train,query）的位置索引，train图像的索引，及描述子之间的距离
        DMatch.distance - Distance between descriptors. The lower, the better it is.
        DMatch.trainIdx - Index of the descriptor in train descriptors
        DMatch.queryIdx - Index of the descriptor in query descriptors
        DMatch.imgIdx - Index of the train image.
        '''
        '''
        if kp_1 !=None and kp_2 != None:
            kp1_list=[kp_1[mat[0].queryIdx].pt for mat in matches]
            kp2_list=[kp_2[mat[0].trainIdx].pt for mat in matches]
            des_distance=[(mat[0].distance,mat[1].distance) for mat in matches]
            print(des_distance[:5])
        '''
        
        good=[]
        for m,n in matches:
            if m.distance < self.knnMatch_ratio*n.distance:
                good.append(m) 
        #good_num=len(good)
        return good #,good_num
    
    
    def sequence_statistics(self):
        from tqdm import tqdm
        '''
        function - 序列图像匹配计算，每一位置图像与后续所有位置匹配分析
        '''        
        des_list=[]
        print("计算关键点和描述子...")
        for f in tqdm(self.imgs_fp):        
            _,des=self.kp_descriptor(f)
            des_list.append(des)
        matches_sequence={}
        print("计算序列图像匹配数...")
        for i in tqdm(range(len(des_list)-1)):
            matches_temp=[]
            for j_des in des_list[i:]:
                matches_temp.append(self.feature_matching(des_list[i],j_des))
            matches_sequence[i]=matches_temp
        matches_num={k:[len(v) for v in val] for k,val in matches_sequence.items()}
        return matches_num  

def vanishing_position_length(matches_num,coordi_df,epsg,**kwargs):
    from shapely.geometry import Point, LineString, shape
    import geopandas as gpd
    import pyproj
    import numpy as np
    import pandas as pd
    '''
    function - 计算图像匹配特征点几乎无关联的距离，即对特定位置视觉随距离远去而感知消失的距离

    Paras:
        matches_num - 由类dynamicStreetView_visualPerception计算的特征关键点匹配数量
        coordi_df - 包含经纬度的DataFrame，其列名为：lon,lat
        **kwargs - 同类movingAverage_inflection配置参数
    '''
    MAI_paras={'window':15,'plot_intervals':True,'scale':1.96, 'plot_anomalies':True,'figsize':(15*2,5*2),'threshold':0}
    MAI_paras.update(kwargs)   
    #print( MAI_paras)

    vanishing_position={}
    for idx in range(len(matches_num)): 
        x=np.array(range(idx,idx+len(matches_num[idx]))) 
        y=np.array(matches_num[idx])
        y_=pd.Series(y,index=x)   
        MAI=movingAverage_inflection(y_, window=MAI_paras['window'],plot_intervals=MAI_paras['plot_intervals'],scale=MAI_paras['scale'], plot_anomalies=MAI_paras['plot_anomalies'],figsize=MAI_paras['figsize'],threshold=MAI_paras['threshold'])   
        _,_,_,_,from_vert_t, _,_, _,from_horiz_t,_=MAI.knee_elbow()
        if np.any(from_horiz_t!= None) :
            vanishing_position[idx]=(idx,from_horiz_t[0])
        else:
            vanishing_position[idx]=(idx,idx)
    vanishing_position_df=pd.DataFrame.from_dict(vanishing_position,orient='index',columns=['start_idx','end_idx'])

    vanishing_position_df['geometry']=vanishing_position_df.apply(lambda idx:LineString(coordi_df[idx.start_idx:idx.end_idx][['lon','lat']].apply(lambda row:Point(row.lon,row.lat), axis=1).values.tolist()), axis=1)
    crs_4326=4326
    vanishing_position_gdf=gpd.GeoDataFrame(vanishing_position_df,geometry='geometry',crs=crs_4326)

    crs_=pyproj.CRS(epsg) 
    vanishing_position_gdf_reproj=vanishing_position_gdf.to_crs(crs_)
    vanishing_position_gdf_reproj['length']=vanishing_position_gdf_reproj.geometry.length
    return vanishing_position_gdf_reproj

class movingAverage_inflection:
    import pandas as pd
    
    '''
    class - 曲线（数据）平滑，与寻找曲线水平和纵向的斜率变化点
    
    Paras:
    series - pandas 的Series格式数据
    window - 滑动窗口大小，值越大，平滑程度越大
    plot_intervals - 是否打印置信区间，某人为False 
    scale - 偏差比例，默认为1.96, 
    plot_anomalies - 是否打印异常值，默认为False,
    figsize - 打印窗口大小，默认为(15,5),
    threshold - 拐点阈值，默认为0
    '''
    def __init__(self,series, window, plot_intervals=False, scale=1.96, plot_anomalies=False,figsize=(15,5),threshold=0):
        self.series=series
        self.window=window
        self.plot_intervals=plot_intervals
        self.scale=scale
        self.plot_anomalies=plot_anomalies
        self.figsize=figsize
        
        self.threshold=threshold
        self.rolling_mean=self.movingAverage()
    
    def masks(self,vec):
        '''
        function - 寻找曲线水平和纵向的斜率变化，参考 https://stackoverflow.com/questions/47342447/find-locations-on-a-curve-where-the-slope-changes
        '''
        d=np.diff(vec)
        dd=np.diff(d)

        # Mask of locations where graph goes to vertical or horizontal, depending on vec
        to_mask=((d[:-1] != self.threshold) & (d[:-1] == -dd-self.threshold))
        # Mask of locations where graph comes from vertical or horizontal, depending on vec
        from_mask=((d[1:] != self.threshold) & (d[1:] == dd-self.threshold))
        return to_mask, from_mask
        
    def apply_mask(self,mask, x, y):
        return x[1:-1][mask], y[1:-1][mask]   
    
    def knee_elbow(self):
        '''
        function - 返回拐点的起末位置
        '''        
        x_r=np.array(self.rolling_mean.index)
        y_r=np.array(self.rolling_mean)
        to_vert_mask, from_vert_mask=self.masks(x_r)
        to_horiz_mask, from_horiz_mask=self.masks(y_r)     

        to_vert_t, to_vert_v=self.apply_mask(to_vert_mask, x_r, y_r)
        from_vert_t, from_vert_v=self.apply_mask(from_vert_mask, x_r, y_r)
        to_horiz_t, to_horiz_v=self.apply_mask(to_horiz_mask, x_r, y_r)
        from_horiz_t, from_horiz_v=self.apply_mask(from_horiz_mask, x_r, y_r)    
        return x_r,y_r,to_vert_t, to_vert_v,from_vert_t, from_vert_v,to_horiz_t, to_horiz_v,from_horiz_t, from_horiz_v

    def movingAverage(self):
        rolling_mean=self.series.rolling(window=self.window).mean()        
        return rolling_mean        

    def plot_movingAverage(self,inflection=False):
        import numpy as np
        from sklearn.metrics import median_absolute_error, mean_absolute_error
        import matplotlib.pyplot as plt
        """
        function - 打印移动平衡/滑动窗口，及拐点
        """

        plt.figure(figsize=self.figsize)
        plt.title("Moving average\n window size = {}".format(self.window))
        plt.plot(self.rolling_mean, "g", label="Rolling mean trend")

        #打印置信区间，Plot confidence intervals for smoothed values
        if self.plot_intervals:
            mae=mean_absolute_error(self.series[self.window:], self.rolling_mean[self.window:])
            deviation=np.std(self.series[self.window:] - self.rolling_mean[self.window:])
            lower_bond=self.rolling_mean - (mae + self.scale * deviation)
            upper_bond=self.rolling_mean + (mae + self.scale * deviation)
            plt.plot(upper_bond, "r--", label="Upper Bond / Lower Bond")
            plt.plot(lower_bond, "r--")

            # 显示异常值，Having the intervals, find abnormal values
            if self.plot_anomalies:
                anomalies=pd.DataFrame(index=self.series.index, columns=self.series.to_frame().columns)
                anomalies[self.series<lower_bond]=self.series[self.series<lower_bond].to_frame()
                anomalies[self.series>upper_bond]=self.series[self.series>upper_bond].to_frame()
                plt.plot(anomalies, "ro", markersize=10)
                
        if inflection:
            x_r,y_r,to_vert_t, to_vert_v,from_vert_t, from_vert_v,to_horiz_t, to_horiz_v,from_horiz_t, from_horiz_v=self.knee_elbow()
            plt.plot(x_r, y_r, 'b-')
            plt.plot(to_vert_t, to_vert_v, 'r^', label='Plot goes vertical')
            plt.plot(from_vert_t, from_vert_v, 'kv', label='Plot stops being vertical')
            plt.plot(to_horiz_t, to_horiz_v, 'r>', label='Plot goes horizontal')
            plt.plot(from_horiz_t, from_horiz_v, 'k<', label='Plot stops being horizontal')     
            

        plt.plot(self.series[self.window:], label="Actual values")
        plt.legend(loc="upper right")
        plt.grid(True)
        plt.xticks(rotation='vertical')
        plt.show()



