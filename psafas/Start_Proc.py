# !/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding=utf8

import os,uuid
import arcpy

import Tkinter as tk
from Tkinter import *
from tkinter import ttk
import tkFileDialog
import tkinter.font as font
from tkinter import messagebox
import sys

reload(sys)
sys.setdefaultencoding('utf8')


import sqlite3,json,random
import xml.etree.ElementTree as ET
import math


from Layer_Class   import *
from Basic_Func    import *
from Advanced_Func import *
from Psafas_Tools  import * 


#####################  CHEACKS ########################


arcpy.env.overwriteOutPut = True

# ErrorDictionary = {"1": "ערכים חסרים בשדות של שכבת חלקות",
#                     "2": "נקודת מודד חסרה",
#                     "3": "בדיקת טופולוגיה - חורים",
#                     "4": "בדיקת טופולוגיה - חפיפות",
#                     "5": "אי התאמה של חזית עם גבול חלקה",
#                     "6": "וורטקס ללא נקודה מהמודד",
#                     "7": "חזית חסרה",
#                     "8": "חזית כפולה",
#                     "9": "נקודת גבול כפולה",
#                     "10":"שטח חלקה לא עומד בתקן",
#                     "11":"מספר חלקה כפול",
#                     "12":"אי הצמדה של נקודת גבול לגבולות החלקה",
#                     "13":"מספר חלקה או גוש לא תקין",
#                     "14":"שונתה חלקה גובלת עם גושים חיצוניים לאזור העבודה"}

ErrorDictionary_services = {"1" : "בדיקת חלקות",
                    "2" : "בדיקת גושים",
                    "4": "בדיקת ערכים",
                    "8": "בדיקת חלקות מבוטלות"}

ErrorDictionary = {"1": "Missing Values in fields of parcel layer", # test
                    "2": "Missing modad point",
                    "3": "topology test - Holes",
                    "4": "topology test - Intersect",
                    "5": "arc and parcel are not overlap",
                    "6": "vertex without point from modad",
                    "7": "missing arc",
                    "8": "overlap arc",
                    "9": "double point",
                    "10":"area not standard",
                    "11":"double parcel ID",
                    "12":"Point not on parcel border",
                    "13":"Number of parcel or Gush are not Invalid",
                    "14":"Parcel changed in the border of AOI"}



def ShapeType(desc):
    
    if str(desc.shapeType) == 'Point':
        Geom_type = 'POINT'
    elif str(desc.shapeType) == 'Polyline':
        Geom_type = 'POLYLINE'
    else:
        Geom_type = 'POLYGON'
    return Geom_type

def print_arcpy_message(msg,status = 1):
    '''
    return a message :
    
    print_arcpy_message('sample ... text',status = 1)
    [info][08:59] sample...text
    '''
    msg = str(msg)
    
    if status == 1:
        prefix = '[info]'
        msg = prefix + str(datetime.datetime.now()) +"  "+ msg
        # print (msg)
        arcpy.AddMessage(msg)
        
    if status == 2 :
        prefix = '[!warning!]'
        msg = prefix + str(datetime.datetime.now()) +"  "+ msg
        print (msg)
        arcpy.AddWarning(msg)
            
    if status == 0 :
        prefix = '[!!!err!!!]'
        
        msg = prefix + str(datetime.datetime.now()) +"  "+ msg
        print (msg)
        arcpy.AddWarning(msg)
        msg = prefix + str(datetime.datetime.now()) +"  "+ msg
        print (msg)
        arcpy.AddWarning(msg)
            
        warning = arcpy.GetMessages(1)
        error   = arcpy.GetMessages(2)
        arcpy.AddWarning(warning)
        arcpy.AddWarning(error)
            
    if status == 3 :
        prefix = '[!FINISH!]'
        msg = prefix + str(datetime.datetime.now()) + " " + msg
        print (msg)
        arcpy.AddWarning(msg) 

def add_field(fc,field,Type = 'TEXT'):
    if arcpy.Exists(fc):
        TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
        if not TYPE:
            arcpy.AddField_management (fc, field, Type, "", "", 500)
        

def Delete_polygons(fc,del_layer,Out_put):

    desc = arcpy.Describe(fc)

    fc = arcpy.CopyFeatures_management(fc,Out_put)
    
    if desc.ShapeType == u'Point':
        del_layer_temp = 'in_memory' + '\\' + 'Temp'
        arcpy.Dissolve_management(del_layer,del_layer_temp)

        if desc.ShapeType == u'Point':
            geom_del = [row.shape for row in arcpy.SearchCursor (del_layer_temp)][0]
            Ucursor  = arcpy.UpdateCursor (Out_put)
            for row in Ucursor:
                point_shape = row.shape.centroid
                if geom_del.distanceTo(point_shape)== 0:
                    Ucursor.deleteRow(row)

                    del Ucursor
            else:
                print ("no points in the layer")
                        
    else:
        count_me = int(str(arcpy.GetCount_management(del_layer)))
        if count_me > 0:
            temp = 'in_memory' +'\\'+'_temp'
            arcpy.Dissolve_management(del_layer,temp)
            geom_del = [row.shape for row in arcpy.SearchCursor (temp)][0]
            Ucursor  = arcpy.UpdateCursor (Out_put)
            for row in Ucursor:
                geom_up     = row.shape
                new_geom    = geom_up.difference(geom_del)
                try:
                    row.shape = new_geom
                    Ucursor.updateRow (row)
                except:
                    pass
            del Ucursor
            arcpy.Delete_management(temp)
        else:
            pass

                        
    if desc.ShapeType == u'Point':
        pass
    else:
        up_cursor = arcpy.UpdateCursor(Out_put)
        for row in up_cursor:
            geom = row.shape
            if geom.area == 0:
                up_cursor.deleteRow(row)
        del up_cursor
        
    arcpy.RepairGeometry_management(Out_put)
    return Out_put

def Feature_to_polygon(path,Out_put):

    dif_name  = str(uuid.uuid4())[::5]
    path_diss = arcpy.Dissolve_management(path,r'in_memory\Dissolve_temp' + dif_name)


    def Split_List_by_value(list1,value,del_value = False):
         list_index = []
         for n, val in enumerate(list1):
              if val == value:
                   list_index.append(n)

         list_index.append(len(list1))

         list_val = []
         num = 0
         for i in list_index:
              list_val.append(list1[num:i])
              num = + i

         if del_value:
              for i in list_val:
                   for n in i:
                        if n is None:
                             i.remove(value)

         return list_val

            
    polygon = []
    cursor = arcpy.SearchCursor(path_diss)
    for row in cursor:
        geom = row.shape
        for part in geom:
            num = 0
            for pt in part:
                if pt:
                    polygon.append([pt.X,pt.Y])
                else:
                    polygon.append(None)

    poly    = Split_List_by_value(polygon,None,True)            
    feature = arcpy.CopyFeatures_management(path,Out_put)

    for i in poly[1:]:
        array = arcpy.Array()
        for n in i:
            array.add(arcpy.Point(n[0],n[1]))
        polygon      = arcpy.Polygon(array, arcpy.SpatialReference("Israel TM Grid"))
        in_rows      = arcpy.InsertCursor(feature)
        in_row       = in_rows.newRow()
        in_row.Shape = polygon
        in_rows.insertRow(in_row)
        
    arcpy.RepairGeometry_management(Out_put)
    return Out_put				
                      
