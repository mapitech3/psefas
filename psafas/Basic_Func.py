# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # Basic Func # # # # # # # # # # # # # # # 

from Layer_Class import Layer_Management
from Layer_Class import Split_List_by_value
from Layer_Class import Feature_to_polygon

import json
import arcpy
import os,math
import pandas as pd
import datetime
import numpy as np


arcpy.env.overwriteOutput = True


"""
print_arcpy_message
generateCurves
Feature_to_polygon
del_line_Not_on_parcels
Polygon_To_Line
Polygon_To_Line_holes
Delete_polygons
topology
Get_Polygon_vertx
CreateWorkingGDB
getLayerPath
PtsToPolygon
collinearity
Fix_curves
VerticesToTable2
fix_tolerance
dis
Split_Line_By_Vertex
Multi_to_single
delete_parts_if_inside
Spatial_Connection_To_LabelPoint
Average
Delete_By_length
Delete_Duplic_Line
Layer_To_Edge_list
fix_tolerance_line
del_Non_Boundery_Line
Delete_By_length
"""

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


def del_line_Not_on_parcels(ARC_bankal,Parcel_makor):

    #  # cuting layer , to work on less data # #

    # # Check Arc points\ID

    dicLine = [[str(round(pt.X,1)) + '-' + str(round(pt.Y,1)),row.objectid] for row in arcpy.SearchCursor(ARC_bankal) for part in row.shape for pt in part if pt]
    data_p  = [str(round(pts.X,1)) +'-' + str(round(pts.Y,1)) for i in arcpy.SearchCursor(Parcel_makor) for n in i.shape for part in i.shape for pts in part if pts]
    del_line = list(set([i[1] for i in dicLine if i[0] not in data_p]))
    
    if del_line:
        arcpy.MakeFeatureLayer_management      (ARC_bankal,'ARC_bankal_lyr')
        arcpy.SelectLayerByAttribute_management('ARC_bankal_lyr',"NEW_SELECTION","\"OBJECTID\" IN ("+str(del_line)[1:-1]+")")
        arcpy.DeleteFeatures_management        ('ARC_bankal_lyr')

  


def Delete_polygons(fc,del_layer,Out_put = ''):

    '''
    fc        = השכבה הראשית- שכבה ממנה רוצים למחוק
    del_layer = שכבה שתמחק את השכבה הראשית
    Out_put   = שכבת הפלט, במידה ולא תוכנס שכבה, ימחק מהשכבה הראשית
    '''
    
    desc = arcpy.Describe(fc)

    if not Out_put == '':
        fc = arcpy.CopyFeatures_management(fc,Out_put)
    else:
        Out_put = fc
    
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
                else:
                    pass
            del Ucursor
        del del_layer_temp
                        
    else:
        count_me = int(str(arcpy.GetCount_management(del_layer)))
        if count_me > 0:
            temp = 'in_memory' +'\\'+'_temp'
            arcpy.Dissolve_management(del_layer,temp)
            if int(str(arcpy.GetCount_management(temp))) > 0:
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


def topology(final):
        
    gdb                 = os.path.dirname(final)
    Dissolve_temp       = r'in_memory' + '\\'+ 'dissolve_me'
    Feature_to_poly     = r'in_memory' + '\\'+'Feature_to_poly'
    Topolgy_Check_holes = gdb + '\\'+'Topolgy_Check_holes'
    Topolgy__intersect  = gdb + '\\'+'Topolgy_Check_intersect'

    arcpy.Dissolve_management                 (final,Dissolve_temp)
    Feature_to_polygon                        (Dissolve_temp,Feature_to_poly)
    Delete_polygons                           (Feature_to_poly,Dissolve_temp,Topolgy_Check_holes)
    count = int(str(arcpy.GetCount_management (Topolgy_Check_holes)))
    if count == 0:
        arcpy.Delete_management(Topolgy_Check_holes)
        Topolgy_Check_holes = None

    over_lap       = arcpy.Intersect_analysis([final],Topolgy__intersect)
    over_lap_count = int(str(arcpy.GetCount_management (over_lap)))
    if over_lap_count == 0:
        arcpy.Delete_management(Topolgy__intersect)
        Topolgy__intersect = None

    arcpy.Delete_management(Dissolve_temp)
    del Dissolve_temp
    return Topolgy_Check_holes,Topolgy__intersect




