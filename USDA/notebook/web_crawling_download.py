# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 01:29:47 2022

@author: richie bao
"""

from database import postSQL2gpd,gpd2postSQL
from util_misc import AttrDict
__C=AttrDict() 
args=__C

__C.db=AttrDict() 
__C.db.UN='postgres'
__C.db.PW='123456'
__C.db.DB='AoT_20220831'
__C.db.GC='geometry' 
__C.db.db_info=dict(geom_col=args.db.GC,myusername=args.db.UN,mypassword=args.db.PW,mydatabase=args.db.DB)

__C.data=AttrDict()
__C.data.sn_bound_10deg='./data/MCD12Q1v006/sn_bound_10deg.txt'
__C.data.MCD12Q1v006='G:\data\MCD12Q1v006\data'


import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'


def modland_grids(fp,start_idx=0,boundary_coordi=None): #[lon_min,lon_max,lat_min,lat_max]
    import pandas as pd
    
    with open (fp,'r') as f:
        lines=f.readlines()[start_idx:-2]
    lines_df=pd.DataFrame(columns=lines[0].split(),data=[row.split() for row in lines[1:]])
    lines_df=lines_df.apply(pd.to_numeric,errors='ignore')
    
    def within_func(row):
        lon_sum=(row.lon_min>=lon_min and row.lon_min<=lon_max)+(row.lon_max>=lon_min and row.lon_max<=lon_max)    
        lat_sum=(row.lat_min>=lat_min and row.lat_min<=lat_max)+(row.lat_max>=lat_min and row.lat_max<=lat_max)
        if lon_sum>0 and lat_sum>0:
            return 1
        else: 
            return 0        
        
    if boundary_coordi:
        lon_min,lon_max,lat_min,lat_max=boundary_coordi
        lines_df['mask']=lines_df.apply(within_func,axis=1) 
        extracted_rows=lines_df[lines_df['mask']==1]
        extracted_rows['identifier']=extracted_rows.apply(lambda row:f"h{int(row.ih)}v{int(row.iv):02}",axis=1)
        return extracted_rows
    else:
        return lines_df    
    
def urls_extraction(urls_dict,conditional_chars):
    from urllib.parse import urljoin
    
    urls_extraction_dict={}
    for k,v in urls_dict.items():
        urls_extraction_dict[k]=[]
        for url in v:
            for i in identifier:
                if i in url:
                    urls_extraction_dict[k].append(urljoin(k,url))
    return urls_extraction_dict 

def urls_download(urls_dict,pattern,save_root):
    import re
    import os
    import urllib
    import shutil
    import wget    
    import requests
    
    from requests.auth import HTTPBasicAuth
    from requests.auth import HTTPDigestAuth
    from requests_ntlm import HttpNtlmAuth
    
    import urllib3   
    import bs4
    #from urllib import request, parse
    
 
    for k,v in urls_dict.items():
        #print(k)
        directory_name=re.findall(pattern,k)
        #print(directory_name[0])
        save_dir=os.path.join(save_root,directory_name[0])
        isExist=os.path.exists(save_dir)
        if not isExist:
            os.makedirs(save_dir)                
        else:
            print(f"The directory {save_dir} already exists.") #  No files will be downloaded.
            
        for url in v[1:]:
            fn=os.path.basename(url)
            save_fn=os.path.join(save_dir,fn)
            print(save_fn)
            url=fr"https://e4ftl01.cr.usgs.gov/MOTA/MCD12Q1.006/2020.01.01/MCD12Q1.A2020001.h00v10.006.2021361185556.hdf"
            print(url)
            
            username = 'richiebao_siniticink'
            password = 'Lfyh0322' 
            
            
            
            login = os.getenv('user')
            password = os.getenv('pwd')
            r = requests.get(url, verify=True, stream=True,auth=(login,password))
            print(r.status_code)
                        
            open(f'G:/temp/0000.hdf',"wb").write(r.content)
                        
            
            
            
            
            
            
            
            
            # headers = {
            #  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
            #  "Connection": "keep-alive",
            # }            
            
            # s = requests.Session()
            # cookie = requests.cookies.create_cookie('COOKIE_NAME','COOKIE_VALUE')
            # s.cookies.set_cookie(cookie)
            # with s.get(url, stream=True, headers=headers) as r:      
            #     print(r.status_code)                    
                                    
            
            
            # r = requests.get(url, auth=(username,password))
            # print(r.status_code)
            # if r.status_code == 200:
                
            
            
            # import urllib.request
            # httphandler = urllib.request.HTTPHandler()
            # opener = urllib.request.build_opener(httphandler)
            # request = urllib.request.Request(url)
            # response = opener.open(request)
            
            # print(response.read().decode('utf-8'))

                   
                    
                    
                    
            '''
            request_pwd = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            request_pwd.add_password(None, url, 'richiebao_siniticink', 'Lfyh0322')
            handler = urllib.request.HTTPBasicAuthHandler(request_pwd)    
            
            
            handler_open = urllib.request.build_opener(handler)
            urllib.request.install_opener(handler_open)
            
            req_obj = urllib.request.Request(url)
            with urllib.request.urlopen(req_obj) as res_obj:
                print(res_obj.read())
            '''
            # username = 'richiebao_siniticink'
            # password = 'Lfyh0322'            
            # p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            # p.add_password(None, url, username, password)
            # handler = urllib.request.HTTPBasicAuthHandler(p)
            # opener = urllib.request.build_opener(handler)
            # urllib.request.install_opener(opener)
            # zip_file = urllib.request.urlopen(url).read()
            

            #print(type(handler_open))
           # res_obj = handler_open.open(url)
            #auth=HTTPBasicAuth('richiebao_siniticink', 'Lfyh0322')            
            #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
            #request=requests.get(url,verify=False) # auth=auth,verify=True, headers=headers
            
            #a=urllib.request.urlopen(url)
            
            #print(request.text)
            #response=wget.download(url,save_fn,)
            
            
            
            #print(request.content)
            #with open(save_fn, 'wb') as f:
                #f.write(request.content)
            #open(save_fn,'wb').write(request.content)
            
            #with urllib.request.urlopen(url) as response,open(save_fn,'wb') as out_file: # auth=("richiebao_siniticink","Lfyh0322")
                #shutil.copyfileobj(response,out_file)
                
            # r = requests.get(url, auth=HttpNtlmAuth(username, password))  
            # print(r.status_code)     
            # print(r.headers)            
            # page = r.content
            # print (page)     

            break
        
        break    
    
    


if __name__=="__main__":
    modland_ivih_masked=modland_grids(args.data.sn_bound_10deg,start_idx=6,boundary_coordi=[68,139,15,57])    
    print(modland_ivih_masked.shape)
    modland_ivih_masked.sort_values(by=['ih','iv'])   
    
    identifier=modland_ivih_masked.identifier.to_list()
    print(identifier)   
    
    import pickle
    
    MCD12Q1_crawl_url_fp="./data/MCD12Q1_crawl_urls.pickle"
    with open(MCD12Q1_crawl_url_fp,'rb') as f:
        MCD12Q1_crawl_urls=pickle.load(f)    
        
    urls_extraction_dict=urls_extraction(MCD12Q1_crawl_urls,identifier) 

    pattern=r'006.(\d+)\.'
    save_root='G:\data\MCD12Q1v006\data' 
    urls_download(urls_extraction_dict,pattern,save_root)     
            
            
            
            