def Calc_field_value_error(layer,append_layer,error_code,error_type):
    add_field(layer,"ERROR_TYPE")
    add_field(layer,"ERROR_Code")
    arcpy.CalculateField_management(layer, "ERROR_TYPE", "\""+error_type+"\"", "VB")
    arcpy.CalculateField_management(layer, "ERROR_Code", "\""+error_code+"\"", "VB")
    arcpy.Append_management(layer, append_layer, "NO_TEST")
    arcpy.Delete_management(layer)


def deleteErrorCode(layer, list_code):
    add_field(layer,"ERROR_Code")
    add_field(layer,"ERROR_TYPE")
    cursor = arcpy.da.UpdateCursor(layer,["ERROR_Code"])
    exe = [cursor.deleteRow() for row in cursor if row[0]if str(row[0]) in list_code]
                    

def topology_basic(final,gdb):

    memory        = r'in_memory'
    random_name   = str(uuid.uuid4())[::5]
    Diss          = memory + '\\' + 'dissolve'                + random_name
    feat_to_poly  = memory + '\\' + 'Feature_to_poly'         + random_name
    topo_holes    = memory + '\\' + 'Topolgy_Check_holes'     + random_name
    topo_inter    = memory + '\\' + 'Topolgy_Check_intersect' + random_name
    error_polygon = gdb     + '\\' + 'Errors_polygon'          

    deleteErrorCode (error_polygon, ["3"])
    deleteErrorCode (error_polygon, ["4"])

    arcpy.Dissolve_management                 (final.layer,Diss)
    Feature_to_polygon                        (Diss,feat_to_poly)
    Delete_polygons                           (feat_to_poly,Diss,topo_holes)

    arcpy.Intersect_analysis([final.layer],topo_inter)

    Calc_field_value_error  (topo_holes,error_polygon,"3",ErrorDictionary["3"])
    Calc_field_value_error  (topo_inter,error_polygon,"4",ErrorDictionary["4"])

    del_geom(error_polygon)

    arcpy.Delete_management(Diss)
    arcpy.Delete_management(feat_to_poly)

def del_geom(path):
    data      = [str(row[0].centroid.X) + "_" + str(row[0].centroid.Y) for row in arcpy.da.SearchCursor(path,['SHAPE@'])]
    to_delete = set()
    with arcpy.da.UpdateCursor(path,['SHAPE@']) as cursor:
        for row in cursor:
            key   = str (row[0].centroid.X) + "_" + str (row[0].centroid.Y)
            count = data.count(key)
            if count > 1:
                if key in to_delete:
                    cursor.deleteRow()
            to_delete.add(key)

def line_Not_on_parcels(ARC_bankal,Parcel_makor, gdb):

    #  # cuting layer , to work on less data # #

    # # Check Arc points\ID

    random_name    = str(uuid.uuid4())[::5]
    Boundery_touch = 'in_memory\\Boundery_touch' + random_name
    error_line     = gdb + "\\Errors_Line"
    feat_lyr       = 'ARC_bankal_lyr' + random_name

    deleteErrorCode                        (error_line, ["5"])

    arcpy.MakeFeatureLayer_management       (ARC_bankal.layer,feat_lyr)
    arcpy.SelectLayerByLocation_management  (feat_lyr ,"SHARE_A_LINE_SEGMENT_WITH",Parcel_makor.layer,'0.1 Meters',"NEW_SELECTION","INVERT")
    arcpy.Select_analysis                   (feat_lyr ,Boundery_touch)

    arcpy.RepairGeometry_management (Boundery_touch)


    Calc_field_value_error  (Boundery_touch,error_line,"5",ErrorDictionary["5"])


class Layer_Engine():

    def __init__(self,layer,columns = 'all'):

        if columns == 'all':
            columns = [f.name.encode('UTF-8') for f in arcpy.ListFields(layer)]
            columns.extend(['SHAPE@AREA'])
            columns.extend(['SHAPE@'])

        self.layer           = layer
        self.gdb             = os.path.dirname  (layer)
        self.name            = os.path.basename (layer)
        self.desc            = arcpy.Describe(layer)
        self.shapetype       = ShapeType(self.desc)
        self.oid             = str(self.desc.OIDFieldName)
        self.len_columns     = len(columns)
        self.data            = [row for row in arcpy.da.SearchCursor (self.layer,columns)]
        self.df              = pd.DataFrame(data = self.data, columns = columns)
        self.df["geom_type"] = self.shapetype
        self.len_rows        = self.df.shape[0]
        self.columns         = columns

        self.data_shape,self.set_= None,None


    def Extract_shape(self):
        
        if self.shapetype != 'POINT':
            self.data_shape          = [str(round(j.X,2)) + '-' + str(round(j.Y,2))  for i in arcpy.da.SearchCursor (self.layer,['SHAPE@']) if i[0] for n in i[0] for j in n if j]
            self.set_                = set(self.data_shape)
            self.df_shape            = pd.DataFrame(data = self.data_shape , columns = ['SHAPE'])
        else:
            self.data_shape          = [str(round(i[-1].centroid.X,2)) + '-' + str(round(i[-1].centroid.Y,2)) for i in self.data if i[-1]]
            self.set_                = set(self.data_shape)
            self.df_shape            = pd.DataFrame(data = self.data_shape , columns = ['SHAPE'])


def polygon_to_line(fc,layer_new):
    ws, fc_name = os.path.split (layer_new)
    s_r = arcpy.Describe (fc).spatialReference

    if arcpy.Exists(layer_new):
        arcpy.Delete_management(layer_new)
        
    line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)
        
    Search = arcpy.da.SearchCursor(fc,"SHAPE@"  )
    insert = arcpy.da.InsertCursor(line,"SHAPE@")

    exe = [insert.insertRow([arcpy.Polyline(arcpy.Array([arcpy.Point(point.X,point.Y)\
          for shape in row[0] for point in shape if point]))]) for row in Search]

    arcpy.RepairGeometry_management(layer_new)
    return layer_new

def generateCurves(fc):
    desc    = arcpy.Describe(fc)
    fc_name = desc.name
    fc_gdb  = desc.path
    Curves  = fc_gdb + "\\" + fc_name + "_curves_polygon"
    if arcpy.Exists(Curves):
        arcpy.Delete_management(Curves)
    arcpy.CreateFeatureclass_management(fc_gdb, fc_name + "_curves_polygon", "POLYGON", "", "", "",fc)
    for row in arcpy.da.SearchCursor(fc,['SHAPE@']):
        pts  = arcpy.Array()
        j = json.loads(row[0].JSON)
        if 'curve' in str(j):
            #print "You have true curves!"
            try:
                exe = [pts.add(arcpy.Point(f[0], f[1])) for i in row[0] if i for f in i if f]
            except:
                exe = [pts.add(f) for i in row[0] if i for f in i if f]
        if pts:
                pts.add(pts.getObject(0))
                polygon = arcpy.Polygon(pts, arcpy.SpatialReference("Israel TM Grid"))
                diff    = polygon.symmetricDifference(row[0])
                diff_sp = arcpy.MultipartToSinglepart_management(diff, arcpy.Geometry())
                if len(diff_sp) > 0:
                    arcpy.Append_management(diff_sp, Curves, "NO_TEST")
    return Curves



