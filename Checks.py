#!/usr/bin/env python
# -*- coding:utf-8-*-
import arcpy
import pythonaddins
import os
import json
import sqlite3
import pandas as pd
import math
import xml.etree.ElementTree as ET
import arcpy, urllib2, urllib

arcpy.env.overwriteOutput = True


def print_arcpy_message(msg, status=1):
    '''
    return a message :

    print_arcpy_message('sample ... text',status = 1)
    >>> [info][08:59] sample...text
    '''
    msg = str (msg)

    if status == 1:
        prefix = '[info]'
        msg = prefix + str (datetime.datetime.now ()) + "  " + msg
        print (msg)
        arcpy.AddMessage (msg)

    if status == 2:
        prefix = '[!warning!]'
        msg = prefix + str (datetime.datetime.now ()) + "  " + msg
        print (msg)
        arcpy.AddWarning (msg)

    if status == 0:
        prefix = '[!!!err!!!]'

        msg = prefix + str (datetime.datetime.now ()) + "  " + msg
        print (msg)
        arcpy.AddWarning (msg)
        msg = prefix + str (datetime.datetime.now ()) + "  " + msg
        print (msg)
        arcpy.AddWarning (msg)

        warning = arcpy.GetMessages (1)
        error = arcpy.GetMessages (2)
        arcpy.AddWarning (warning)
        arcpy.AddWarning (error)

    if status == 3:
        prefix = '[!FINISH!]'
        msg = prefix + str (datetime.datetime.now ()) + " " + msg
        print (msg)
        arcpy.AddWarning (msg)

def Get_Gdb_path():
    MXD = arcpy.mapping.MapDocument (r'CURRENT')
    df = MXD.activeDataFrame
    lyrs = arcpy.mapping.ListLayers(MXD, "חלקות לעריכה", df)
    if lyrs:
        if lyrs[0].isFeatureLayer:
            return lyrs[0].workspacePath

def Get_Mxd_path():
    MXD      = arcpy.mapping.MapDocument (r'CURRENT')
    path_mxd = MXD.filePath
    return   path_mxd

def get_layer_by_fc_name(fc_name):
    mxd = arcpy.mapping.MapDocument('CURRENT')
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
    print "ok"
    if df:
        lyrs = arcpy.mapping.ListLayers(mxd,"*", df)
        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if lyr.datasetName == fc_name:
                    return lyr.dataSource




def add_field(fc,field,Type = 'TEXT'):
    TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
    if not TYPE:
        arcpy.AddField_management (fc, field, Type)
               

def Error_Table(gdb,List_to_add):
    '''
    [INFO]
        get list where: [['Error_Type','Text'],['Error_Type','Text']]
    input:
        List_to_add = [['parcel','22-33-44'],['point','12312_56756']]
    OutPut:
        table with errors
    '''

    full_path = gdb                  + '\\' + 'Error_Table'

    if not arcpy.Exists(full_path):
        arcpy.CreateTable_management(gdb,'Error_Table')

    fields = ['Error_Code','Error_Type','Message']
    for i in fields:
        try:
            add_field(full_path,i,'TEXT')
        except:
            pass

    Error_Type = [i[0] for i in List_to_add]

    with arcpy.da.UpdateCursor(full_path,['Error_Code','Error_Type','Message']) as cursor:
        for row in cursor:
            if row[0] in Error_Type[0]:
                cursor.deleteRow()
    del cursor

    for row in List_to_add:
        insert = arcpy.InsertCursor (full_path)
        in_row               = insert.newRow()
        in_row.Error_Code    = row[0]
        in_row.Error_Type    = row[1].decode('UTF-8')
        in_row.Message       = row[2].decode('UTF-8')
        insert.insertRow   (in_row)

    return full_path

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
                print "no points in the layer"
                        
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

def polygon_to_line(fc,layer_new):
    ws, fc_name = os.path.split (layer_new)
    s_r = arcpy.Describe (fc).spatialReference

    if arcpy.Exists(layer_new):
        arcpy.Delete_management(layer_new)
        
    line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)
        

    Search = arcpy.da.SearchCursor(fc,"SHAPE@"  )
    insert = arcpy.da.InsertCursor(line,"SHAPE@")

    for row in Search:
        points = [arcpy.Point(point.X,point.Y) for shape in row[0] for point in shape if point]
    
        array    = arcpy.Array(points)
        polyline = arcpy.Polyline(array)

        insert.insertRow([polyline])

    arcpy.RepairGeometry_management(layer_new)
    return layer_new

def Feature_to_polygon(path,Out_put):


    path_diss = arcpy.Dissolve_management(path,r'in_memory\Dissolve_temp')


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
                if str(type(pt)) <> "<type 'NoneType'>":
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
                        

def make_polygon_to_point(layer):
    
        wc,name   = os.path.split(layer)
        out_put   = wc + '\\' + name +'_point'
        
        spatial_reference = arcpy.Describe (layer).spatialReference
        ws, fc_name = os.path.split (out_put)

        arcpy.CreateFeatureclass_management (ws, fc_name, 'POINT', spatial_reference=spatial_reference)

        icursor = arcpy.InsertCursor (out_put)
        exists = []
        with arcpy.da.SearchCursor (layer, ['SHAPE@'])as cursor:
                for row in cursor:
                    geom = row[0]
                    for item in geom:
                        for pt in item:
                            if pt:
                                key = str(pt.X) + '-'+str(pt.Y)
                                if key not in exists:
                                    in_row           = icursor.newRow ()
                                    point            = arcpy.Point (pt.X, pt.Y)
                                    ptGeometry       = arcpy.PointGeometry (point)
                                    in_row.Shape     = ptGeometry
                                    exists.append(key)
                                    icursor.insertRow (in_row)
        del cursor
        return out_put


