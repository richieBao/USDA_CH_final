def MCD12Q1v006_group_vs_ts(g_names_dt,nc_fn,n=0,save_fn=None):
    import rioxarray as rxr
    import xarray as xr
    import numpy as np
    import pandas as pd
    from tqdm import tqdm

    g_lst=[]
    dt_lst=[]
    for g_n,dt in g_names_dt:
        g=rxr.open_rasterio(nc_fn, group=g_n)      
        g_lst.append(g['LC_Prop1'])        
        dt_lst.append(dt)
        
        
    g_n=g_lst[n]
    x,y=np.meshgrid(g_n.x.values,g_n.y.values)
    xy=np.stack((x,y),axis=-1).reshape(-1,2)
    sel_lst=[]
    #i=0
    for coordi in tqdm(xy):
        row=[coordi[0],coordi[1]]        
        for g in g_lst:
            val=g.sel(x=coordi[0],y=coordi[1],method='nearest').data.item()
            row.append(val)            
        sel_lst.append(row)                  
        #if i==10:break
        #i+=1
    sel_df=pd.DataFrame(sel_lst,columns=["x","y"]+dt_lst)
    if save_fn:
        sel_df.to_pickle(save_fn)        
        
    return g_lst
    #stack=xr.combine_by_coords(g_lst[:3])
    #return stack
    
a=MCD12Q1v006_group_vs_ts(g_names_dt,args.data.MCD12Q1v006_preprocessed,n=0,save_fn=args.data.MCD12Q1v006_dt_vals)