def Insert_needed_arc(parcel_bankal,arc_bankal,Keshet,gdb):

    random_name       = str(uuid.uuid4())[::5]
    arc_diss          = r'in_memory'  + '\\' + 'arc__Diss'      + random_name
    parce_to_line     = r'in_memory'  + '\\' + 'parcel_to_line' + random_name
    error_line        = gdb  + '\\' + 'Errors_Line'

    deleteErrorCode                        (error_line, ["7"])

    polygon_to_line                        (parcel_bankal.layer ,parce_to_line)
    arcpy.Dissolve_management              (arc_bankal.layer    ,arc_diss     )
    data = [i.shape for i in arcpy.SearchCursor(arc_diss)][0]
    with arcpy.da.UpdateCursor(parce_to_line,['SHAPE@']) as cursor:
        for row in cursor:
            geom      = row[0]
            new_geom  = geom.difference(data)
            row[0]    = new_geom
            cursor.updateRow(row)

    Del_Layer_on_ref(parce_to_line,Keshet)

    arcpy.RepairGeometry_management        (parce_to_line)
    # delete lines that on polygone with holes
    feat_lyr = 'par_to_line_lyr' + str(uuid.uuid4())[::5]
    arcpy.MakeFeatureLayer_management      (parce_to_line,feat_lyr)
    arcpy.SelectLayerByLocation_management (feat_lyr,"SHARE_A_LINE_SEGMENT_WITH",parcel_bankal.layer,"0.01 Meters",'','INVERT')
    arcpy.DeleteFeatures_management        (feat_lyr)

    del_geom(parce_to_line)

    Calc_field_value_error (parce_to_line,error_line,"7",ErrorDictionary["7"])


def Del_Layer_on_ref(layer,curve,invert = ''):
    name = 'par_' + str(random.randrange(0, 1000, 1))
    arcpy.MakeFeatureLayer_management      (layer,name)
    arcpy.SelectLayerByLocation_management (name,"INTERSECT",curve,'0.1 Meters','',invert)
    arcpy.DeleteFeatures_management        (name)

def Node_not_on_parcel(parcel_all,PARCEL_NODE_EDIT,gdb):

    node_error = gdb + '\\' + 'Errors_Point'
    Error_temp = r'in_memory' + '\\' + 'Error_temp'

    deleteErrorCode (node_error, ["12"])
    feat_name = 'node_final_lyr' + str(uuid.uuid4())[::5]

    arcpy.MakeFeatureLayer_management      (PARCEL_NODE_EDIT,feat_name)
    arcpy.SelectLayerByLocation_management (feat_name ,"BOUNDARY_TOUCHES",parcel_all.layer,'0.01 Meters',"","INVERT")
    arcpy.Select_analysis                  (feat_name ,Error_temp)

    Calc_field_value_error (Error_temp,node_error,"12",ErrorDictionary["12"])

def vertex_without_modad_point(layer_parcel,parcel_modad,node_modad,gdb):

    node_error    = gdb + '\\' + 'Errors_Point'
    Error_t    = 'parcel_vertex_lyr'
    layer         = gdb + '\\' + 'parcel_vertexs'
    Error_temp    = gdb + '\\' + 'Error_temp'

    arcpy.CopyFeatures_management([arcpy.PointGeometry(arcpy.Point(j.X,j.Y)) for i in arcpy.SearchCursor (layer_parcel.layer) for n in i.shape for j in n if j],layer)

    arcpy.MakeFeatureLayer_management      (layer,Error_t)
    arcpy.SelectLayerByLocation_management (Error_t,"INTERSECT",node_modad.layer,'0.01 meters',"NEW_SELECTION","INVERT")

    deleteErrorCode (node_error, ["6"])

    Del_Layer_on_ref       (Error_t,parcel_modad,'INVERT')

    arcpy.Dissolve_management (Error_t,Error_temp,'','',False)
    Calc_field_value_error    (Error_temp,node_error,"6",ErrorDictionary["6"])


def missing_modad_point(layer_node,parcel_modad,node_modad,gdb):

    node_error = gdb + '\\' + 'Errors_Point'
    Error_temp = 'layer_node_lyr'

    deleteErrorCode (node_error, ["2"])

    arcpy.CopyFeatures_management(layer_node.layer,'in_memory\\Node_copy')

    # check = layer_node.layer - node_modad.layer
    arcpy.MakeFeatureLayer_management     ('in_memory\\Node_copy','layer_node_lyr')
    arcpy.SelectLayerByLocation_management('layer_node_lyr',"INTERSECT",node_modad.layer,'0.01 meters',"NEW_SELECTION","INVERT")

    Del_Layer_on_ref       (Error_temp,parcel_modad,'INVERT')
    Calc_field_value_error (Error_temp,node_error,"2",ErrorDictionary["2"])


def double_arc(gdb,arc):

    Error_line = gdb            + '\\' + 'Errors_Line'
    arc_inter  = r'in_memory'  + '\\' + 'arc_intersect' + str(uuid.uuid4())[::5]

    deleteErrorCode                   (Error_line, ["8"])
    arcpy.Intersect_analysis          ([arc],arc_inter)
    del_geom                          (arc_inter)

    Calc_field_value_error (arc_inter,Error_line,"8",ErrorDictionary["8"])


def double_node(gdb,node):

    Errors_Point = gdb           + '\\' + 'Errors_Point'
    node_inter   = r'in_memory'  + '\\' + 'node_inter' + str(uuid.uuid4())[::5]

    deleteErrorCode          (Errors_Point, ["9"])
    arcpy.Intersect_analysis ([node],node_inter)
    Calc_field_value_error   (node_inter,Errors_Point,"9",ErrorDictionary["9"])


def Parcel_data_attri(path_after,ws):

    path_before = ws + '\\' + 'PARCEL_ALL_EDIT_copy'
    conn        = sqlite3.connect(":memory:")
    c           = conn.cursor()

    c.execute("""CREATE TABLE Before_Table (
                        PARCEL      INTEGER,
                        GUSH_NUM    INTEGER,
                        KEY         text,
                        GUSH_SUFFIX INTEGER
                        )""")

    c = conn.cursor()
    c.execute("""CREATE TABLE Table_After (
                        PARCEL      INTEGER,
                        GUSH_NUM    INTEGER,
                        KEY         text,
                        GUSH_SUFFIX INTEGER
                        )""")

    for i in arcpy.SearchCursor(path_before):
        c.execute ("INSERT INTO Before_Table VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM)+"-"+ str(i.GUSH_SUFFIX)+"',"+str(i.GUSH_SUFFIX)+")")

    for i in arcpy.SearchCursor(path_after):
        Gush     = i.GUSH_SUFFIX
        parcel   = i.PARCEL
        gush_num = i.GUSH_NUM
        if not i.GUSH_SUFFIX:
            Gush = 0
        if not i.PARCEL:
            parcel = 0
        if not i.GUSH_NUM:
            gush_num = 0

        c.execute ("INSERT INTO Table_After VALUES (" + str(parcel) +','+ str(gush_num) + ",'"+str(parcel)+"-"+str(gush_num) +"-"+ str(Gush)+"',"+str(Gush)+")")

    count_before = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Before_Table group by KEY) t1 WHERE t1.count > 1;''')]
    count_after  = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Table_After group by KEY) t1 WHERE t1.count > 1;''')]

    if count_before:
        msg  =  " # # # WARNING # # # Found identical parcels on orig parcels : {}".format(count_before)
        print_arcpy_message(msg,1)

    if count_before:
        msg2 = " # # # WARNING # # # Found identical parcels on new parcels : {}".format(count_after)
        print_arcpy_message(msg2,1)


    add_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Table_After A LEFT JOIN Before_Table B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]
    del_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Before_Table A LEFT JOIN Table_After B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]


    print_arcpy_message("added parcels:   {}  ".format(add_parcels),1)
    print_arcpy_message("Deleted parcels: {}  ".format(del_parcels),1)

