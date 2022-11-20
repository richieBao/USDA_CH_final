# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 15:38:30 2022

@author: richie bao
"""
from collections import OrderedDict
from util_misc import AttrDict
import time
import os
import re
from pathlib import Path
import csv
import datetime  
import errno
from tqdm import tqdm

def AoT_reduction_setup(args): 
    '''    
    更新extraction下的属性参数

    Parameters
    ----------
    args : Class(dict)
        AttrDict方法的参数配置.

    Returns
    -------
    None.

    '''    
    
    #check that path exists and contains the necessary files
    if os.path.exists(args.path):
        args.extraction.dirPath=str(args.path)
        if not os.path.isfile(str(args.extraction.dirPath+"/data.csv")) or not os.path.isfile(str(args.extraction.dirPath+"/nodes.csv")) or not os.path.isfile(str(args.extraction.dirPath+"/sensors.csv")) or not os.path.isfile(str(args.extraction.dirPath+"/provenance.csv")) or not os.path.isfile(str(args.extraction.dirPath+"/README.md")):
            print("Error: Files missing from input directory path.")
            exit(1)
    else:
        print("Error: Path does not exist. Specify full path to unpackaged complete node data set")
        exit(1);
 
    # remove trailing slash if user includes it
    if (str(args.extraction.dirPath[-1:])=="/"):
        args.extraction.dirPath=args.extraction.dirPath[:-1]     
        
    # set the input file (full path to file) 
    args.extraction.inputFile=args.extraction.dirPath+"/data.csv"        
        
    # make sure user specifies a time period
    if args.period==None:
        print("Error: No time value given. Must be an int followed by 's','m','h',or 'd'.")
        exit(1)
        
    if not re.match(r"[0-9]+[s,m,h,d]{1}$| [0-9]+[s,m,h,d]{1}$|[0-9]+[s,m,h,d]{1} $| [0-9]+[s,m,h,d]{1} $",args.period):
        print("Error: Time value must be an int followed by 's','m','h',or 'd'.")
        exit(1)
        
    interval=args.period[-1:]
    numInterval=abs(int(args.period[0:-1]))        
    # print(interval,numInterval)
    
    if (numInterval < 1):
        print("Error: Time value must be a positive integer greater than 0.")
        exit(1)    
    
    # convert user input time period into seconds - must be at least 24 seconds
    if interval=='s':
        if(numInterval<24):
            print("Error: Time value cannot be less than 24 seconds.")
            exit(1)
        else:
            args.extraction.period=numInterval
    elif interval=='m':
        args.extraction.period=numInterval*60
    elif interval == 'h':
        args.extraction.period=numInterval*60*60
    elif interval=='d':
        args.extraction.period=numInterval*24*60*60
    else:
        args.extraction.period=numInterval        
        
    # create path names
    dp=Path(args.extraction.dirPath)
    parentDir=dp.parent.absolute()  
    args.extraction.subDir=str(parentDir.joinpath(dp.name+"_reduced_data_" + str(args.extraction.period)))
    fileName=parentDir.joinpath(dp.name+"_reduced_data_" + str(args.extraction.period) + "/data.csv")
    args.extraction.fileName=str(fileName)
    args.extraction.outputFile=args.extraction.fileName
    
def AoT_reduction_createData(args):
    '''
    数据精度处理计算

    Parameters
    ----------
    args : Class(dict)
        AttrDict方法的参数配置， AoT_reduction_setup()更新后参数.

    Returns
    -------
    None.

    '''      
    
    valStr=''
    count=0
    newVal=''
    currMax=0
    currMin=0
    
    timeRange={"beginTime":0,"endTime":0}
    
    with open(args.extraction.inputFile, "r") as file:
        # create a csv reader object (it is an Ordered Dictionary of all the rows from the .csv file)
        # populate the fieldNames variable to place at the top of the output .csv file
        # replace any null values so that no errors occur
        reader=csv.DictReader(x.replace('\0', 'NullVal') for x in file)
        args.extraction.fieldNames=reader.fieldnames        
        print(f"field names:{args.extraction.fieldNames}")
        # sensor values can come from the original data set or the moving average tool; otherwise, the tool cannot function
        for i in range(0,len(args.extraction.fieldNames)):
            if (args.extraction.fieldNames[i]=="value_hrf"):
                args.extraction.hrfTitle="value_hrf"
            elif (args.extraction.fieldNames[i]=="value_hrf_moving_average"):
                args.extraction.hrfTitle="value_hrf_moving_average"    
            
        if (args.extraction.hrfTitle!="value_hrf" and args.extraction.hrfTitle!="value_hrf_moving_average"):
            print("Error: Could not find appropriate value header. CSV file headers must include either 'value_hrf' or 'value_hrf_moving_average'.")
            exit(1)        
                
        # go through each line of the input .csv file
        for row in tqdm(reader):
            count=count + 1                
            # print number of lines parsed every *lines* amount of lines
            #if (args.printLines==True) and (count % args.lines==0):
                #print(count,end="\r")  
                
            #start the output evenly at the day, hour, or minute,
            if (count == 1):                
                hours = int(datetime.datetime.strptime(row['timestamp'], '%Y/%m/%d %H:%M:%S').hour)
                minutes = int(datetime.datetime.strptime(row['timestamp'], '%Y/%m/%d %H:%M:%S').minute)
                seconds = int(datetime.datetime.strptime(row['timestamp'], '%Y/%m/%d %H:%M:%S').second)
                difference = hours*60*60 + minutes*60 + seconds
                
                timeRange["beginTime"] =  (datetime.datetime.strptime(row['timestamp'],'%Y/%m/%d %H:%M:%S') - datetime.datetime(1970,1,1)).total_seconds()
                timeRange["beginTime"] = timeRange["beginTime"] - difference
                timeRange["endTime"] = timeRange["beginTime"] + args.extraction.period
                
            #set the new beginning and new end of the time range
            #if there is a gap in the data, this while loop runs until it hits the next timestamp
            while (timeRange["endTime"] < (datetime.datetime.strptime(row['timestamp'],'%Y/%m/%d %H:%M:%S') - datetime.datetime(1970,1,1)).total_seconds()):
                timeRange["beginTime"] = timeRange["endTime"]
                timeRange["endTime"] = timeRange["endTime"] + args.extraction.period
                
                
            # create the temporary dictionary (uses each sensor's value_hrf (or value_hrf_moving_average) as part of the value for each of the keys in outputDict) to hold
            # the sum, count, min, and max of the sensor hrf values over the specified time period
            if (',' in row[args.extraction.hrfTitle]):
                newVal='"'+ row[args.extraction.hrfTitle] +'"' # corrects error if commas are included in a sensor value
            else:
                newVal=row[args.extraction.hrfTitle]
            temp={'sum':newVal,'count':1, 'max':newVal, 'min':newVal}          
            
            # delete value columns so that when getting all columns, they can just be used as the dict key
            # (value_raw will most likely not be used by end user and does not make sense to keep track of)
            del row[args.extraction.hrfTitle]   
            
            # delete the value_raw, value_hrf_sum, and value_hrf_count columns if they exist
            try:
                del row['value_raw']
            except:
                pass
            try:
                del row['value_hrf_sum']
            except:
                pass
            try:
                del row['value_hrf_count']
            except:
                pass       
            
            # iterate through the dictionary to generate the outputDict for each time period
            for k,v in row.items():
                # concatenate fields to be used as dictionary keys except value_hrf (or value_hrf_moving_average) (to be used as part of dictionary values) and value_raw (deleted)
                # edit timestamp (to be used as part of dictionary keys - this is what determines how many rows from the input .csv file will be condensed into one row)
                # timestamp adjusted based on timeRange from code above generated by user input - timestamp is also halfway between the previous period and next period                    
                if k=='timestamp':
                    valStr=valStr + str(datetime.datetime.utcfromtimestamp(timeRange["endTime"] - args.extraction.period/2).strftime('%Y/%m/%d %H:%M:%S'))
                else:
                    valStr=valStr + ',' + str(v)    
                    
            # if the key already exists (meaning the row has already been made and now the current value_hrf (or value_hrf_moving_average) just needs to be added to the sum and the count value needs to be incremented)
            # then try to set the value of the dictionary key (key is in the format: timestamp,node_id,subsystem,sensor,parameter) - skips any values that are 'NA' or are a mix of letters and numbers
            # dictionary value is another dictionary in the format: {'sum':sum,'count':count,'min':min,'max':max}
            # else just update the outputDict with the temporary dictionary created above that contains the first value_hrf(or value_hrf_moving_average) for the current key
            if valStr in args.extraction.outputDict:                
                try:
                    # calculate min and max
                    currMax=max(float(newVal),float(args.extraction.outputDict[valStr]['max']))
                    currMin=min(float(newVal),float(args.extraction.outputDict[valStr]['min']))

                    args.extraction.outputDict[str(valStr)] = {'sum':str(float(args.extraction.outputDict[valStr]['sum'])+float(temp['sum'])),'count':args.extraction.outputDict[str(valStr)]['count']+1,'min':currMin,'max':currMax}

                    # if there are more than *beginMinMaxCalcs* values in the averaging period, add min and max to output file
                    if float(args.extraction.outputDict[str(valStr)]['count']) > args.beginMinMaxCalcs:
                        args.extraction.minmax=True
                except ValueError:
                    pass
            else:
                args.extraction.outputDict[str(valStr)] = temp
            valStr = ''            
            
            #if count==100:break # 调试用    
def AoT_reduction_writeFile(args):
    '''
    计算均值并将数据存储到更新的文件目录下

    Parameters
    ----------
    args : Class(dict)
        AttrDict方法的参数配置， AoT_reduction_setup()更新后参数.

    Returns
    -------
    None.

    '''    
    
    summation=0.0
    avg=0.0
    minimum=0.0
    maximum=0.0
    count=0
    
    # create the sub directory that will contain the reduced data and the copied metadata files
    if not os.path.exists(os.path.dirname(args.extraction.fileName)):
        try:
            os.makedirs(os.path.dirname(args.extraction.fileName))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    
    # erase whatever is currently in output csv file
    open(args.extraction.outputFile,'w').close()    
    
    # now should have a dictionary with key value pairs in the following format (keys are shown as their titles but in the actual dictionary are the actual values):
    # {'timestamp,node_id,subsystem,sensor,parameter':{'sum':sum,'count':count,'min':min,'max':max}}

    # update the output csv file's first line with the field names (removing 'value_hrf' (or 'value_hrf_moving_average') and 'value_raw') in the following format:
    # timestamp,node_id,subsystem,sensor,parameter,value_hrf_sum,value_hrf_count,value_hrf_average or timestamp,node_id,subsystem,sensor,parameter,value_hrf_sum,value_hrf_count,value_hrf_average,value_hrf_min,value_hrf_max
    with open (args.extraction.outputFile,'w') as f:    
        # remove un used field names
        try:
            args.extraction.fieldNames.remove('value_raw')
        except:
            pass
        try:
            args.extraction.fieldNames.remove('value_hrf_count')
        except:
            pass
        try:
            args.extraction.fieldNames.remove('value_hrf_sum')
        except:
            pass
        
        args.extraction.fieldNames.remove(args.extraction.hrfTitle)

        for i in range(0,len(args.extraction.fieldNames)):
            f.write(str(args.extraction.fieldNames[i])+',')

        # if there are more than *beginMinMaxCalcs* values in the averaging period, add min and max to output file
        if args.extraction.minmax==True:
            f.write('value_hrf_sum,value_hrf_count,value_hrf_average,value_hrf_min,value_hrf_max\n')
        else:
            f.write('value_hrf_sum,value_hrf_count,value_hrf_average\n')        
    
    # create the final output file
    with open (args.extraction.outputFile,'a') as f:    
        # for each item in the dictionary - calculate the average of each time period (row) using the sum and count
        # include the average in the value dictionary of outputDict
        for key,val in args.extraction.outputDict.items():
            avg=0
            summation=val['sum']
            minimum=val['min']
            maximum=val['max']
            count=val['count']
            
            try:
                avg=round(float(val['sum'])/val['count'],3)
                summation=round(float(val['sum']),3)
                minimum=round(float(val['min']),3)
                maximum=round(float(val['max']),3)
                val.update({'average':avg})
            except ValueError:
                val.update({'average':0})

            # write the whole row with the outputDict key (timestamp,node_id,subsystem,sensor,parameter) and the outputDict values (sum,count,average,max,min)
            # also include the average, max, and min if there are more than *beginMinMaxCalcs* values in the averaging period
            if args.extraction.minmax == True:    
                f.write(str(key)+','+str(summation)+','+str(count)+','+str(avg)+','+str(minimum)+','+str(maximum)+'\n')
            else:
                f.write(str(key)+','+str(summation)+','+str(count)+','+str(avg)+'\n')         
                
if __name__=="__main__" :        
    __C=AttrDict() 
    args=__C
    
    # 配置参数
    __C.period='1h' # Rows condense over this amt of time. Type an int followed by 's','m','h',or 'd' (e.g. '-t 30m').
    __C.path=r"D:\AoT\AoT_slice_2019"  # 待处理的AoT数据根目录
    __C.printLines=True # 是否打印计算进度，行信息
    __C.lines=1000 # 打印计算进度时，多少行更新一次信息
    __C.beginMinMaxCalcs=1000 # if there are more than *beginMinMaxCalcs* values in the averaging period, add min and max to output file
    
    # 默认参数（自动更新）
    __C.extraction=AttrDict()
    __C.extraction.inputFile=''
    __C.extraction.outputFile=''
    __C.extraction.fieldNames=[]
    __C.extraction.outputDict=OrderedDict()
    __C.extraction.period=0
    __C.extraction.minmax=False
    __C.extraction.dirPath=''
    __C.extraction.subDir=''
    __C.extraction.hrfTitle=''
    __C.extraction.fileName=''
    print(args)

    # begin timer for benchmarking
    timerStart=time.time()
    AoT_reduction_setup(args)
    #print(args)
    AoT_reduction_createData(args)   
    AoT_reduction_writeFile(args)
    
    # end timer and show run time
    timerEnd=time.time()
    runTime=timerEnd-timerStart
    print("-"*50)
    print("Done. ",end="")
    print("Took %.2fs to complete." % runTime)


    '''
    runfile('C:/Users/richi/omen_richiebao/omen_github/USDA_CH_final/USDA/notebook/aot_valid_hrf.py', wdir='C:/Users/richi/omen_richiebao/omen_github/USDA_CH_final/USDA/notebook')
    field names:['timestamp', 'node_id', 'subsystem', 'sensor', 'parameter', 'value_raw', 'value_hrf']
    1580262949it [4:29:19, 97794.52it/s] 
    
    runfile('C:/Users/richi/omen_richiebao/omen_github/USDA_CH_final/USDA/notebook/aot_reduction_data.py', wdir='C:/Users/richi/omen_richiebao/omen_github/USDA_CH_final/USDA/notebook')
    {'period': '1h', 'path': 'D:\\AoT\\AoT_slice_2019', 'printLines': True, 'lines': 1000, 'beginMinMaxCalcs': 1000, 'extraction': {'inputFile': '', 'outputFile': '', 'fieldNames': [], 'outputDict': OrderedDict(), 'period': 0, 'minmax': False, 'dirPath': '', 'subDir': '', 'hrfTitle': '', 'fileName': ''}}
    field names:['timestamp', 'node_id', 'subsystem', 'sensor', 'parameter', 'value_raw', 'value_hrf']
    1188048218it [21:09:50, 15593.13it/s]
    --------------------------------------------------
    Done. Took 76322.59s to complete.
    '''