def topology_basic(final,ws):


    no_holes     = False
    no_intersect = False

    gdb           = os.path.dirname(final)
    memory        = r'in_memory'
    Diss          = memory + '\\' + 'dissolve'
    feat_to_poly  = memory + '\\' + 'Feature_to_poly'
    topo_holes    = gdb    + '\\' + 'Topolgy_Check_holes'
    topo_inter    = gdb    + '\\' + 'Topolgy_Check_intersect'
    error_polygon = ws     + '\\' + 'Errors_polygon'

    deleteErrorCode (error_polygon, ["3"])
    deleteErrorCode (error_polygon, ["4"])

    arcpy.Dissolve_management                 (final,Diss)
    Feature_to_polygon                        (Diss,feat_to_poly)
    Delete_polygons                           (feat_to_poly,Diss,topo_holes)

    arcpy.Intersect_analysis([final],topo_inter)

    Calc_field_value_error  (topo_holes,error_polygon,"3",ErrorDictionary["3"])
    Calc_field_value_error  (topo_inter,error_polygon,"4",ErrorDictionary["4"])

    arcpy.Delete_management(Diss)
    arcpy.Delete_management(feat_to_poly)



def deleteErrorCode(layer, list_code):
    add_field(layer,"ERROR_Code")
    with arcpy.da.UpdateCursor(layer,["ERROR_Code"]) as cursor:
        for row in cursor:
            if row[0]:
                if str(row[0]) in list_code:
                    cursor.deleteRow()


def Calc_field_value_error(layer,append_layer,error_code,error_type):
    add_field(layer,"ERROR_TYPE")
    add_field(layer,"ERROR_Code")
    arcpy.CalculateField_management(layer, "ERROR_TYPE", "\""+error_type+"\"", "VB")
    arcpy.CalculateField_management(layer, "ERROR_Code", "\""+error_code+"\"", "VB")
    arcpy.Append_management(layer, append_layer, "NO_TEST")
    arcpy.Delete_management(layer)

def line_Not_on_parcels(ARC_bankal,Parcel_makor, ws):

    #  # cuting layer , to work on less data # #

    # # Check Arc points\ID
    temp_arc       = 'in_memory\\Temp_arc'
    Boundery_touch = 'in_memory\\Boundery_touch'
    temp_err_arc   = 'in_memory\\Err'
    error_line     = ws + "\\Errors_Line"

    deleteErrorCode                        (error_line, ["5"])
    arcpy.MultipartToSinglepart_management (ARC_bankal,temp_arc)

    arcpy.MakeFeatureLayer_management       (ARC_bankal,'ARC_bankal_lyr')
    arcpy.SelectLayerByLocation_management  ('ARC_bankal_lyr',"BOUNDARY_TOUCHES",Parcel_makor,'0.1 Meters',"NEW_SELECTION","INVERT")
    arcpy.Select_analysis                   ('ARC_bankal_lyr',Boundery_touch)

    dicLine = {str(round(pt.X,0)) + '-' + str(round(pt.Y,0)):row.objectid for row in arcpy.SearchCursor(temp_arc) for part in row.shape for pt in part if str(type(pt)) <> 'NoneType'}
    data_p  = [str(round(pts.X,0)) +'-' + str(round(pts.Y,0)) for i in arcpy.SearchCursor(Parcel_makor) for n in i.shape for part in i.shape for pts in part if pts]
    del_lines = list(set([i for n,i in dicLine.items() if n not in data_p]))
    
    print_arcpy_message("errors on arc id: {}".format(del_lines),1)
    if del_lines:
        arcpy.Select_analysis   (temp_arc, temp_err_arc,"\"OBJECTID\" IN ("+str(del_lines)[1:-1]+")")
        arcpy.Append_management (Boundery_touch,temp_err_arc,"NO_TEST")
        Calc_field_value_error  (temp_err_arc,error_line,"5",ErrorDictionary["5"])

        
