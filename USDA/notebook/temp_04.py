from database import postSQL2gpd,gpd2postSQL
from util_misc import AttrDict
__C=AttrDict() 
args=__C

__C.db=AttrDict() 
__C.db.UN='postgres'
__C.db.PW='123456'
__C.db.DB='inequalityNsegregation'
__C.db.GC='geometry' 
__C.db.db_info=dict(geom_col=args.db.GC,myusername=args.db.UN,mypassword=args.db.PW,mydatabase=args.db.DB)

__C.gi=AttrDict()
__C.gi.Chicago_epsg=32616
__C.gi.epsg_wgs84=4326

__C.data=AttrDict()
__C.data.landuse='G:\data\landuse_Chicago\LUI15_shapefile_v1' # 芝加哥2015年土地利用SHP格式文件
__C.data.landuse_LB='E:\data\Chicago_landuse\Chicago_landuse_LB\landuse_LB_uncropped.shp'
__C.data.landuse_tif='E:\data\Chicago_landuse\landuse.tif'

def raster2postSQL(raster_fn,TN,para='',**kwargs): # (c|a|d|p) 
    # create extension postgis_raster;
    from osgeo import gdal, osr
    import psycopg2
    import subprocess   
    import sys,os
    
    DB=kwargs['mydatabase']
    UN=kwargs['myusername']
    PW=kwargs['mypassword']    
    try:
        conn=psycopg2.connect("dbname={DB} user={UN} host='localhost' password={PW}".format(DB=DB,UN=UN,PW=PW))
        conn.set_session(autocommit=True) # if you want your updates to take effect without being in a transaction and requiring a commit, for a beginner, I would set this to True
    except:
        print("I am unable to connect to the database...")       

    raster=gdal.Open(raster_fn)
    proj=osr.SpatialReference(wkt=raster.GetProjection())
    # print(proj)
    SRID=str(proj.GetAttrValue('AUTHORITY',1))
    # print(SRID)
    query_srs_srid="""SELECT * FROM spatial_ref_sys WHERE srid = {}""".format(SRID)    
    # print(query)
    curs=conn.cursor()
    curs.execute(query_srs_srid)
    srs_srid=curs.fetchall()
    proj_str=str(proj).replace("\n","\t").replace(" ", "")
    # proj_str=proj_str.replace(" ", "")
    if srs_srid:
        print("srs_SRID={}".format(srs_srid[0][0]))
    else:
        query_insert_srid="""INSERT into spatial_ref_sys (srid, auth_name,auth_srid, proj4text, srtext) values ({srid}, '{auth_name}', {auth_srid}, {proj4text}, '{srtext}') ;""".format(srid=SRID,auth_name='custom',auth_srid=SRID,proj4text="''",srtext=proj_str)
        # print(query_insert_srid)
        curs.execute(query_insert_srid)
    
    gt=raster.GetGeoTransform()
    pixelSizeX=str(round(gt[1]))
    pixelSizeY=str(round(-gt[5]))
    # print(pixelSizeX,pixelSizeY)
    '''
    Raster Data Management, Queries, and Applications
    https://postgis.net/docs/using_raster_dataman.html 
    https://spatial-dev.guru/2022/01/28/import-rasters-file-to-postgis-database-using-raster2pgsql/
    '''
    # cmds='raster2pgsql -s '+projection+' -I -C -M "'+raster_fn+'" -F -t '+pixelSizeX+'x'+pixelSizeY+' public.'+TN+' | psql -d {} -U {} -h localhost -p {}'.format(DB,UN,5432)
    cmds='raster2pgsql -s '+SRID+' -I -C -M {} '.format(para)+raster_fn+' -F -t '+pixelSizeX+'x'+pixelSizeY+' public.'+TN+' | psql postgresql://{}:{}@localhost:5432/{}'.format(UN,PW,DB)
    
    print(cmds)
    print("_"*50)
    subprocess.call(cmds, shell=True,cwd='./psql')
    print("Loaded {} to PostgreSQL...".format(os.path.basename(raster_fn)))   
    
fn=r'E:\data\Chicago_landuse\landuse.tif'
raster2postSQL(fn,'landuse_tif','-d',**args.db.db_info)    