def Fix_Pnt_Tolerance(AOI_final,AOI_Point):

    pnt_save = {str(round(pt.X,1)) + '-' + str(round(pt.Y,1)):[pt.X,pt.Y] for row in arcpy.SearchCursor(AOI_final) for part in row.shape for pt in part if pt}

    with arcpy.da.UpdateCursor(AOI_Point,['SHAPE@']) as cursor:
        for row in cursor:
            X_pt = str(round(row[0].centroid.X,1))
            Y_pt = str(round(row[0].centroid.Y,1))
            key = X_pt + '-' + Y_pt
            if pnt_save.has_key(key):
                point = arcpy.Point(pnt_save[key][0],pnt_save[key][1])
                row[0] = point
                cursor.updateRow(row)


def getLayerPath(fc,CURRENT = 'CURRENT'):

    '''
    [INFO]
        מקבל שכבה מהמשתמש, מחזיר את בסיס הנתונים בו הוא נמצא
    '''

    MXD  = arcpy.mapping.MapDocument (CURRENT)
    df   = MXD.activeDataFrame
    lyrs = arcpy.mapping.ListLayers(MXD, fc.split("\\")[-1], df)
    if lyrs:
        if lyrs[0].isFeatureLayer:
            return os.path.dirname(lyrs[0].dataSource)
    else:
        return os.path.dirname(fc)


def CreateWorkingGDB(gdb,Folder,copy,fc_name,CURRENT):


    '''
        [INFO]
            Create GDB and copy all the layers from the source GDB to the new GDB, also except layer from mxd
        INPUT - GDB     which all his layer will be copyed
              - Folder  New GDB will be created, with copyed layers
              - Names of the layer that you need to copy, in list
              - fc_name , name of 1 layer from the mxd, in case layer from MXD will enter the tool

        RETURN - NEW gdb with all the "workimg on" layers
    '''

    def get_fc_from_mxd(fc_name,CURRENT):
    #CURRENT
        mxd = arcpy.mapping.MapDocument(CURRENT)
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        lyrs = arcpy.mapping.ListLayers(mxd, '*', df)
        fc = None
        for lyr in lyrs:
                if lyr.isFeatureLayer:
                        if os.path.basename(lyr.dataSource) == fc_name:
                                fc = lyr.dataSource
        return fc
    
    folder_source = os.path.dirname  (gdb)
    name          = os.path.basename (folder_source)
    tazar_num     = ''.join([i for i in name if i.isdigit()])
    ws = Folder + '\\' + 'Tazar_{}.gdb'.format(tazar_num)
    if arcpy.Exists(ws):
                    arcpy.Delete_management(ws)

    print ('Tazar_{}.gdb'.format(tazar_num))
    arcpy.CreateFileGDB_management(Folder,'Tazar_{}.gdb'.format(tazar_num))
    
    return_list = []
    for fc in copy:
        try:
            arcpy.CopyFeatures_management    (gdb + '\\' + fc ,ws + '\\' + fc + '_copy')
        except:
            copy_me = get_fc_from_mxd        (fc_name,CURRENT)
            gdb     = os.path.dirname(copy_me)
            arcpy.CopyFeatures_management    (gdb + '\\' + fc ,ws + '\\' + fc + '_copy')
        return_list.append(ws + '\\' + fc + '_copy')

    return ws