def point_Not_in_bankal_or_moded(parcel_all_final,ws):


    pnt_New = make_polygon_to_point(parcel_all_final)

    Point         = r'in_memory' + '\\' + 'Point'
    Pnt_to_del    = r'in_memory' + '\\' + 'Point_to_delete'
    error_point   = ws           + '\\' + "Errors_Point"
    pnt_Old       = ws           + '\\' + 'PARCEL_NODE_EDIT_copy'
    node_moded    = ws           + '\\' + 'node_tazar'
    parcel_bankal = ws           + '\\' + 'PARCEL_ALL_EDIT_copy'
    parcel_modad  = ws           + '\\' + 'PARCELS_inProc_edit_copy'

    deleteErrorCode                          (error_point, ["6"])

    bankal_vertex = make_polygon_to_point(parcel_bankal)
    modad_vertex  = make_polygon_to_point(parcel_modad)

    arcpy.MakeFeatureLayer_management        (pnt_New,'pnt_New_lyr')
    arcpy.SelectLayerByLocation_management   ('pnt_New_lyr','INTERSECT',node_moded,'0.1 Meters',"NEW_SELECTION",'INVERT')
    arcpy.Select_analysis                    ('pnt_New_lyr',Point)

    arcpy.MakeFeatureLayer_management        (Point,'Point_lyr')
    arcpy.SelectLayerByLocation_management   ('Point_lyr','INTERSECT',pnt_Old,'0.1 Meters')
    arcpy.SelectLayerByAttribute_management  ('Point_lyr',"SWITCH_SELECTION")
    arcpy.Select_analysis                    ('Point_lyr',Pnt_to_del)

    # del points from bankal that are not in Node bankal
    arcpy.MakeFeatureLayer_management        (Pnt_to_del,'Pnt_to_del_lyr')
    arcpy.SelectLayerByLocation_management   ('Pnt_to_del_lyr','INTERSECT',bankal_vertex,'0.1 Meters',"NEW_SELECTION")
    arcpy.DeleteFeatures_management          ('Pnt_to_del_lyr')

    # del points that on modad tazar but not in his nodes
    arcpy.MakeFeatureLayer_management        (Pnt_to_del,'Pnt_to_del_lyr2')
    arcpy.SelectLayerByLocation_management   ('Pnt_to_del_lyr2','INTERSECT',modad_vertex,'0.1 Meters',"NEW_SELECTION")
    arcpy.DeleteFeatures_management          ('Pnt_to_del_lyr2')

    Calc_field_value_error                   (Pnt_to_del,error_point,"6",ErrorDictionary["6"])
    arcpy.Delete_management                  (bankal_vertex)
    #arcpy.Delete_management                  (modad_vertex)


def missing_Values_in_parcel(Parcel_makor,ws):

    error_polygon = ws + '\\' + 'Errors_Polygon'

    deleteErrorCode (error_polygon, ["1"])
    field_mising = ws + '\\' +'Field_missing'
    #arcpy.CreateFeatureclass_management(p_gdb,'Field_missing',"POLYGON") 

    arcpy.Select_analysis(Parcel_makor,field_mising,"\"PARCEL\" is null or \"GUSH_NUM\" is null or \"GUSH_SUFFIX\" is null or \"LEGAL_AREA\" is null  or \"TALAR_NUMBER\" is null or \"TALAR_YEAR\" is null")
    add_field(field_mising,"ERROR_TYPE",'TEXT')
    add_field(field_mising,"ERROR_Code",'TEXT')

    arcpy.CalculateField_management(field_mising,'ERROR_Code', "\"1\"",'VB')
    arcpy.CalculateField_management(field_mising,'ERROR_Type', "\"missing values\"",'VB')

    Calc_field_value_error  (field_mising,error_polygon,"1",ErrorDictionary["1"])



def Junctions(path_orig,new_point,jun_name = ''):

    if jun_name == '':
        jun_name = 'junction'

    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("""CREATE TABLE pnt_table (
            XY     text,
            ID    INTEGER,
            X     real,
            Y     real
            )""")

    path = path_orig +'_single_part'
    arcpy.MultipartToSinglepart_management(path_orig,path)

    exists_pts = []
    with arcpy.da.SearchCursor(path,['SHAPE@','OID@']) as cur:
        for row in cur:
            geom = row[0]
            for part in geom:
                for pnt in part:
                    if pnt:
                        key = str(round(pnt.X,2)) +"-"+ str(round(pnt.Y,2))
                        if key not in exists_pts:
                            c.execute ("INSERT INTO pnt_table VALUES (""'" + str (round(pnt.X,2)) + "-" + str (round(pnt.Y,2)) + "'""," + str (round(row[1],2))+"," +str(pnt.X) +","+ str(pnt.Y) +")")
                            exists_pts.append(key)
            exists_pts = []

                                
    data1 = [row for row in c.execute ('''SELECT * FROM(SELECT *, COUNT(*) as count FROM pnt_table group by XY) t1 WHERE t1.count > 1''')]

    fc_gdb, fc_name = os.path.split(new_point)

    full_name = arcpy.CreateFeatureclass_management(fc_gdb, fc_name, "POINT")

    all_rows = arcpy.InsertCursor(full_name)
    arcpy.AddField_management(new_point,'polyID','LONG')
    arcpy.AddField_management(new_point,'X','DOUBLE')
    arcpy.AddField_management(new_point,'Y','DOUBLE')
    arcpy.AddField_management(new_point,jun_name,'DOUBLE')
    arcpy.AddField_management(new_point,'XY','TEXT')

    point = arcpy.Point()
    for row in data1:
        in_row = all_rows.newRow()
        in_row.setValue ("polyID", row[1])
        in_row.setValue ("X", row[2])
        in_row.setValue ("Y", row[3])
        in_row.setValue (jun_name, row[4])
        in_row.setValue ("XY", row[0])

        point.X = row[2]
        point.Y = row[3]

        pointGeometry = arcpy.PointGeometry(point)
        in_row.shape = pointGeometry
        all_rows.insertRow (in_row)

    del all_rows
    arcpy.Delete_management(path)
    return new_point