def Calc_Area(lyr,ws,gdb):
    def math_delta_rashum(area_rashum):
        area_rashum = float(area_rashum)
        delta1 = (0.3 * (math.sqrt(area_rashum)) + (0.005 * area_rashum))
        delta2 = (0.8 * (math.sqrt(area_rashum)) + (0.002 * area_rashum))
        if delta1 > delta2:
            delta = delta1
        else:
            delta = delta2
        return delta
                                     
    def find_problem(Area_rasum,Shape_area,delta):
        minus = abs(Area_rasum - Shape_area)
        if minus > delta:
            return 'Warning, Delta is to big'
        else:
            return 'Ok'
        
    cut_bankal    = ws  + '\\' + 'cut_bankal'
    tazar_copy    = ws  + '\\' + 'PARCELS_inProc_edit_copy'
    error_polygon = gdb + '\\' + 'Errors_Polygon'

    deleteErrorCode (error_polygon, ["10"])

    feat_name = 'lyr_layer' + str(uuid.uuid4())[::5]
    if arcpy.Exists(cut_bankal):
        arcpy.Delete_management(cut_bankal)

    arcpy.MakeFeatureLayer_management      (lyr,feat_name, "\"LEGAL_AREA\" IS NOT NULL")
    arcpy.SelectLayerByLocation_management (feat_name,"INTERSECT",tazar_copy,'100 Meters')
    arcpy.Select_analysis                  (feat_name,cut_bankal)

        
    fields = [["GAP", "DOUBLE"],["delta", "DOUBLE"],["Check", "TEXT"]]
    for i in fields:
        try:
            arcpy.AddField_management(cut_bankal,i[0], i[1])
        except:
            pass

    with arcpy.da.UpdateCursor(cut_bankal,["LEGAL_AREA","SHAPE_Area","GAP","delta","Check"]) as up_cursor:
        for row in up_cursor:
            delta  = math_delta_rashum(row[0])
            row[3] = delta
            row[2] = abs(row[1] - row[0])- delta
            row[4] = find_problem(row[0],row[1],delta)
            up_cursor.updateRow (row)
    del up_cursor

    feat_lyr = 'cut_bankal_del' + str(uuid.uuid4())[::5]
    arcpy.MakeFeatureLayer_management  (cut_bankal, feat_lyr,"\"Check\" = 'Ok'")
    arcpy.DeleteFeatures_management    (feat_lyr)

    Calc_field_value_error (cut_bankal,error_polygon,"10",ErrorDictionary["10"])

def Check_accurancy_pracel(fc,gdb):

    Error_Polygon = gdb + '\\' + 'Errors_Polygon'

    deleteErrorCode (Error_Polygon, ["11"])

    list_fields = ["GUSH_NUM","GUSH_SUFFIX","PARCEL","LEGAL_AREA","PNUMTYPE","TALAR_NUMBER","TALAR_YEAR","SYS_DATE","KEY"]

    add_field(fc,'KEY',Type = 'TEXT')
    with arcpy.da.UpdateCursor(fc,list_fields) as cursor:
        for row in cursor:
            row[-1] = str(row[0]) +'-' + str(row[1])+ '-' + str(row[2])
            cursor.updateRow(row)

    x = [row[0] for row in arcpy.da.SearchCursor (fc,["KEY"])]

    arcpy.RemoveSpatialIndex_management(Error_Polygon)
    in_rows = arcpy.InsertCursor(Error_Polygon)
    with arcpy.da.SearchCursor(fc,["KEY",'SHAPE@']) as cursor:
            for row in cursor:
                    count = x.count(row[0])
                    if count > 1:
                        in_row            = in_rows.newRow()
                        in_row.Shape      = row[1]
                        in_row.ERROR_Code = '11'
                        in_row.ERROR_TYPE = ErrorDictionary["11"]
                        in_rows.insertRow(in_row)
    del in_rows

def missing_Values_in_parcel(Parcel_makor,ws,gdb):

    error_polygon = gdb + '\\' + 'Errors_Polygon'

    deleteErrorCode (error_polygon, ["1"])
    field_mising = ws + '\\' +'Field_missing'
    #arcpy.CreateFeatureclass_management(p_gdb,'Field_missing',"POLYGON") 

    arcpy.Select_analysis(Parcel_makor,field_mising,"\"PARCEL\" is null or \"GUSH_NUM\" is null or \"GUSH_SUFFIX\" is null or \"LEGAL_AREA\" is null  or \"TALAR_NUMBER\" is null or \"TALAR_YEAR\" is null")
    add_field(field_mising,"ERROR_TYPE",'TEXT')
    add_field(field_mising,"ERROR_Code",'TEXT')

    arcpy.CalculateField_management(field_mising,'ERROR_Code', "\"1\"",'VB')
    arcpy.CalculateField_management(field_mising,'ERROR_Type', "\"missing values\"",'VB')

    Calc_field_value_error  (field_mising,error_polygon,"1",ErrorDictionary["1"])


def Find_not_exists_parcel_in_Gush(parcel_all_final,ws,gdb):

    Tazar         = ws + '\\' + 'PARCELS_inProc_edit_copy'
    parcel_before = ws + '\\' + 'PARCEL_ALL_EDIT_copy'
    parcel_Error  = gdb + '\\' + 'Errors_Polygon'

    deleteErrorCode (parcel_Error, ["13"])

    bankal_before   = [str(i.PARCEL) +'-'+str(i.GUSH_NUM) for i in arcpy.SearchCursor(parcel_before)]
    Tazar           = [str(i.PARCEL) +'-'+str(i.GUSH_NUM) for i in arcpy.SearchCursor(Tazar)]


    ## Calc sets ##

    exists_before      = set(bankal_before + Tazar)
    bankal_after       = set([str(i.PARCEL) +'-'+str(i.GUSH_NUM) for i in arcpy.SearchCursor(parcel_all_final)])
    Miss_parcel_gush   = list(bankal_after   - exists_before)
    Miss_parcel_gush2  = list(exists_before   - bankal_after)

    up_rows = arcpy.InsertCursor(parcel_Error)

    with arcpy.da.SearchCursor(parcel_all_final,['PARCEL','GUSH_NUM','SHAPE@']) as cursor:
        for row in cursor:
            key = str(row[0]) +'-'+str(row[1])
            if key in Miss_parcel_gush:
                in_row            = up_rows.newRow()
                if row[2]:
                    in_row.Shape      = row[2]
                in_row.ERROR_Code = '13'
                in_row.ERROR_TYPE = ErrorDictionary["13"]
                up_rows.insertRow(in_row)
    del cursor

