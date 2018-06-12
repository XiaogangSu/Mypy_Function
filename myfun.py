import os
import pandas as pd
import numpy as np
import xlrd
import csv
import math
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import copy

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率

def readtxt(filename,filepath,splitstr):
    path = filepath
    name = filename
    path_name = os.path.join(path, name)
    data_list = []
    fn = open(path_name)
    for line in fn:
        temp = line.split(splitstr)
        data_list.append(temp)
    fn.close()
    return (data_list)

def readexcel(filepath, filename, sheetname):  #filepath:文件路径，filename:文件名，sheetname:sheet名称
    data_list = []
    workbook = xlrd.open_workbook(os.path.join(filepath,filename))
    sheet = workbook.sheet_by_name(sheetname)
    nrows = sheet.nrows
    ncols = sheet.ncols
    for i in range(nrows):
        data_list.append([])
        for j in range(ncols):
            data_list[i].append(sheet.cell(i,j).value)
    return(data_list)

#读取csv文件，返回list,但list中的值会都转换为str,若表中存在str,读取之后数据都转换为str
def readcsv(filepath, filename):
    print('读取文件：'+filename)
    data_df = pd.read_csv(os.path.join(filepath, filename), header=None)
    data_list = np.array(data_df).tolist()
    return(data_list)

#data:数据名称(list)，epsg1:原始数据坐标系，epsg2:目标坐标系lon_index:经度数据列索引，lat_index:纬度数据列索引，alt_index: 高程列索引
#只返回投影后的经纬度高程列
def cor_tr(data, epsg1, epsg2, lon_index, lat_index, alt_index):
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")
    gdal.SetConfigOption("SHAPE_ENCODING", "")
    ogr.RegisterAll()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg1)
    sr_tar = osr.SpatialReference()
    sr_tar.ImportFromEPSG(epsg2)
    data_tr = []
    data_copy = copy.deepcopy(data)
    for val in data_copy:
        temppoint = ogr.Geometry(ogr.wkbPoint)
        temppoint.AssignSpatialReference(sr)
        temppoint.AddPoint(val[lon_index], val[lat_index], val[alt_index])
        # print(temppoint)
        temppoint.TransformTo(sr_tar)
        # print(temppoint.GetX(),temppoint.GetY(),temppoint.GetZ())
        data_tr.append([temppoint.GetX(),temppoint.GetY(), temppoint.GetZ()])
    return(data_tr)

#同cor_tr，返回输入列表的所有列
def cor_tr2(data, epsg1, epsg2, lon_index, lat_index, alt_index):
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")
    gdal.SetConfigOption("SHAPE_ENCODING", "")
    ogr.RegisterAll()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg1)
    sr_tar = osr.SpatialReference()
    sr_tar.ImportFromEPSG(epsg2)
    datacopy = copy.deepcopy(data)
    data_tr = datacopy
    i = -1
    for val in datacopy:
        i=i+1
        temppoint = ogr.Geometry(ogr.wkbPoint)
        temppoint.AssignSpatialReference(sr)
        temppoint.AddPoint(val[lon_index], val[lat_index], val[alt_index])
        # print(temppoint)
        temppoint.TransformTo(sr_tar)
        # print(temppoint.GetX(),temppoint.GetY(),temppoint.GetZ())
        data_tr[i][lon_index] = temppoint.GetX()
        data_tr[i][lat_index] = temppoint.GetY()
        data_tr[i][alt_index] = temppoint.GetZ()
        # data_tr.append([temppoint.GetX(),temppoint.GetY(), temppoint.GetZ()])
    return(data_tr)