def generateCurves(fc):
    desc    = arcpy.Describe(fc)
    fc_name = desc.name
    fc_gdb  = desc.path
    Curves  = fc_gdb + "\\" + fc_name + "_curves_polygon"
    #print "generateCurves("+fc_name+")..."
    arcpy.CreateFeatureclass_management(fc_gdb, fc_name + "_curves_polygon", "POLYGON", "", "", "",fc)
    curveFeatureList = []
    for row in arcpy.SearchCursor(fc):
        pts = []
        geom = row.Shape
        j = json.loads(geom.JSON)
        if 'curve' in str(j):
            coords = geom.__geo_interface__['coordinates']

            for i in coords:
                if i:
                    for f in i:
                        if f:
                            pts.append(arcpy.Point(f[0],f[1]))
                        else:
                            pts.append(None)

        poly    = Split_List_by_value(pts,None,True) 

        if pts:
            array        = arcpy.Array(None)
            polygon = arcpy.Polygon(array, arcpy.SpatialReference("Israel TM Grid"))
            if len(poly) > 1:
                for part in poly:
                    poly_part = PtsToPolygon(part)
                    polygon   = polygon.symmetricDifference(poly_part)
            else:
                polygon = PtsToPolygon(poly[0])

            diff    = polygon.symmetricDifference(geom)
            diff_sp = arcpy.MultipartToSinglepart_management(diff, arcpy.Geometry())
            if len(diff_sp) > 0:
                arcpy.Append_management(diff_sp, Curves, "NO_TEST")
    return Curves


def dis(x1,x2,y1,y2):
    dist = math.sqrt(((x1-x2)**2) + ((y1-y2)**2))
    return dist

def PtsToPolygon1(coord_list):
    parts = arcpy.Array()
    rings = arcpy.Array()
    ring = arcpy.Array()
    for part in coord_list:
        for pnt in part:
            if pnt:
                ring.add(arcpy.Point(pnt[0], pnt[1]))
            else:
                # null point - we are at the start of a new ring
                rings.add(ring)
                ring.removeAll()
        # we have our last ring, add it
        rings.add(ring)
        ring.removeAll()
        # if we only have one ring: remove nesting
        if len(rings) == 1:
            rings = rings.getObject(0)
        parts.add(rings)
        rings.removeAll()
    # if single-part (only one part) remove nesting
    if len(parts) == 1:
        parts = parts.getObject(0)
    return arcpy.Polygon(parts)

def PtsToPolygon(pts):
    point = arcpy.Point()
    array = arcpy.Array()
    for point in pts:
        array.add(point)
    array.add(array.getObject(0))

    polygon = arcpy.Polygon(array, arcpy.SpatialReference("Israel TM Grid"))
    return polygon


def Delete_layers_after_use(layers):
    for i in layers:
        try:
                arcpy.Delete_management (i)
        except:
            pass 


def collinearity(p1, p2, p3):
    """return True if 3 points are collinear.
    tolerance value will decide whether lines are collinear; may need
    to adjust it based on the XY tolerance value used for feature class"""
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]
    res = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
    return abs(res)  



def Polygon_To_Line_holes(Polygon,New_Line):

    Multi_to_single(Polygon)

    ws, fc_name = os.path.split (New_Line)
    s_r = arcpy.Describe (Polygon).spatialReference
    arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)

    ins_cursor = arcpy.da.InsertCursor (New_Line, ["SHAPE@"])

    New_Lines = []
    with arcpy.da.SearchCursor(Polygon,['SHAPE@','OBJECTID']) as cursor:
        for row in cursor:
            geom = row[0]
            array_temp = arcpy.Array() 
            conti      = True
            for part in geom:
                for pt in part:
                    if pt:
                        if conti:
                            array_temp.append(pt)
                        else:
                            New_Lines.append(arcpy.Point(pt.X,pt.Y))
                    else:
                        New_Lines.append(None)
                        conti = False



            polyline = arcpy.Polyline (array_temp,s_r)
            ins_cursor.insertRow ([polyline])

    del cursor

    # Insert rings in polygon, and make them lines

    InsertCursor = arcpy.InsertCursor(New_Line)
    insert       = InsertCursor.newRow()

    New_Lines = Split_List_by_value(New_Lines,None,True)

    for row in New_Lines:
        if row:
            row            = arcpy.Array(row)
            line           = arcpy.Polyline(row)
            insert.shape   = line
            InsertCursor.insertRow  (insert)

    arcpy.RepairGeometry_management(New_Line)