def get_envelop_area(path,num):
    # Temp_layers
    path_diss = r'in_memory\dissolve'  + str(uuid.uuid4())[::5] + str(num)
    New_Line  = r'in_memory\New_Line'  + str(uuid.uuid4())[::5] + str(num)
    cut_layer = r'in_memory\cut_layer' + str(uuid.uuid4())[::5] + str(num)

    feat_name = 'path_lyr' + str(uuid.uuid4())[::5] + str(num)
    # procssing 
    arcpy.Dissolve_management              (path,path_diss)
    polygon_to_line                        (path_diss,New_Line)
    arcpy.MakeFeatureLayer_management      (path, feat_name)
    arcpy.SelectLayerByLocation_management (feat_name, "BOUNDARY_TOUCHES",New_Line)
    arcpy.Select_analysis                  (feat_name, cut_layer)

    data = {int(row[0]):row[1] for row in arcpy.da.SearchCursor(cut_layer,['PARCEL_ID','SHAPE@']) if row[0] if row[1]}

    return data

def Found_bad_parcel_around_AOI(path_new,ws,gdb):
    Errors_Polygon  = gdb + '\\' + 'Errors_Polygon'

    deleteErrorCode (Errors_Polygon, ["14"])

    path_orig = ws + '\\' + 'PARCEL_ALL_EDIT_copy'
    data_orig = get_envelop_area(path_orig,1)
    data_new  = get_envelop_area(path_new,2)

    list_area_problem = [[key,data_new[key],data_orig[key]] for key in data_orig if (key in data_new and round(data_orig[key].area,1) != round(data_new[key].area,1))]
    # list_key_problem  =  list(set(data_orig.keys()).symmetric_difference(set(data_new.keys())))

    geoms = []
    if len(list_area_problem) > 0:
        for i in list_area_problem: print_arcpy_message("key: {} has changed, from area of: {}, to area of: {}".format(i[0],round(i[1].area,2),round(i[2].area,2)),2)
        
        geoms   = [i[1] for i in list_area_problem]
        fields  = ['SHAPE@','ERROR_Code','ERROR_TYPE']
        insert = arcpy.da.InsertCursor(Errors_Polygon,fields)

        insertion = [insert.insertRow  ([value,'14',ErrorDictionary["14"]])\
                    for value in geoms]

def get_layer_by_fc_name(fc_name,CURRENT):
    mxd = arcpy.mapping.MapDocument(CURRENT)
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
    if df:
        lyrs = arcpy.mapping.ListLayers(mxd,"*", df)
        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if lyr.datasetName == fc_name:
                    return lyr.dataSource


def XML_to_Table(xml_string, gdb, df):

    #xml_string = xml_string.replace("-","")
    #print xml_string
    root = ET.fromstring(xml_string)
    data = root.getchildren()

    rows = [ParcelError for ParcelError in [ParcelErrors for ParcelErrors in data]]
    rows = rows[0].getchildren()

    if len(rows) == 0:
        #pythonaddins.MessageBox('לא נמצאו שגיאות','INFO',0)
        pythonaddins.MessageBox('No Errors Found','INFO',0)
    else:
        fields = [field.tag.replace("{http://tempuri.org/}", "") for field in rows[0].getchildren() if field.tag.replace("{http://tempuri.org/}", "") != "ErrInfo"]
        err_infos = rows[0][-1].getchildren()
        for err_info in err_infos:
            fields.append(err_info.tag.replace("{http://tempuri.org/}", ""))
        print (fields)

        
        arcpy.CreateTable_management(gdb, "Errors")
        for field in fields:
            arcpy.AddField_management(gdb + "\\Errors", field, "TEXT")
            
        all_values = []
        for row in rows:
            fields = [field.tag.replace("{http://tempuri.org/}", "") for field in row.getchildren() if field.tag.replace("{http://tempuri.org/}", "") != "ErrInfo"]
            values = [field.text for field in row.getchildren() if '\n' not in field.text]
            err_infos = row[-1].getchildren()
            for err_info in err_infos:
                fields.append(err_info.tag.replace("{http://tempuri.org/}", ""))
                values.append(err_info.text)
            #print zip(fields, values)
            all_values.append(zip(fields, values))

        rows = arcpy.InsertCursor(gdb + "\\Errors")
        for values in all_values:
            row = rows.newRow()
            print (values)
            for row_val in values:
                row.setValue(row_val[0], row_val[1])
            rows.insertRow(row)


        del row
        del rows
        #pythonaddins.MessageBox('Errors Found','INFO',0)
    
    print_arcpy_message(df.name, 1)
    error_table = arcpy.mapping.TableView(gdb + "\\Errors")
    arcpy.mapping.AddTableView(df,error_table)

    #arcpy.mapping.AddLayer(df, error_table, "BOTTOM")

    arcpy.RefreshActiveView()
        #pythonaddins.MessageBox('Error table have been added to the map','INFO',0)
        #pythonaddins.MessageBox('טבלת שגיאות נוספה למפה','INFO',0)


# # # # # # Geometry # # # # # 