#读取pointshp属性表，并且添加每个点的坐标信息(X,Y,Z),提取数据有表头信息
def read_pointshp(filepath, filename):
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")
    gdal.SetConfigOption("SHAPE_ENCODING", "")
    ogr.RegisterAll()
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = ogr.Open(os.path.join(filepath, filename), 0)
    if ds == None:
        print('打开文件%s失败！' % os.path.join(filepath, filename))
    else:
        print('打开文件%s成功！' % os.path.join(filepath, filename))
    lyr = ds.GetLayer(0)
    feanum = lyr.GetFeatureCount()
    print('点个数', feanum)
    data_list = []
    field_index = []   #属性表表头索引
    defn = lyr.GetLayerDefn()
    iFieldCount = defn.GetFieldCount()
    for index in range(iFieldCount):
        oField = defn.GetFieldDefn(index)
        field_index.append(oField.GetNameRef())
    for i in range(feanum):
        feat = lyr.GetNextFeature()
        # data_list.append([])
        temp = []
        for index in field_index:
            temp.append(feat.GetField(index))
        temp.append(feat.geometry().GetX())
        temp.append(feat.geometry().GetY())
        temp.append(feat.geometry().GetZ())
        data_list.append(temp)
    listname_part = ['X','Y','Z']
    list_name = field_index + listname_part
    data_list.insert(0, list_name)
    return(data_list)

#数据加密WGS84--->火星
def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret

def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret

def out_of_china(lng, lat):
    # 判断是否在国内，不在国内不做偏移 :param lng: :param lat: :return:
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

def wgs84togcj02(data, lon_index, lat_index):#data:数据list不header,lon_index 经度列索引,lat_index纬度列索引
    """
    （经度，纬度）
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    data_output = copy.deepcopy(data)   #深拷贝

    for i in range(len(data)):
        lng = float(data[i][lon_index])
        lat = float(data[i][lat_index])
        if out_of_china(lng, lat):  # 判断是否在国内
            print('第%d行数据(%.4f,%.4f)超出中国范围'%(i,lng,lat))
            continue
        dlat = transformlat(lng - 105.0, lat - 35.0)
        dlng = transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * pi
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
        dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
        mglat = lat + dlat
        mglng = lng + dlng
        data_output[i][lon_index] = mglng
        data_output[i][lat_index] = mglat
    return(data_output)

#火星坐标系转WGS84坐标系
def gcj02towgs84(data, lon_index, lat_index):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    data_output = copy.deepcopy(data)  # 深拷贝
    for i in range(len(data)):
        lng = float(data[i][lon_index])
        lat = float(data[i][lat_index])
        # print(data[i][lon_index], lng)
        if out_of_china(lng, lat):
            print('第%d行数据(%.4f,%.4f)超出中国范围' % (i, lng, lat))
            return(lng, lat)
        dlat = transformlat(lng - 105.0, lat - 35.0)
        dlng = transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * pi
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
        dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
        mglat = lat + dlat
        mglng = lng + dlng
        data_output[i][lon_index] = lng * 2 - mglng
        data_output[i][lat_index] = lat * 2 - mglat
    return(data_output)

def savecsv(savedata_list, savename, savepath):  #保存list到csv 参数：保存数据（list），保存文件名（str）,保存路径（str）
    path = savepath
    name = savename
    savedata_df = pd.DataFrame(savedata_list)
    savedata_df.to_csv(os.path.join(path, name), index=False, header=False)
    print(savename + '保存成功！')

def savetxt(datalist, savename, savepath):  #保存deepmotion转换后的数据为txt 参数：保存数据（list），保存文件名（str）,保存路径（str）
    path = savepath
    name = savename
    datacopy = copy.deepcopy(datalist)
    file = open(os.path.join(path, savename), 'w')
    for line in datacopy:
        line_str = str(line)
        try:
            line_str1 = line_str.replace(',', ' ')
        except:
            pass
        line_str2 = line_str1.replace('[', '')
        line_str3 = line_str2.replace(']', '\n')
        file.write(line_str3)
    file.close()
    print(savename+'保存成功！')

#input函数改善默认值输入 str输入说明，default_str,若输入为空时该值为默认值
def input_2(str,default_str):
    input_val = input(str)
    if input_val == '':
        input_val = default_str
        print(str,default_str)
    return(input_val)