def Check_if_Stubbern_Arc(path,path_ARC,tazar):

    path_lyr     = gdb + '\\' + 'path_lyr_cut'
    path_ARC_lyr = gdb + '\\' + 'path_ARC_cut'

    arcpy.MakeFeatureLayer_management      (path,'path_lyr')
    arcpy.MakeFeatureLayer_management      (path_ARC,'path_ARC_lyr')

    arcpy.SelectLayerByLocation_management('path_lyr',"WITHIN_A_DISTANCE",tazar,'250 Meters',"NEW_SELECTION")
    arcpy.SelectLayerByLocation_management('path_ARC_lyr',"WITHIN_A_DISTANCE",tazar,'250 Meters',"NEW_SELECTION")

    arcpy.Select_analysis('path_lyr',path_lyr)
    arcpy.Select_analysis('path_ARC_lyr',path_ARC_lyr)

    Check_parcel_point = gdb + '\\' + 'Check_parcel_point'
    check_arc_point    = gdb + '\\' + 'check_arc_point'
    check_inter        = r'in_memory\Check_inter'
    problem_check      = gdb + '\\' + 'problem_check'

    Junctions(path_lyr    ,Check_parcel_point,"Jun_parcel")
    Junctions(path_ARC_lyr,check_arc_point,"Jun_Arc")

    arcpy.Intersect_analysis               ([Check_parcel_point,check_arc_point],check_inter)
    arcpy.AddField_management              (check_inter,'Prob',"LONG")
    arcpy.CalculateField_management        (check_inter,'Prob',"[Jun_parcel] - [Jun_Arc]","VB")
    arcpy.MakeFeatureLayer_management      (check_inter,'check_inter_lyr', "\"Prob\" > 0")
    arcpy.SelectLayerByLocation_management ('check_inter_lyr','INTERSECT',tazar,'1 Meters',"NEW_SELECTION","INVERT")
    arcpy.DeleteFeatures_management        ('check_inter_lyr')
    arcpy.Select_analysis                  ('check_inter_lyr',problem_check)

    arcpy.Delete_management(path_lyr)
    arcpy.Delete_management(path_ARC_lyr)
    arcpy.Delete_management(Check_parcel_point)
    arcpy.Delete_management(check_arc_point)

    problems = False
    if int(str(arcpy.GetCount_management(problem_check))) > 0:
        problems = True
    arcpy.Delete_management(problem_check)

    return problems

def PtsToPolygon(pts):
    point = arcpy.Point()
    array = arcpy.Array()
    for point in pts:
        array.add(point)
    array.add(array.getObject(0))

    polygon = arcpy.Polygon(array, arcpy.SpatialReference("Israel TM Grid"))
    return polygon

def Find_Error_Lines(path,ws,gdb):

    path_ARC   = gdb + '\\' + 'PARCEL_ARC_EDIT'
    tazar      = ws + '\\' + 'tazar_border'
    error_line = ws + '\\' + 'Errors_Line'

    deleteErrorCode (error_line, ["7"])

    # temp Layers
    new_point  = gdb + '\\' + 'JunctionsParcels'
    POINT_ARC  = gdb + '\\' + 'Junctions_ARCS'
    temp_inter = r'in_memory\intersect'


    stubbern_arc_bool = Check_if_Stubbern_Arc(path,path_ARC,tazar)
    # Create missing pnts vertex

    if stubbern_arc_bool:
        print_arcpy_message("Tool May have Found stubbern arc, Checking and fixing", status=1)
        prob_misse = gdb + '\\' + 'prob_misse'

        parcels    = Junctions(path,new_point,"Jun_parcel")
        arcs       = Junctions(path_ARC,POINT_ARC,"Jun_Arc")

        arcpy.MakeFeatureLayer_management      (new_point,'new_point_lyr')
        arcpy.SelectLayerByLocation_management ('new_point_lyr','INTERSECT',POINT_ARC,'',"NEW_SELECTION","INVERT")
        arcpy.SelectLayerByLocation_management ('new_point_lyr','WITHIN_A_DISTANCE',tazar,'250 Meters',"REMOVE_FROM_SELECTION","INVERT")
        arcpy.SelectLayerByLocation_management ('new_point_lyr',"COMPLETELY_WITHIN",path_ARC,'',"REMOVE_FROM_SELECTION")
        arcpy.Select_analysis                  ('new_point_lyr',prob_misse)

        Smallest_dis                           (prob_misse)

        ID_geom = {i[0]:i[1] for i in arcpy.da.SearchCursor(prob_misse,["OBJECTID","SHAPE@"])}
        line    = arcpy.CreateFeatureclass_management(gdb,'line_new','POLYLINE')

        fields  = ["KEY","KEY2","dis"]
        for i in fields:
            add_field(line,i)

        Point_cur = arcpy.SearchCursor(prob_misse)
        for row in Point_cur:
            if row.Dis != None:
                cursor = arcpy.InsertCursor(line,['OBJECTID','KEY2','Dis'])
                array = arcpy.Array()
                shape = row.shape
                X1 = shape.centroid.X
                Y1 = shape.centroid.Y
                X2 = ID_geom[int(row.KEY2)].centroid.X
                Y2 = ID_geom[int(row.KEY2)].centroid.Y
                array.add(arcpy.Point(X1,Y1))
                array.add(arcpy.Point(X2,Y2))
                polyline = arcpy.Polyline(array)

                in_row = cursor.newRow()
                in_row.KEY    = str(row.OBJECTID)
                in_row.Dis    = str(row.Dis)
                in_row.KEY2   = str(row.KEY2)
                in_row.shape = polyline
                cursor.insertRow(in_row)

                del cursor

        arcpy.Delete_management(new_point)
        arcpy.Delete_management(POINT_ARC)
        arcpy.Delete_management(prob_misse)

        arcpy.MakeFeatureLayer_management      (line,'Line_del',"\"SHAPE_Length\" > 1")
        arcpy.SelectLayerByLocation_management ('Line_del',"SHARE_A_LINE_SEGMENT_WITH",path,'',"NEW_SELECTION","INVERT")
        arcpy.DeleteFeatures_management        ('Line_del')

        num_found = int(str(arcpy.GetCount_management(line)))
        if num_found > 0:
            Calc_field_value_error (line,error_line,"7",ErrorDictionary["7"])

            print_arcpy_message("Tool Found: {} stubbern arcs".format(str(num_found)), status=2)
        else:
            print_arcpy_message("No stubbern arcs found", status=1)