def Cheaks(CURRENT):

    select_all_cbx = 'true'                


    if select_all_cbx == 'true':
        topology_basic_cbx               = 'true'
        line_Not_on_parcels_cbx          = 'true'
        Missing_arc_cbx                  = 'true'
        Node_not_on_parcel_cbx           = 'true'
        vertex_without_modad_point_cbx   = 'true'
        missing_modad_point_cbx          = 'true'
        double_arc_cbx                   = 'true'
        double_node_cbx                  = 'true'
        Parcel_data_cbx                  = 'true'
        Check_area_in_tazar_cbx          = 'true'
        Gush_parcel_doubled_cbx          = 'true'
        missing_Values_in_parcel_cbx     = 'true'
        Parcel_gush_number_not_vaild_cbx = 'true'
        Found_bad_parcel_around_AOI_cbx  = 'true'



    lyr_dataSource = get_layer_by_fc_name('PARCELS_inProc_edit',CURRENT)
    arcpy.AddMessage(lyr_dataSource)

    if lyr_dataSource:
        # extract from script location
        scriptPath = os.path.abspath(__file__)
        Scripts    = os.path.dirname(scriptPath)
        ToolShare  = os.path.dirname(Scripts)
        Scratch    = ToolShare + "\\Scratch"
        ToolData   = ToolShare + "\\ToolData"

        # extract from MXD
        mxd           = arcpy.mapping.MapDocument   (CURRENT)
        df            = arcpy.mapping.ListDataFrames  (mxd)[0]
        gdb           = os.path.dirname  (lyr_dataSource)
        folder_source = os.path.dirname  (gdb)
        name          = os.path.basename (folder_source)
        tazar_num     = ''.join([i for i in name if i.isdigit()])
        ws = Scratch + '\\' + 'Tazar_{}.gdb'.format(tazar_num)
        arcpy.AddMessage(ws)
    else:
        sys.exit()


    # final layers
    parcel_all  = gdb + '\\' + 'PARCEL_ALL_EDIT'
    arc_all     = gdb + '\\' + 'PARCEL_ARC_EDIT'
    node_all    = gdb + '\\' + 'PARCEL_NODE_EDIT'

    # modad layers
    node_modad    = gdb + '\\' + 'POINTS_inProc_edit'
    parcel_modad  = gdb + '\\' + 'PARCELS_inProc_edit'
    arc_modad     = gdb + '\\' + 'LINES_inProc_edit'


    layer_parcel     = Layer_Engine(parcel_all)
    layer_arc        = Layer_Engine(arc_all)
    layer_node       = Layer_Engine(node_all)

    lyr_node_modad   = Layer_Engine(node_modad)

    layer_parcel.Extract_shape  ()

    Keshet = generateCurves(layer_parcel.layer)

    if topology_basic_cbx == 'true':
        print_arcpy_message  (ErrorDictionary["3"],1)
        print_arcpy_message  (ErrorDictionary["4"],1)
        topology_basic       (layer_parcel,gdb)

    if line_Not_on_parcels_cbx == 'true':
        print_arcpy_message  (ErrorDictionary["5"],1)
        line_Not_on_parcels  (layer_arc,layer_parcel, gdb)

    if Missing_arc_cbx == 'true':
        print_arcpy_message (ErrorDictionary["7"],1)
        Insert_needed_arc   (layer_parcel,layer_arc,Keshet,gdb)

    if Node_not_on_parcel_cbx == 'true':
        print_arcpy_message (ErrorDictionary["12"],1)
        Node_not_on_parcel  (layer_parcel,layer_node.layer,gdb)

    if vertex_without_modad_point_cbx == 'true':
        print_arcpy_message (ErrorDictionary["6"],1)
        vertex_without_modad_point  (layer_parcel,parcel_modad,lyr_node_modad,gdb)

    if missing_modad_point_cbx == 'true':
        print_arcpy_message (ErrorDictionary["2"],1)
        missing_modad_point (layer_node,parcel_modad,lyr_node_modad,gdb)

    if double_arc_cbx == 'true':
        print_arcpy_message (ErrorDictionary["8"],1)
        double_arc          (gdb,arc_all)

    if double_node_cbx == 'true':
        print_arcpy_message (ErrorDictionary["9"],1)
        double_node         (gdb,node_all)

    if Parcel_data_cbx == 'true':
        print_arcpy_message ('חלקות יוצאות ונכנסות',1)
        Parcel_data_attri         (layer_parcel.layer,ws)

    if Check_area_in_tazar_cbx == 'true':
        print_arcpy_message             (ErrorDictionary["10"],1)     
        Calc_Area                       (layer_parcel.layer,ws,gdb)

    if Gush_parcel_doubled_cbx == 'true':
        print_arcpy_message             (ErrorDictionary["11"],1)
        Check_accurancy_pracel          (layer_parcel.layer,gdb)

    if missing_Values_in_parcel_cbx == 'true':
        print_arcpy_message             (ErrorDictionary["1"],1)
        missing_Values_in_parcel        (layer_parcel.layer,ws,gdb)

    if Parcel_gush_number_not_vaild_cbx == 'true':
        print_arcpy_message             (ErrorDictionary["13"],1)
        Find_not_exists_parcel_in_Gush  (layer_parcel.layer,ws,gdb)

    if Found_bad_parcel_around_AOI_cbx == 'true':
        print_arcpy_message             (ErrorDictionary["14"],1)
        Found_bad_parcel_around_AOI     (layer_parcel.layer,ws,gdb)






#######################################################

arcpy.env.overwriteOutput = True


def Get_layer_gdb(gdb):

    parcel_bankal = gdb + '\\' + 'PARCEL_ALL_EDIT'
    arc_bankal    = gdb + '\\' + 'PARCEL_ARC_EDIT'
    point_bankal  = gdb + '\\' + 'PARCEL_NODE_EDIT'

    parcel_modad  = gdb + '\\' + 'PARCELS_inProc_edit'
    arc_modad     = gdb + '\\' + 'LINES_inProc_edit'
    point_modad   = gdb + '\\' + 'POINTS_inProc_edit'

    return parcel_bankal,arc_bankal,point_bankal,parcel_modad,arc_modad,point_modad

def Get_layer_gdb_Copy(GDB):

    parcel_bankal_c = GDB + '\\' + 'PARCEL_ALL_EDIT_copy'
    arc_bankal_c    = GDB + '\\' + 'PARCEL_ARC_EDIT_copy'
    point_bankal_c  = GDB + '\\' + 'PARCEL_NODE_EDIT_copy'

    parcel_modad_c  = GDB + '\\' + 'PARCELS_inProc_edit_copy'
    arc_modad_c     = GDB + '\\' + 'LINES_inProc_edit_copy'
    point_modad_c   = GDB + '\\' + 'POINTS_inProc_edit_copy'

    return parcel_bankal_c,arc_bankal_c,point_bankal_c,parcel_modad_c,arc_modad_c,point_modad_c