def Polygon_To_Line(fc,layer_new):
    
    ws, fc_name = os.path.split (layer_new)
    s_r = arcpy.Describe (fc).spatialReference

    if arcpy.Exists(layer_new):
        arcpy.Delete_management(layer_new)
        
    line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)

    insert = arcpy.da.InsertCursor(line,"SHAPE@")

    Search = arcpy.da.SearchCursor(fc,"SHAPE@"  )
    Get_Line_list = []
    pid = 0
    for row in Search:
        for part in row[0]:
            for pt in part:
                if pt:
                    Get_Line_list.append([pid,pt.X,pt.Y])
                else:
                    pass
        pid +=1

    for i in range(pid):
        points   = [arcpy.Point(n[1],n[2]) for n in Get_Line_list if n[0] == i]
        array    = arcpy.Array(points)
        polyline = arcpy.Polyline(array)
        insert.insertRow([polyline])

    arcpy.RepairGeometry_management(layer_new)

def Fix_curves(fc,tazar_border,curves):

        print_arcpy_message("START Func: Fix curves",1)

        name       = fc
        gdb        = os.path.dirname(fc)
        curves_cut = gdb + '\\' + 'curves_cut'
        fc2        = gdb + '\\' + 'temp'
        
        Delete_polygons(curves,tazar_border,curves_cut)
        Delete_polygons(fc,curves_cut,fc2)      
        arcpy.MakeFeatureLayer_management(fc2,'ARCEL_ALL_FINAL_lyr')
        
        list_Upd = []
        cursor = arcpy.SearchCursor(curves_cut)
        for i in cursor:
                arcpy.SelectLayerByLocation_management('ARCEL_ALL_FINAL_lyr',"SHARE_A_LINE_SEGMENT_WITH",i.shape)
                layer_ID = [row.OBJECTID for row in arcpy.SearchCursor('ARCEL_ALL_FINAL_lyr',['OBJECTID','PARCEL_ID']) if row.PARCEL_ID is not None]
                if layer_ID:
                    list_Upd.append([layer_ID[0],i.shape])


        for i in list_Upd:
                upd_cursor = arcpy.UpdateCursor(fc2)
                for up_row in upd_cursor:
                        geom = up_row.shape
                        id   = up_row.OBJECTID
                        if str(id) == str(i[0]):
                                new_geom     = geom.union (i[1])
                                up_row.shape = new_geom
                                upd_cursor.updateRow(up_row)  


        arcpy.Delete_management (fc)
        arcpy.Delete_management (curves_cut)
        arcpy.Rename_management (fc2, name)
        

def VerticesToTable2(fc, table,c):
    #read fc vertices
    xys = []
    fc_rows = [[row.OBJECTID, row.SHAPE] for row in arcpy.SearchCursor(fc)]
    for item in fc_rows:
        fc_oid = item[0]
        geometry = item[1]
        fc_part_num = 1
        for fc_part in geometry:
            fc_pnt_num = 1
            xys_for_linerity = []
            for fc_pnt in fc_part:
                if fc_pnt:
                    x = fc_pnt.X
                    y = fc_pnt.Y
                    c.execute("INSERT INTO "+table+" VALUES ("+str(fc_pnt_num) + ","
                              +str(x) + ","
                              +str(y) + ","
                              +"'"+str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y)))+"',"
                              +str(fc_part_num) + ","
                              +str(fc_oid) +", 0, 0)")
                    xys.append(str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y))))
                    xys_for_linerity.append([x,y])
                    fc_pnt_num = fc_pnt_num + 1
            counter = 0
            for xy_l in xys_for_linerity:
                if counter > 0 and counter < len(xys_for_linerity) - 1:
                    xy1 = xys_for_linerity[counter  - 1]
                    xy2 = xy_l
                    xy3 = xys_for_linerity[counter  + 1]
                    linearity = collinearity(xy1, xy2, xy3)
                    c.execute("UPDATE "+table+" SET linearity = "+str(linearity) + " WHERE x = "+str(xy_l[0])+" AND y = "+str(xy_l[1]))
                if counter == 0:
                    xy1 = xys_for_linerity[-1]
                    xy2 = xy_l
                    xy3 = xys_for_linerity[1]
                    linearity = collinearity(xy1, xy2, xy3)
                    c.execute("UPDATE "+table+" SET linearity = "+str(linearity) + " WHERE x = "+str(xy_l[0])+" AND y = "+str(xy_l[1]))
                if counter == len(xys_for_linerity) - 1:
                    xy1 = xys_for_linerity[-2]
                    xy2 = xy_l
                    xy3 = xys_for_linerity[0]
                    linearity = collinearity(xy1, xy2, xy3)
                    c.execute("UPDATE "+table+" SET linearity = "+str(linearity) + " WHERE x = "+str(xy_l[0])+" AND y = "+str(xy_l[1]))
                counter = counter + 1
                              
    for xy in xys:
        xy_count = len([i for i in xys if i == xy])
        c.execute("UPDATE "+table+" SET junction = "+str(xy_count) + " WHERE xy = '"+xy+"'")