def Smallest_dis(layer):

    list1   = [[i[0],i[1]] for i in arcpy.da.SearchCursor(layer,    ["SHAPE@","OBJECTID"])]
    all_list = [[row[1],n[0].distanceTo(row[0]),n[1]] for row in arcpy.da.SearchCursor(layer,["SHAPE@","OBJECTID"])for n in list1 if (n[0].distanceTo(row[0]) != 0) and (n[0].distanceTo(row[0]) < 100)]
    df         = pd.DataFrame(all_list,columns= ['KEY','NUM','KEY2'])
    gb         = df.groupby ('KEY').agg({'NUM':'min'}).reset_index()

    list_dis   = gb.values.tolist()
    for i in range(len(list_dis)):
        try:
            if list_dis[i][1] == list_dis[i+1][1]:
                list_dis[i].append(list_dis[i+1][0])
                del list_dis[i+1]
            else:
                pass
        except:
            pass

    for n,i in enumerate(list_dis):
        if len(i) < 3:
            del list_dis[n]
    

    dic1 = {item[0]:item[1:] for item in list_dis}
    add_field(layer,'KEY2','TEXT')
    add_field(layer,'Dis','TEXT')

    print dic1
    found = 0
    not_found = 0
    with arcpy.da.UpdateCursor(layer,['OBJECTID','KEY2','Dis']) as Ucursor:
        for row in Ucursor:
            if dic1.has_key(float(row[0])):
                try:
                    row[2] = dic1[row[0]][0]
                    row[1] = dic1[row[0]][1]
                    Ucursor.updateRow(row)
                    found +=1
                except:
                    pass
            else:
                not_found += 1

    print "Total Match Found: {}".format(str(found))
    print "Total Match missed: {}".format(str(not_found))

def generateCurves(fc):
                desc = arcpy.Describe(fc)
                fc_name = desc.name
                fc_gdb = desc.path
                Curves = fc_gdb + "\\" + fc_name + "_curves_polygon"
                #print "generateCurves("+fc_name+")..."
                arcpy.CreateFeatureclass_management(fc_gdb, fc_name + "_curves_polygon", "POLYGON", "", "", "",fc)
                curveFeatureList = []
                for row in arcpy.SearchCursor(fc):
                                pts = []
                                geom = row.Shape
                                j = json.loads(geom.JSON)
                                if 'curve' in str(j):
                                                #print "You have true curves!"
                                                coords = geom.__geo_interface__['coordinates']
                                                for i in coords:
                                                                if i:
                                                                                for f in i:
                                                                                                if f:
                                                                                                                pts.append(arcpy.Point(f[0], f[1]))
                                if pts:
                                                                polygon = PtsToPolygon(pts)
                                                                diff = polygon.symmetricDifference(geom)
                                                                diff_sp = arcpy.MultipartToSinglepart_management(diff, arcpy.Geometry())
                                                                if len(diff_sp) > 0:
                                                                                                arcpy.Append_management(diff_sp, Curves, "NO_TEST")
                return Curves

def Insert_needed_arc(parcel_bankal,ws,gdb):

    Keshet = generateCurves(parcel_bankal)

    print "Insert_needed_arc"
    tazar_c           = ws  + '\\' + 'PARCELS_inProc_edit_copy'
    arc_bankal        = gdb + '\\' + 'PARCEL_ARC_EDIT'
    arc_bankal_single = ws  + '\\' + 'PARCEL_ARC_EDIT_single' 
    arc_diss          = ws  + '\\' + 'arc__Diss'
    parce_to_line     = ws  + '\\' + 'parcel_to_line'
    error_line        = ws  + '\\' + 'Errors_Line'

    arcpy.MultipartToSinglepart_management (arc_bankal,arc_bankal_single)

    arcpy.MakeFeatureLayer_management      (parcel_bankal,'arc_bankal_single_lyr')
    arcpy.SelectLayerByLocation_management ('arc_bankal_single_lyr',"INTERSECT",tazar_c,'100 Meters')

    polygon_to_line                        ('arc_bankal_single_lyr',parce_to_line)
    arcpy.Dissolve_management              (arc_bankal,arc_diss)
    data = [i.shape for i in arcpy.SearchCursor(arc_diss)][0]
    with arcpy.da.UpdateCursor(parce_to_line,['SHAPE@']) as cursor:
        for row in cursor:
            geom      = row[0]
            new_geom  = geom.difference(data)
            row[0]    = new_geom
            cursor.updateRow(row)

    arcpy.MakeFeatureLayer_management      (parce_to_line,'par_bankal_to_line_lyr')
    arcpy.SelectLayerByLocation_management ('par_bankal_to_line_lyr',"INTERSECT",Keshet,'0.1 Meters')
    arcpy.DeleteFeatures_management        ('par_bankal_to_line_lyr')

    Calc_field_value_error (parce_to_line,error_line,"7",ErrorDictionary["7"])
    #arcpy.Delete_management(arc_diss)
    #arcpy.Delete_management(arc_bankal_single)