def PSAFAS(parcel_tazar,mxd_newPath):

    scriptPath = os.path.abspath(__file__)
    Scripts    = os.path.dirname(scriptPath)
    ToolShare  = os.path.dirname(Scripts)
    Scratch    = ToolShare + "\\Scratch"
    ToolData   = ToolShare + "\\ToolData"

    parcels_bankal         = parcel_tazar
    Dis_border_pnts        = 1
    Folder                 = Scratch
    Dis_limit_border_pnts  = 1
    sett                   = ToolData + '\\' + r'Set.gdb\Sett'
    CURRENT                = mxd_newPath


    print_arcpy_message     ("# # # # # # # S T A R T # # # # # #",status = 1)


    layers_to_Copy  = ['PARCEL_ALL_EDIT','PARCEL_ARC_EDIT','PARCEL_NODE_EDIT','PARCELS_inProc_edit','LINES_inProc_edit','POINTS_inProc_edit']

    GDB_Source      = getLayerPath     (parcels_bankal,CURRENT)
    GDB             = CreateWorkingGDB (GDB_Source,Folder,layers_to_Copy,'PARCELS_inProc_edit',CURRENT)

    # קריאה של שכבות העבודה מבסיס הנתונים המקורי והחדש
    parcel_bankal    ,arc_bankal    ,point_bankal    ,parcel_modad     , arc_modad    ,  point_modad    = Get_layer_gdb       (GDB_Source)
    parcel_bankal_c  ,arc_bankal_c  ,point_bankal_c  ,parcel_modad_c   , arc_modad_c  ,  point_modad_c  = Get_layer_gdb_Copy  (GDB)

    # שכבות עזר

    Continue   = True                         # בדיקת צורך בהמשך פעולות גאומטריות, יהיה שלילי כאשר לא היו בעיות גאומטריות 
    holes_2    = GDB + '\\' + 'Holes_Check_2' # return from func: CheckResultsIsOK(AOI,tazar_border,2)
    inter2     = GDB + '\\' + 'Intersect_Check_2'
    AOI2       = GDB + '\\' + 'AOI2'          # clean_slivers_by_vertex
    AOI3       = GDB + '\\' + 'AOI3'          # after using: fix_holes_by_neer_length
    AOI_best   = ''                           # return the last AOI Layer
    AOI_final  = GDB + '\\' + 'AOI_Final'
    AOI_Point  = GDB + '\\' + 'AOI_Point'
    AOI_Line   = GDB + '\\' + 'AOI_Line'
    AOI_Fix    = GDB + '\\' + 'Fix_holes'

    diss_aoi   = r'in_memory' + '\\' +'diss_aoi'

    if CheckIfSkipProcess(parcel_bankal_c,parcel_modad_c,GDB):
        print_arcpy_message     ("Exit",status = 1)
        sys.exit(0)

    ChangeFieldNames                   (parcel_modad_c,arc_modad_c,point_modad_c)  # שינוי שמות השדות לפורמט בנק"ל
    connect_parcel_to_sett             (parcel_modad_c,sett,parcel_bankal_c)       # הזנה של שמות ומספרי מפתח של ישובים לחלקות ניסיון ראשון

    AOI,tazar_border,Curves,parcel_Bankal_cut,Point_bankal_Cut = PrePare_Data    (parcel_bankal_c,parcel_modad_c,point_modad_c,point_bankal_c,GDB,'POINT_NAME','POINT_NAME')

    Get_Attr_From_parcel               (AOI,parcel_modad_c)                        #במידה והכלי מאתר שכל הישובים מסביב אותו דבר connect_parcel_to_sett גורס את הפעולה של
    Fix_curves                         (AOI,tazar_border,Curves)


    if CheckResultsIsOK(AOI,tazar_border,1):
        AOI_best  = AOI
        Continue  = False

        # # # # # # # # בודק אם יש שינוי בגבולת אך ללא שינוי בתוך התצר, במידה ואין שינוי בגבולות, מחליף בין היישויות
    Sub_Processing(parcel_bankal,parcel_modad_c,point_bankal,point_modad,arc_bankal,arc_modad,tazar_border,parcel_modad_c,AOI,GDB)

    if Continue:
        
        if not Dis_border_pnts:
            Dis_border_pnts = get_default_Snap_border (Point_bankal_Cut,parcel_modad_c,Dis_limit_border_pnts)
        else:
            print_arcpy_message('1', status=1)

        Snap_border_pnts        (tazar_border ,AOI,Dis_border_pnts) # סתימת חורים ע"י הזזת נקודות גבול
        Update_Polygons         (AOI , parcel_modad_c)
        Fix_curves              (AOI,tazar_border,Curves)
        AOI_best  = AOI

        if CheckResultsIsOK(AOI,tazar_border,2):                
            Continue   = False

    if arcpy.Exists(holes_2):
        if int(str(arcpy.GetCount_management(holes_2))) == 0 and arcpy.Exists(inter2):
            holes_2 = inter2
    else:
        holes_2 = inter2

        # # # # # # # במידה ואין חורים, ויש אינטרסקטים קטנים ממוצע של 1, הכלי ידלג על המשך הפעולות הגאומטריות

    if Continue:
        names_curves              (AOI ,parcel_modad_c,Curves)
        clean_slivers_by_vertex   (AOI ,holes_2,tazar_border,2,AOI2)
        Update_Layer_Curves_By_ID (AOI2,parcel_modad_c,Curves)
        Clean_non_exist_pnts      (AOI2,tazar_border ,parcel_bankal_c,parcel_modad_c)
        Update_Layer_Curves_By_ID (AOI2,parcel_modad_c,Curves)
        AOI_best  = AOI2
            # # # # # # Check if all holes are closed after the Geometry tool
        if CheckResultsIsOK(AOI2,tazar_border,3):
            Continue   = False

    if Continue:
            # # # # # # # Work Only if there is still Holes
        fix_holes_Overlaps_By_Length  (AOI2,tazar_border   ,AOI3)      # סתימת חורים ע"י שיוך לפי קו גדול משותף גדול ביותר
        clean_pseudo                  (AOI3,tazar_border   ,Curves)
        Update_Layer_Curves_By_ID     (AOI3,parcel_modad_c ,Curves)

        AOI_best = AOI3

    CheckResultsIsOK(AOI_best,tazar_border,5)

    Delete_small_double_parcel    (AOI_best)
    fix_holes_Overlaps_By_Length  (AOI_best,tazar_border   ,AOI_Fix) 
    stubborn_parts                (AOI_Fix,parcel_bankal_c,parcel_modad_c,AOI_final,Curves)
    Update_Layer_Curves_By_ID     (AOI_final,parcel_modad_c,Curves)

    CheckResultsIsOK              (AOI_final,tazar_border,6)

    fix_tolerance                 (AOI_final,tazar_border)
    get_no_node_vertex            (AOI_final,tazar_border,point_modad_c,Point_bankal_Cut)
    Delete_curves_out_AOI         (AOI_final,parcel_bankal)
    Fix_Multi_part_Bankal         (AOI_final,tazar_border,parcel_Bankal_cut) # מתקן חלקות רחוקות שנפגעו בגלל שיש בהן חורים
    Update_Polygons               (AOI_final,parcel_modad_c)
    CheckResultsIsOK              (AOI_final,tazar_border,7)                # בדיקת סופית, כמה חורים נשארו

    #  #  #  #  #  # # Prepare Insert to Razaf  #  #  #  #  #  #  # 
    print_arcpy_message ("  #   #   #    # Preper data For Insert  #   #   #   #  ")

    Calculate_Area_Rashum   (AOI_final)
    NewGushim               (parcel_modad_c, parcel_bankal,AOI_final)
    Get_Point_AOI           (AOI_final,point_bankal_c,point_modad_c,AOI_Point)
    Create_Line_AOI         (AOI_final,tazar_border,Curves,arc_bankal_c,AOI_Line)

    #  #  #  #  #  #  # insert To Razaf #  #  #  #  #  #  #  # #

    print_arcpy_message ("  #   #   #    # insert To Razaf  #   #   #   #  ")

    # # # # # Polygons 

    Update_Polygons           (parcel_bankal,AOI_final)

    # # # # Lines

    arcpy.Dissolve_management (AOI_final,diss_aoi)
    Layer_Management          (arc_bankal).Select_By_Location ('COMPLETELY_WITHIN',diss_aoi)
    arcpy.Append_management   (AOI_Line,arc_bankal,'NO_TEST')

    Multi_to_single           (arc_bankal)

    arcpy.Append_management  (arc_modad_c,arc_bankal,'NO_TEST')

    del_Non_Boundery_Line    (arc_bankal,AOI_final,tazar_border)

    Find_stubbern_lines      (arc_bankal,AOI_final,tazar_border)
    Delete_Duplic_Line       (arc_bankal)

    # # # # Points

    bankal_pnts = Layer_Management (point_bankal).Select_By_Location('INTERSECT',AOI_final)

    arcpy.Append_management        (AOI_Point,point_bankal)

    #    #   #    #  #

    print_arcpy_message ("  #   #   #    #  Last Checks  #   #   #   #  ")

    Parcel_data         (parcel_bankal,parcel_bankal_c,parcel_modad_c)

    print_arcpy_message     ("# # # # # # # #     F I N I S H     # # # # # # # # #",1)



def createFolder(dic):
    try:
        if not os.path.exists(dic):
            os.makedirs(dic)
    except OSError:
        print ("Error Create dic")
    return dic

def createGDB(folder,gdb_name):
    
        gdb = folder +'\\' + gdb_name
        if arcpy.Exists(gdb):
                arcpy.Delete_management(gdb)
                arcpy.CreateFileGDB_management(folder, gdb_name)
        else:
                arcpy.CreateFileGDB_management(folder, gdb_name)
        return gdb

def Get_Tazar_Path_Num(path_source_tazar):

    set_jobs,numTazar  = [],[]
    All_ready_run      = []

    for root, dirs, files in os.walk(path_source_tazar):
            for file in files:
                    if root.endswith(".gdb"):
                        if 'SRVToGDB' in root:
                            if root not in All_ready_run:
                                numTazar.append      (root.split('_')[-2])
                                set_jobs.append      (root + '\\' + r'DS_Srv')
                                All_ready_run.append (root)

    return [set_jobs,numTazar]