def fix_tolerance(layer_path,border):
    
    gdb           = os.path.dirname(border)
    border_diss   = gdb + '\\' + 'border_diss'
    holes_to_keep = gdb + '\\' + 'holes_to_keep'
    arcpy.Dissolve_management(border,border_diss)

    dic_point = {str([float('{0:.0f}'.format(pt.X)),float('{0:.0f}'.format(pt.Y))]):[pt.X,pt.Y] for i in arcpy.SearchCursor(border_diss) for part in i.Shape for pt in part if pt}

    arcpy.Delete_management (gdb + '\\' + 'border_diss')

    lyr_management = Layer_Management    (layer_path)
    lyr_management.Multi_to_single       ()
    lyr_management.Fill_Holes_in_Polygon (holes_to_keep,False,True)

    Ucursor = arcpy.UpdateCursor(layer_path)
    for i in Ucursor:
        ring = arcpy.Array()
        geom = i.Shape
        j = json.loads(geom.JSON)
        if 'curve' not in str(j):
            for part in geom:
                counter = 0
                for pt in part:
                    if pt:
                        if counter == 0:
                            first_pt = pt
                        key = str([float('{0:.0f}'.format(pt.X)),float('{0:.0f}'.format(pt.Y))])
                        if dic_point.has_key(key):
                            ring.add(arcpy.Point(dic_point[key][0],dic_point[key][1]))
                        else:
                            ring.add(pt)
                        counter = counter + 1
                    else:
                        ring.add(first_pt)
                        ring.add(None)
                        counter = 0

            polygon = arcpy.Polygon(ring)
            i.Shape = polygon
            Ucursor.updateRow(i) 
        else:
            pass

    
    Delete_polygons(layer_path,holes_to_keep)


def Spatial_Connection_To_LabelPoint(layer,ref,field_to_pass = []):

    '''
    [INFO] - חיבור מרחבי בין יישויות
    INPUT:
    1) layer         - השכבה אליה יכנסו הערכים לשדות חדשים
    2) ref           - השכבה ממנה ישלפו הערכים והשדות
    3) field_to_pass - שדות אותם רוצים להעביר, במידה ולא ינתן, יעביר את כל השדות
    OUTPUT:
    1) layer         - אותה שכבה עם השדות החדשים
    '''

    if field_to_pass == []:
        field_to_pass  = [i for i in Layer_Management(ref).fields() if i != 'SHAPE']

    # שכבת עזר 
    temp_intersect = 'in_memory\intersectAOI3'

    # שכבה אליה יכנסו השדות החדשות
    layer       = Layer_Management(layer)
    # המספר מזהה של השכבה
    OID         = layer.oid

    # יצירת נקודות במרכז היישות, 
    LabelPoint  = layer.Get_Label_Point_As_Point()
    LabelPoint  = Layer_Management(LabelPoint)

    # שם השכבה הראשית אצל שכבת הנקודות, הקשר בין השכבות
    ID_Field    = 'FID_'+LabelPoint.name # OID after intersect

    # חיבור בין שכבת הנקודות לשכבה חדשה
    arcpy.Intersect_analysis([ref,LabelPoint.layer],temp_intersect)

    # הכנה של השדות לפני הכנסה לחיבור הטבלאי בין הנקודות לשכבה הראשית
    field_to_pass = ''.join([i+';' for i in field_to_pass])[:-1]

    arcpy.JoinField_management(layer.layer, OID, temp_intersect, ID_Field, field_to_pass)

    LabelPoint.Destroy_layer()
    del temp_intersect