def double_arc(ws,gdb):

    Error_line = ws  + '\\' + 'Errors_Line'
    arc        = gdb + '\\' +'PARCEL_ARC_EDIT'
    arc_inter  = ws  + '\\' + 'arc_intersect'

    deleteErrorCode                   (Error_line, ["8"])
    arcpy.Intersect_analysis          ([arc],arc_inter)
    arcpy.MakeFeatureLayer_management (arc_inter,'arc_inter',"\"SHAPE_Length\" < 0.2")
    arcpy.DeleteFeatures_management   ('arc_inter')
    Calc_field_value_error (arc_inter,Error_line,"8",ErrorDictionary["8"])


def double_node(ws,gdb):

    Errors_Point = ws  + '\\' + 'Errors_Point'
    node         = gdb + '\\' +'PARCEL_NODE_EDIT'
    node_inter   = ws  + '\\' + 'node_inter'

    deleteErrorCode (Errors_Point, ["9"])
    arcpy.Intersect_analysis([node],node_inter)
    Calc_field_value_error (node_inter,Errors_Point,"9",ErrorDictionary["9"])


def Parcel_data(path_after,ws,GDB):

    tazar       = ws + '\\' + 'PARCELS_inProc_edit_copy'
    path_before = ws + '\\' + 'PARCEL_ALL_EDIT_copy'


    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
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
        Gush = i.GUSH_SUFFIX
        if not i.GUSH_SUFFIX:
            Gush = 0
        c.execute ("INSERT INTO Table_After VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM) +"-"+ str(Gush)+"',"+str(Gush)+")")

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




def Calc_Area(lyr,ws):
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
        
    cut_bankal    = ws + '\\' + 'cut_bankal'
    tazar_copy    = ws + '\\' + 'PARCELS_inProc_edit_copy'
    error_polygon = ws + '\\' + 'Errors_Polygon'

    deleteErrorCode (error_polygon, ["10"])

    arcpy.MakeFeatureLayer_management      (lyr,'lyr_layer', "\"LEGAL_AREA\" IS NOT NULL")
    arcpy.SelectLayerByLocation_management ('lyr_layer',"INTERSECT",tazar_copy,'100 Meters')
    arcpy.Select_analysis                  ('lyr_layer',cut_bankal)

        
    fields = [["GAP", "DOUBLE"],["delta", "DOUBLE"],["Check", "TEXT"]]
    for i in fields:
        try:
            print i[0]
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

    arcpy.MakeFeatureLayer_management  (cut_bankal,'cut_bankal_del',"\"Check\" = 'Ok'")
    arcpy.DeleteFeatures_management    ('cut_bankal_del')

    Calc_field_value_error (cut_bankal,error_polygon,"10",ErrorDictionary["10"])


def Check_accurancy_pracel(fc,ws):

    Error_Polygon = ws + '\\' + 'Errors_Polygon'

    deleteErrorCode (Error_Polygon, ["11"])

    list_fields = ["GUSH_NUM","GUSH_SUFFIX","PARCEL","LEGAL_AREA","PNUMTYPE","TALAR_NUMBER","TALAR_YEAR","SYS_DATE","KEY"]

    add_field(fc,'KEY',Type = 'TEXT')
    with arcpy.da.UpdateCursor(fc,list_fields) as cursor:
        for row in cursor:
            row[-1] = str(row[0]) +'-' + str(row[1])+ '-' + str(row[2])
            cursor.updateRow(row)

    x = [row[0] for row in arcpy.da.SearchCursor (fc,["KEY"])]

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


def Node_not_on_parcel(parcel_all,ws,gdb):

    node_final = gdb + '\\' + 'PARCEL_NODE_EDIT'
    node_error = ws + '\\' + 'Errors_Point'
    Error_temp = ws + '\\' + 'Error_temp'

    deleteErrorCode (node_error, ["12"])

    arcpy.MakeFeatureLayer_management      (node_final,'node_final_lyr')
    arcpy.SelectLayerByLocation_management ('node_final_lyr',"BOUNDARY_TOUCHES",parcel_all,'0.01 Meters',"","INVERT")
    arcpy.Select_analysis                  ('node_final_lyr',Error_temp)

    Calc_field_value_error (Error_temp,node_error,"12",ErrorDictionary["12"])



def Fins_not_exists_parcel_ot_Gush(parcel_all_final,ws):

    Tazar         = ws + '\\' + 'PARCELS_inProc_edit_copy'
    parcel_before = ws + '\\' + 'PARCEL_ALL_EDIT_copy'
    parcel_Error  = ws + '\\' + 'Errors_Polygon'

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
                in_row.Shape      = row[2]
                in_row.ERROR_Code = '13'
                in_row.ERROR_TYPE = ErrorDictionary["13"]
                up_rows.insertRow(in_row)
    del cursor


def get_no_node_vertex(Paecel_all_final,gdb,ws):

            tazar_border       = ws  + '\\' + 'tazar_border'
            node               = gdb + '\\' + 'POINTS_inProc_edit'
            old_node           = ws + '\\' + 'PARCEL_NODE_EDIT_copy'
            parcel_all         = ws  + '\\' + 'cut_parcel_copy'
            Possible_Error_pts = ws  + "\\" + "Possible_Error_p"

            point_Error  = ws + '\\' + 'Errors_Point'
            
            deleteErrorCode (point_Error, ["2"])

            arcpy.MakeFeatureLayer_management      (Paecel_all_final,'Paecel_all_final_lyr')
            arcpy.SelectLayerByLocation_management ('Paecel_all_final_lyr','INTERSECT',tazar_border,'5 Meters')
            arcpy.Select_analysis                  ('Paecel_all_final_lyr',parcel_all)

            point = make_polygon_to_point          (parcel_all)

            print_arcpy_message("START Func: get no node vertex",1)
            
            arcpy.MakeFeatureLayer_management     (point,"points_lyr")
            arcpy.SelectLayerByLocation_management("points_lyr","BOUNDARY_TOUCHES",tazar_border,0.003)
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",node,0.003,"REMOVE_FROM_SELECTION")
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",old_node,0.003,"REMOVE_FROM_SELECTION")
            arcpy.Select_analysis("points_lyr",Possible_Error_pts)

            arcpy.Delete_management(parcel_all)
            arcpy.Delete_management(point)

            Calc_field_value_error (Possible_Error_pts,point_Error,"2",ErrorDictionary["2"])



def Call_Service(service_code_sum, gdb):

    #gdb = Get_Gdb_path()
    mxd = Get_Mxd_path()

    url = r"http://etm:804/CadasterEditWS/CadsterEditJobs.asmx/CheckTalarErrors"

    desc_list = dict([i.split(":") for i in ((arcpy.mapping.ListDataFrames((arcpy.mapping.MapDocument(r'CURRENT')), "*")[0]).description.split(";\r\n")) if i.split(":")[0] <> u''])
    desc_list['gdbEdited'] = gdb
    values = {'gdbEdited':str(desc_list['gdbEdited']),
            'EditId':str(desc_list['EditId']),
            'UserName':str(desc_list['UserName']),
            'IsProd':str(desc_list['IsProd']),
            'editProcess':str(desc_list['editProcess']),
            'chkCode': str(service_code_sum)          
            }
    values_str = 'gdbEdited=' +  str(desc_list['gdbEdited']) + '&' + 'EditId=' +  str(desc_list['EditId']) + '&' + 'UserName=' +  str(desc_list['UserName']) + '&' + 'IsProd=' +  str(desc_list['IsProd']) + '&' + 'editProcess=' +  str(desc_list['editProcess']) + '&' + 'chkCode=' +  str(service_code_sum)
    data = urllib.urlencode(values)

    print_arcpy_message(url + "?" + values_str)
    #req = urllib2.Request(url + "?" + data, None, values)
    #print req
    response = urllib2.urlopen(url + "?" + values_str)
    the_page = response.read()
    print_arcpy_message(the_page, 1)
    return the_page

                

#            #        #      #       menu        #      #       #          #  


ErrorDictionary = {"1": "ערכים חסרים בשדות של שכבת חלקות",
                    "2": "נקודת מודד חסרה",
                    "3": "בדיקת טופולוגיה - חורים",
                    "4": "בדיקת טופולוגיה - חפיפות",
                    "5": "אי התאמה של חזית עם גבול חלקה",
                    "6": "נקודה חדשה שנוצרה",
                    "7": "חזית חסרה",
                    "8": "חזית כפולה",
                    "9": "נקודת גבול כפולה",
                    "10":"שטח חלקה לא עומד בתקן",
                    "11":"מספר חלקה כפול",
                    "12":"אי הצמדה של נקודת גבול לגבולות החלקה",
                    "13":"מספר חלקה או גוש לא תקין"}

ErrorDictionary_services = {"1" : "בדיקת חלקות",
                    "2" : "בדיקת גושים",
                    "4": "בדיקת ערכים",
                    "8": "בדיקת חלקות מבוטלות"}

            
# # # # # # Geometry # # # # # 

Empty                            =  arcpy.GetParameterAsText(0)

topology_basic_cbx               =  arcpy.GetParameterAsText(1)
line_Not_on_parcels_cbx          =  arcpy.GetParameterAsText(2)
point_Not_in_bankal_or_moded_cbx =  arcpy.GetParameterAsText(3)
Missing_arc_cbx                  =  arcpy.GetParameterAsText(4)
Node_not_on_parcel_cbx           =  arcpy.GetParameterAsText(5)
get_no_node_vertex_cbx           =  arcpy.GetParameterAsText(6)
double_arc_cbx                   =  arcpy.GetParameterAsText(7)
double_node_cbx                  =  arcpy.GetParameterAsText(8)  

# # # # # # Table # # # # #

Empty2                           =  arcpy.GetParameterAsText(9)

parcel_out_and_no_parcel_in_cbx  =  arcpy.GetParameterAsText(10)
Check_area_in_tazar_cbx          =  arcpy.GetParameterAsText(11)
Gush_parcel_doubled_cbx          =  arcpy.GetParameterAsText(12)
missing_Values_in_parcel_cbx     =  arcpy.GetParameterAsText(13)
Parcel_gush_number_not_vaild_cbx =  arcpy.GetParameterAsText(14)

select_all_cbx                   = arcpy.GetParameterAsText(15)

# # # # # # Services # # # # #

Empty3                           =  arcpy.GetParameterAsText(16)

parcel_cbx                       =  arcpy.GetParameterAsText(17)
gush_cbx                         =  arcpy.GetParameterAsText(18)
value_cbx                        =  arcpy.GetParameterAsText(19)
cancelparcel_cbx                 =  arcpy.GetParameterAsText(20)

## start process...


scriptPath = os.path.abspath(__file__)
Scripts    = os.path.dirname(scriptPath)
ToolShare  = os.path.dirname(Scripts)
Scratch    = ToolShare + "\\Scratch"
ToolData   = ToolShare + "\\ToolData"


lyr_dataSource = get_layer_by_fc_name('Parcel_all_edit')
lyr_dataSource_lines = get_layer_by_fc_name('Parcel_arc_edit')
if lyr_dataSource:

    mxd           = arcpy.mapping.MapDocument   ('CURRENT')
    df            = arcpy.mapping.ListDataFrames  (mxd)[0]
    gdb           = os.path.dirname  (lyr_dataSource)
    folder_source = os.path.dirname  (gdb)
    name          = os.path.basename (folder_source)
    tazar_num     = ''.join([i for i in name if i.isdigit()])
    ws = Scratch + '\\' + 'Tazar_{}.gdb'.format(tazar_num)
    arcpy.AddMessage(ws)

    arcpy.Select_analysis(lyr_dataSource, ws + "\\PARCEL_ALL_FINAL")
    parcel_all_final = ws + "\\PARCEL_ALL_FINAL"
    
    if select_all_cbx == 'true':
        topology_basic_cbx               = 'true'
        line_Not_on_parcels_cbx          = 'true'
        point_Not_in_bankal_or_moded_cbx = 'true'
        Missing_arc_cbx                  = 'true'
        Node_not_on_parcel_cbx           = 'true'
        get_no_node_vertex_cbx           = 'true'
        double_arc_cbx                   = 'true'
        double_node_cbx                  = 'true'
        parcel_out_and_no_parcel_in_cbx  = 'true'
        Check_area_in_tazar_cbx          = 'true'
        Gush_parcel_doubled_cbx          = 'true'
        missing_Values_in_parcel_cbx     = 'true'
        Parcel_gush_number_not_vaild_cbx = 'true'

    Empty == ''

    #cbx1
    if topology_basic_cbx == 'true':
        print_arcpy_message(ErrorDictionary["3"],1)
        print_arcpy_message(ErrorDictionary["4"],1)
        topology_basic(parcel_all_final,ws)


    #cbx2
    if line_Not_on_parcels_cbx == 'true':
        print_arcpy_message(ErrorDictionary["5"],1)
        line_Not_on_parcels(gdb + '\\' 'PARCEL_ARC_EDIT' , parcel_all_final, ws)

    #cbx3
    if point_Not_in_bankal_or_moded_cbx == 'true':
        print_arcpy_message(ErrorDictionary["6"],1)
        point_Not_in_bankal_or_moded (parcel_all_final,ws)
    

    #cbx4
    if Missing_arc_cbx == 'true':
        print_arcpy_message(ErrorDictionary["7"],1)
        Insert_needed_arc (parcel_all_final,ws,gdb)
        Find_Error_Lines  (parcel_all_final,ws,gdb)

    #cbx5
    if Node_not_on_parcel_cbx == 'true':
        print_arcpy_message(ErrorDictionary["12"],1)
        Node_not_on_parcel(parcel_all_final,ws,gdb)
        pass

    #cbx6
    if get_no_node_vertex_cbx == 'true':
        print_arcpy_message(ErrorDictionary["2"],1)
        get_no_node_vertex(parcel_all_final,gdb,ws)

    #cbx6
    if double_arc_cbx == 'true':
        print_arcpy_message(ErrorDictionary["8"],1)
        double_arc(ws,gdb)
        pass

    #cbx7
    if double_node_cbx == 'true':
        print_arcpy_message(ErrorDictionary["9"],1)
        double_node(ws,gdb)
        pass

    #cbx8
    Empty2 == ''

    #cbx9
    if parcel_out_and_no_parcel_in_cbx == 'true':
        print_arcpy_message('חלקות יוצאות ונכנסות',1)
        Parcel_data(parcel_all_final,ws,gdb)
        pass

    #cbx10
    if Check_area_in_tazar_cbx == 'true':
        print_arcpy_message(ErrorDictionary["10"],1)        
        Calc_Area(parcel_all_final,ws)
        pass

    #cbx11
    if Gush_parcel_doubled_cbx == 'true':
        print_arcpy_message(ErrorDictionary["11"],1)
        Check_accurancy_pracel(parcel_all_final,ws)
        pass

    #cbx12
    if missing_Values_in_parcel_cbx == 'true':
        print_arcpy_message(ErrorDictionary["1"],1)
        missing_Values_in_parcel(parcel_all_final,ws)

    #cbx13
    if Parcel_gush_number_not_vaild_cbx == 'true':
        print_arcpy_message(ErrorDictionary["13"],1)
        Fins_not_exists_parcel_ot_Gush(parcel_all_final,ws)
        pass
    
    service_code_sum = 0
    #cbx17
    if parcel_cbx == 'true':
        print_arcpy_message(ErrorDictionary_services["1"],1)
        service_code_sum = service_code_sum + 1

    #cbx18
    if gush_cbx == 'true':
        print_arcpy_message(ErrorDictionary_services["2"],1)
        service_code_sum = service_code_sum + 2

    #cbx19
    if value_cbx == 'true':
        print_arcpy_message(ErrorDictionary_services["4"],1)
        service_code_sum = service_code_sum + 4

    #cbx20
    if cancelparcel_cbx == 'true':
        print_arcpy_message(ErrorDictionary_services["8"],1)
        service_code_sum = service_code_sum + 8
    
    print_arcpy_message("run service with code " + str(service_code_sum),1)

    if service_code_sum > 0:
        Call_Service(service_code_sum, gdb)