def Create_Folder_gdb_Source_layers(list_path_Num,folder_out_put):
    
    '''
    [Input]
        list_path_Num = [[tazar_path1,tazar_path2],[tazar_num1,tazar_num2]]
    '''

    tazar_folder      = createFolder (folder_out_put + '\\' + 'EditTazar' + str(list_path_Num[1][i]))
    tazar_gdb         = createGDB    (tazar_folder,'CadasterEdit_Tazar.gdb')
    list_layers       = [['parcels_new','PARCELS_inProc_edit'],['lines_new','LINES_inProc_edit'],['points_new','POINTS_inProc_edit']]
    for layer in list_layers: arcpy.CopyFeatures_management(list_path_Num[0][i] + '\\' + layer[0],tazar_gdb + '\\' + layer[1])

    parcel_tazar,line_tazar,point_tazar = tazar_gdb + '\\' + 'PARCELS_inProc_edit',\
                                        tazar_gdb + '\\' + 'LINES_inProc_edit'  ,tazar_gdb + '\\' + 'POINTS_inProc_edit'

    return tazar_folder,tazar_gdb,parcel_tazar,line_tazar,point_tazar
                        
def Get_Uni_Gush(path_bankal,parcel_tazar):  

    add_uuid = str(uuid.uuid4())[::4]
    lyr_name = 'path_bankal_lyr' + add_uuid
    arcpy.MakeFeatureLayer_management        (path_bankal,lyr_name)
    arcpy.SelectLayerByLocation_management   (lyr_name,'INTERSECT',parcel_tazar,'1 Meters')
    data        = list(set([i[0] for i in arcpy.da.SearchCursor (lyr_name,['GUSH_NUM'])]))
    gush_to_add = ','.join([str(i) for i in data])

    return gush_to_add

def mxd_making(mxd_path,gdb_path,tazar_num,gdb,out_put,parcel_tazar):

    mxd = arcpy.mapping.MapDocument (mxd_path)

    mxd.findAndReplaceWorkspacePaths(gdb_path, gdb)
    df           = arcpy.mapping.ListDataFrames(mxd)[0]
    BORDER_Layer = arcpy.mapping.ListLayers(mxd, "", df)[-1]
    df.extent    = BORDER_Layer.getExtent()

    mxd.saveACopy   (out_put + "\\EditTazar"+tazar_num+".mxd")

    ###############  PSAFAS ###################

    PSAFAS          (parcel_tazar,out_put + "\\EditTazar"+tazar_num+".mxd")

    ##############  cheaks #####################

    Cheaks          (out_put + "\\EditTazar"+tazar_num+".mxd")

    ###########################################

    arcpy.AddMessage("Open MXD Copy")
    os.startfile    (out_put + "\\EditTazar"+tazar_num+".mxd")
    arcpy.RefreshActiveView()



#get folder input
def ask_JOB_folder_input():
    job_dir = tkFileDialog.askdirectory()
    folder_input.set(job_dir)
    folder_input.get()

#return variables to main
def return_variables_to_main():
    input_folder       = folder_input.get()
    print (input_folder)
    return input_folder


def CloseWindow():
    window.destroy()


# create the Tkinter window
window = Tk()

#font
myFont  = font.Font(family = "david", size = 15 , weight = "bold")

# define the size of the window in width(350) and height(350) using the 'geometry' method
window.geometry("350x350")

# In order to prevent the window from getting resize
window.resizable(0, 0)

#define the title of the window
window.title("פסיפס")

#getting all variables in string or int
folder_input = tk.StringVar ()

#properties for selecting input_folder
label1 = Label (window, text=" : בחר תצ''ר")

label1.place(relx=0.95, rely=0.1, anchor=NE)
# text box :
entry1 = Entry (window, textvariable=folder_input, state= 'disabled')
entry1.place (relx=0.6, rely=0.1, anchor=NE)
# browser button:
dirBut_input1 = Button (window, text=' Browse ', command=ask_JOB_folder_input)
dirBut_input1.place (relx=0.20, rely=0.09, anchor=NE)

run = Button (window, text='    יצירת עבודה   ', command=CloseWindow , bg = "light blue", fg = "black")
run.place (relx=0.65, rely=0.82, anchor=NE)
run ['font'] = myFont

window.mainloop ()
path_source_tazar = return_variables_to_main()


# Input
path_bankal       = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_ALL'
path_line         = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_ARC'
path_point        = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_NODE'

# path_source_tazar         = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_Start_proc\data\1036'
# path_source_tazar         = arcpy.GetParameterAsText(0) # folder of tazars to make as AOI

# Out_put
folder_out_put    = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_Start_proc\temp'

# Tamplate
mxd_path_template = r"C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_Start_proc\Tamplate\EditTazar.mxd"
gdb_path_template = r"C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_Start_proc\Tamplate\EditTazar880\CadasterEdit_Tazar.gdb"

list_path_Num     = Get_Tazar_Path_Num(path_source_tazar)

for i in range(len(list_path_Num[0])):

    print (list_path_Num[0][i],list_path_Num[1][i])

    tazar_folder,tazar_gdb,parcel_tazar,line_tazar,point_tazar = Create_Folder_gdb_Source_layers(list_path_Num,folder_out_put)

    gush_to_add = Get_Uni_Gush(path_bankal,parcel_tazar)
    add_uuid    = str(uuid.uuid4())[::4]
    lyr_name    = 'bankal_lyr' + add_uuid

    parcel      = tazar_gdb + '\\' + 'PARCEL_ALL_EDIT'
    line        = tazar_gdb + '\\' + 'PARCEL_ARC_EDIT'
    point       = tazar_gdb + '\\' + 'PARCEL_NODE_EDIT'

    # Create Polygon
    arcpy.MakeFeatureLayer_management  (path_bankal, lyr_name,"\"GUSH_NUM\" in ({})".format(gush_to_add))
    arcpy.CopyFeatures_management      (lyr_name   , parcel)

    # Creating New Line
    arcpy.Dissolve_management (parcel,'in_memory\\Diss')
    for j in [[path_line,line]]:arcpy.Intersect_analysis ([j[0],'in_memory\\Diss'],j[1])
    arcpy.DeleteField_management (line,'FID_Diss')

    # Creating New Point
    arcpy.MakeFeatureLayer_management      (path_point      ,'path_point_lyr')
    arcpy.SelectLayerByLocation_management ('path_point_lyr',"INTERSECT",'in_memory\\Diss')
    arcpy.CopyFeatures_management          ('path_point_lyr', point)

    # Creating Errors Polygon, Line, Points
    for err_fc_name in ["Errors_Line", "Errors_Point", "Errors_Polygon"]: arcpy.Copy_management(gdb_path_template + "\\" + err_fc_name, tazar_gdb + "\\" + err_fc_name)

    # creating copy for source parcels lines and points
    for layer in [parcel,line,point]: arcpy.CopyFeatures_management(layer,layer + '_copy')

    year = os.path.basename(os.path.dirname(list_path_Num[0][i])).split('.')[0].split('_')[-1]
    if year.isdigit():
        if int(year) >= 1900 and int(year) <= 2058:
            arcpy.CalculateField_management(parcel_tazar,'TALAR_NUM' ,list_path_Num[1][i],"VB")
            arcpy.CalculateField_management(parcel_tazar,'TALAR_YEAR',year,"VB")

    # create and opening mxd and run psafas
    mxd_making (mxd_path_template,gdb_path_template,list_path_Num[1][i],tazar_gdb,tazar_folder,parcel_tazar)