def Average(lst): 
    return sum(lst) / len(lst) 


def delete_parts_if_inside(layer,delete):

    '''
    [INFO] - Delete all Polygons 
    '''

    layer          = Layer_Management(layer)
    LabelPoint     = layer.Get_Label_Point_As_Point()
    LabelPoint     = Layer_Management(LabelPoint)

    LabelPoint.Select_By_Location('INTERSECT',delete,invert = "INVERT")

    layer.Select_By_Location('INTERSECT',LabelPoint.layer)


def Split_Line_By_Vertex(aoi_line):

    Multi_to_single(aoi_line)
    New_Line  = aoi_line + '_Temp'
    save_name = aoi_line

    arcpy.Select_analysis(aoi_line, New_Line, "\"OBJECTID\" < 0")
    iCursor = arcpy.da.InsertCursor(New_Line, ["SHAPE@"])
    with arcpy.da.SearchCursor(aoi_line,["SHAPE@"]) as sCursor:
        for row in sCursor:
            for part in row[0]:
                prevX = None
                prevY = None
                for pnt in part:
                    if pnt:
                        if prevX:
                            array = arcpy.Array([arcpy.Point(prevX, prevY),
                                                arcpy.Point(pnt.X, pnt.Y)])
                            polyline = arcpy.Polyline(array)
                            iCursor.insertRow([polyline])
                        prevX = pnt.X
                        prevY = pnt.Y
                    else:
                        pass

    del iCursor

    arcpy.Delete_management                (aoi_line)
    arcpy.Rename_management                (New_Line,save_name)


def Multi_to_single(layer):
    
    multi = False
    len_before = int(str(arcpy.GetCount_management(layer)))
    temp_lyer = layer  + 'Temp'
    save_name = layer
    arcpy.MultipartToSinglepart_management (layer,temp_lyer)
    arcpy.Delete_management                (layer)
    arcpy.Rename_management                (temp_lyer,save_name)
    len_after = int(str(arcpy.GetCount_management(layer)))
    if len_after > len_before:
        multi = True

    return multi


def Delete_By_area(layer,dis=0.2):
    with arcpy.da.UpdateCursor(layer,['SHAPE@AREA']) as ucursor:
        for row in ucursor:
            if row[0] < dis:
                ucursor.deleteRow()
    del ucursor


def Delete_Duplic_Line(fc):

	del_layer    = 'in_memory' + '\\' + 'arc_inter'
	diss_layer   = 'in_memory' + '\\' + 'diss_layer'
	Append_layer = 'in_memory' + '\\' + 'Append_layer'

	arcpy.Intersect_analysis          ([fc],del_layer)

	if int(str(arcpy.GetCount_management(del_layer))) > 0:

                del_layer_temp = 'in_memory' + '\\' + 'Temp'
                arcpy.Dissolve_management(del_layer,del_layer_temp)

                geom_del = [row.shape for row in arcpy.SearchCursor (del_layer_temp)][0]
                Ucursor  = arcpy.UpdateCursor (fc)
                for row in Ucursor:
                        for row in Ucursor:
                            if geom_del:
                                if row.shape:
                                    geom_up     = row.shape
                                    new_geom    = geom_up.difference(geom_del)
                                    row.shape = new_geom
                                    Ucursor.updateRow (row)


                arcpy.Dissolve_management              (del_layer,diss_layer)
                arcpy.MultipartToSinglepart_management (diss_layer,Append_layer)
                arcpy.Append_management                (Append_layer,fc,"NO_TEST")


def Layer_To_Edge_list(layer):

    '''
    [INFO] -  מוצא את זוג הוורטקסים הקרובים ביותר לכל קצה של ישות, ומחזיר רשימה עם הקארדינטות של שניהם והמרחק
    INPUT: 
    1) layer = שכבה קווית
    OUTPUT = [[ID_1,x1,y1],[ID_2,x2,y2],distance] 
    '''

    def dis(x1,y1,x2,y2):
        dist = math.sqrt(((x1-x2)**2) + ((y1-y2)**2))
        return dist

    data = [[row.OBJECTID,pt.X,pt.Y] for row in arcpy.SearchCursor(layer) for part in row.shape for pt in part]

    df            = pd.DataFrame(data,columns=["OBJECTID","X","Y"])
    df['index1']  = df.index


    gb_obj = df.groupby(by = 'OBJECTID')

    df_min = gb_obj.agg({'index1' : np.min})
    df_max = gb_obj.agg({'index1' : np.max})

    df_edge = pd.concat([df_min,df_max])

    df2 = pd.merge(df,df_edge, how='inner', on='index1')

    df_edge = df2.values.tolist()
    df_list = df.values.tolist()

    new_list = []
    for n in range(len(df_edge)):
        min_list = []
        dict1    = {}
        for i in range(len(df_list)):
            if df_edge[n][0] != df_list[i][0]:
                dist = dis(df_edge[n][1],df_edge[n][2],data[i][1],data[i][2])
                if dist != 0:
                    min_list.append(dist)
                    dict1[dist] = df_list[i]

        if min_list:
            min_l = min(min_list)
            new_list.append([df_edge[n][:-1],dict1[min_l][:-1],min_l])
        else:
            print ("part have no match type")

    return new_list

def Delete_By_length(layer,dis=0.2):
    with arcpy.da.UpdateCursor(layer,['SHAPE@LENGTH']) as ucursor:
        for row in ucursor:
            if row[0] < dis:
                ucursor.deleteRow()
    del ucursor


def fix_tolerance_line(layer_path,border):

    Multi_to_single(layer_path)

    dic_point = {str([float('{0:.1f}'.format(pt.X)),float('{0:.1f}'.format(pt.Y))]):[pt.X,pt.Y] for i in arcpy.SearchCursor(border) for part in i.Shape for pt in part if pt}

    Ucursor = arcpy.UpdateCursor(layer_path)
    for i in Ucursor:
        geom = i.Shape
        array = arcpy.Array()
        j = json.loads(geom.JSON)
        if 'curve' not in str(j):
            for part in geom:
                for pt in part:
                    if pt:
                        key = str([float('{0:.1f}'.format(pt.X)),float('{0:.1f}'.format(pt.Y))])
                        if dic_point.has_key(key):
                            # dis_moved = dis(pt.X, dic_point[key][0],  pt.Y, dic_point[key][1])
                            # print dis_moved # בדיקה כמה זה מתן
                            array.add(arcpy.Point(dic_point[key][0],dic_point[key][1]))
                        else:
                            array.add(arcpy.Point(pt.X, pt.Y))
                    else:
                        array.add(None)
            polyline = arcpy.Polyline(array)
            i.Shape = polyline
            Ucursor.updateRow(i)
            
        else:
            pass
       

def del_Non_Boundery_Line(line_layer,aoi_Final,tazar_border):
    '''
    [INFO] - מוחק קווים שנקודות הלייבל שלהם לא נמצאת על החלקות
    INPUT:
    1) line_layer = שכבת הקווים ממנה נמחק את הקווים שלא יושבים על החלקות
    2) aoi_Final  = שכבת אזור העבודה אליה תהיה השוואה
    3) tazar_border = הכלי יעבוד רק על קווים שיחתכו את שכבה זו
    ''' 
    Line_cut    = line_layer + '_Cut'
    label_point = line_layer + '_labelPoint'

    #get point from line in AOI 
    Layer_Management(Layer_Management(line_layer).Select_By_Location('INTERSECT',tazar_border,'5 Meters',Line_cut)).Get_Label_Point_As_Point(label_point)
    Layer_Management(label_point).Select_By_Location("BOUNDARY_TOUCHES",aoi_Final)

    Layer_Management(line_layer).Select_By_Location("INTERSECT",label_point)

    arcpy.Delete_management(Line_cut)
    arcpy.Delete_management(label_point)

