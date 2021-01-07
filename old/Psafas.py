# -*- coding: utf-8 -*-

import arcpy, sqlite3, math, json, os,itertools,ast
try:
    import arceditor
except:
    pass
import pandas as pd
#from difflib import get_close_matches
arcpy.env.overwriteOutput = True
import math
import logging
import uuid
import arcpy.mapping
import sys
import numpy as np


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



def get_default_Snap_border(point_bankal,tazar):
    PntTmp = r'in_memory' + '\\' + 'PntTmp'
    buffer = r'in_memory' + '\\' + 'buffer'
    dissol = r'in_memory' + '\\' + 'dissol'
    multiP = r'in_memory' + '\\' + 'multiP'

    def Getmin(list1):
        li = [i[2] for i in list1 if i[2] < 1]
        if li:
            return min(li) - 0.01
        else:
            return 1

    arcpy.MakeFeatureLayer_management           (point_bankal,'path_lyr')
    arcpy.SelectLayerByLocation_management      ('path_lyr','WITHIN_A_DISTANCE',tazar,'5 Meters')
    arcpy.Select_analysis                       ('path_lyr',PntTmp)
    arcpy.MakeFeatureLayer_management           (PntTmp,'PntTmp_lyr')
    arcpy.SelectLayerByLocation_management      ('PntTmp_lyr',"COMPLETELY_WITHIN",tazar)
    arcpy.SelectLayerByAttribute_management     ('PntTmp_lyr',"SWITCH_SELECTION")

    arcpy.Buffer_analysis                   ('PntTmp_lyr',buffer,0.5)
    arcpy.Dissolve_management               (buffer,dissol)
    arcpy.MultipartToSinglepart_management  (dissol,multiP)


    with arcpy.da.UpdateCursor(multiP,['SHAPE@AREA']) as cursor:
        for row in cursor:
            if row[0] < 0.8:
                cursor.deleteRow()

    arcpy.MakeFeatureLayer_management       (PntTmp,'path2_lyr')
    arcpy.SelectLayerByLocation_management  ('path2_lyr','INTERSECT',multiP)

    dis_point  = [[row[0],row[1]] for row in arcpy.da.SearchCursor('path2_lyr',['OBJECTID','SHAPE@'])]
    list_dis   = [[row[1],n[0],row[0].distanceTo(n[1])] for n in dis_point for row in arcpy.da.SearchCursor('path2_lyr',['SHAPE@','OID@']) if row[0].distanceTo(n[1]) > 0]

    print_arcpy_message(Getmin(list_dis), status=1)
    return Getmin(list_dis)


def get_no_node_vertex(point,tazar_border,node,old_node):

            print_arcpy_message("START Func: get no node vertex",1)
            
            arcpy.MakeFeatureLayer_management     (point,"points_lyr")
            arcpy.SelectLayerByLocation_management("points_lyr","BOUNDARY_TOUCHES",tazar_border,0.003)
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",node,0.003,"REMOVE_FROM_SELECTION")
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",old_node,0.003,"REMOVE_FROM_SELECTION")
            arcpy.Select_analysis("points_lyr",gdb + "\\" + "Possible_Error_points")

            return gdb + "\\" + "Possible_Error_points"


def getLayerPath(fc):
    # CURRENT
    MXD = arcpy.mapping.MapDocument (r'CURRENT')
    df = MXD.activeDataFrame
    lyrs = arcpy.mapping.ListLayers(MXD, fc.split("\\")[-1], df)
    if lyrs:
        if lyrs[0].isFeatureLayer:
            return os.path.dirname(lyrs[0].dataSource)


def layerInMxd(i):
    # CURRENT
    MXD = arcpy.mapping.MapDocument ("CURRENT")
    df = MXD.activeDataFrame
    #arcpy.AddMessage(i)
    lyrs = arcpy.mapping.ListLayers(MXD, i.split("\\")[-1], df)
    if lyrs:
        arcpy.AddMessage("layer in mxd")
        return True
    else:
        arcpy.AddMessage("No layer in mxd")
        return False



def Get_layer_gdb(parcels_bankal):

    '''
        using func:
            getLayerPath(fc)
            layerInMxd(i)
    '''

    if layerInMxd(parcels_bankal):
        gdb = getLayerPath    (parcels_bankal)
    else:
        gdb = os.path.dirname (parcels_bankal)

    parcel_bankal = gdb + '\\' + 'PARCEL_ALL_EDIT'
    arc_bankal    = gdb + '\\' + 'PARCEL_ARC_EDIT'
    point_bankal  = gdb + '\\' + 'PARCEL_NODE_EDIT'

    parcel_modad  = gdb + '\\' + 'PARCELS_inProc_edit'
    arc_modad     = gdb + '\\' + 'LINES_inProc_edit'
    point_modad   = gdb + '\\' + 'POINTS_inProc_edit'

    arcpy.AddMessage(gdb)
    return parcel_bankal,arc_bankal,point_bankal,parcel_modad,arc_modad,point_modad


def GetBoolValue(param,message):
        if (param == "true"):
            param = True
            print_arcpy_message("Acctiveted: {}".format(message),1)
        else:
            param = False
            print_arcpy_message("Skip: {}".format(message),1)
        return param


def update_curves(fc,curve):
        for row in arcpy.SearchCursor(curve):
                upd_rows = arcpy.UpdateCursor(fc)
                curve_g = row.Shape
                midpnt = curve_g.centroid
                for upd_row in upd_rows:
                        if upd_row.Shape.distanceTo(midpnt)== 0:
                                diff = upd_row.Shape.difference (curve_g)
                                new_geometry = curve_g.union(diff)
                                upd_row.Shape = new_geometry
                                upd_rows.updateRow(upd_row) 


def ChangeFieldNames(parcel,line,point):
    '''
        Take 3 layers, Changing fields from Source layers to bankal format
    '''

    wrong = {'GUSHNUM':'GUSH_NUM','GUSHSUFFIX':'GUSH_SUFFIX','PARCEL_FINAL':'PARCEL','LEGALAREA':'LEGAL_AREA'}

    List_fields = [[str(i.name),wrong[str(i.name)]] for i in arcpy.ListFields(parcel) if str(i.name) in list(wrong.keys())]

    if List_fields:

        print_arcpy_message("Changing Fields",status = 1)
        list_layers = [parcel,line,point]

        for lyr in list_layers:
            for field in List_fields:
                layer   = os.path.basename(lyr)
                parcels = [os.path.basename(parcel)]
                others  = [os.path.basename(line),os.path.basename(point)]
                if layer in others:
                    if field[0] == 'GUSHNUM':
                        add_field(lyr,field[1],'LONG')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")
                    if field[0] == 'GUSHSUFFIX':
                        add_field(lyr,field[1],'SHORT')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")
                if layer in parcels:
                    if field[0] == 'GUSHNUM':
                        add_field(lyr,field[1],'LONG')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

                    if field[0] in ['GUSHSUFFIX','PARCEL_FINAL']:
                        add_field(lyr,field[1],'SHORT')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

                    if field[0] == 'LEGALAREA':
                        add_field(lyr,field[1],'DOUBLE')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

    None_me = [i for i in arcpy.SearchCursor(parcel) if i.PARCEL_FINAL == None]
    if None_me:
        arcpy.CalculateField_management  (parcel, 'PARCEL', "int( ''.join ([i for i in !PARCELNAME! if i.isdigit()]))", "PYTHON" ) 

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
        del del_layer_temp
                        
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

def get_fc_from_mxd(fc_name):
        #CURRENT
        mxd = arcpy.mapping.MapDocument(r"CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        lyrs = arcpy.mapping.ListLayers(mxd, '*', df)
        fc = None
        for lyr in lyrs:
                if lyr.isFeatureLayer:
                        if os.path.basename(lyr.dataSource) == fc_name:
                                fc = lyr.dataSource
        return fc

def stubborn_parts(path,bankal,tazar,curves,Out_put):

        print_arcpy_message("START Func: stubborn parts",1)
    
        memory = r'in_memory'
        gdb    = os.path.dirname(path)

        ## Create_layers
        sliver_curves    = memory + '\\'+ 'sliver_curves'
        path2            = gdb + '\\'+ 'COPY_TEMP3'
        del_polygons     = gdb + '\\'+ 'del_polygons'
        Featur_to_poly   = memory + '\\' + 'Featur_to_poly'
        paracel_around   = gdb +"\\"+ "paracel2_around"
        parcal_all_Final = Out_put
                
        arcpy.MakeFeatureLayer_management(path,'path_lyr')
        arcpy.SelectLayerByLocation_management('path_lyr',"ARE_IDENTICAL_TO",curves)
        if int(str(arcpy.GetCount_management('path_lyr'))) > 0:
                        #print_arcpy_message("found identical rings")
                        arcpy.DeleteFeatures_management('path_lyr')             
                
                
                
        ## making buffer of slivers
        Feature_to_polygon(path,Featur_to_poly)
        Delete_polygons         (Featur_to_poly,path,sliver_curves)
        arcpy.CopyFeatures_management(path,path2)


        upd_cursor = arcpy.UpdateCursor(sliver_curves)
        for upd in upd_cursor:
                geom = upd.shape
                try:
                                    if geom.area/geom.length > 1:
                                                    upd_cursor.deleteRow(upd)
                except:
                                    pass
                        
        del upd_cursor

        num_slivers = int(str(arcpy.GetCount_management(sliver_curves)))
        if num_slivers > 0:
                print_arcpy_message ("you still have {} slivers, rebuild geometry and attributes".format(num_slivers),1)
        
                arcpy.MakeFeatureLayer_management     (path2, "FINAL2_lyr", "\"UPDATE_CODE\" = 'U'") 
                arcpy.SelectLayerByLocation_management("FINAL2_lyr","SHARE_A_LINE_SEGMENT_WITH",sliver_curves)
                arcpy.MakeFeatureLayer_management     (bankal, "paracel2_lyr") 
                arcpy.SelectLayerByLocation_management("paracel2_lyr","INTERSECT","FINAL2_lyr")
                arcpy.Select_analysis                 ("paracel2_lyr", paracel_around)
                arcpy.MakeFeatureLayer_management     (path2, "FINAL2_lyr2")
                arcpy.SelectLayerByLocation_management("FINAL2_lyr2","SHARE_A_LINE_SEGMENT_WITH",sliver_curves)
                arcpy.Select_analysis                 ("FINAL2_lyr2", del_polygons)
                #Delete_polygons                       (path2,del_polygons)

                def delete_parts_if_inside(orig,delete):
                        for row in arcpy.SearchCursor(delete):
                                upd_rows   = arcpy.UpdateCursor(orig)
                                mid_point  = row.Shape
                                midpnt     = mid_point.labelPoint
                                for upd_row in upd_rows:
                                        if upd_row.Shape.distanceTo(midpnt)== 0:
                                                upd_rows.deleteRow(upd_row)
                                                upd_rows.updateRow(upd_row)
                                                 
                delete_parts_if_inside(paracel_around,path2)
                delete_parts_if_inside(paracel_around,del_polygons)
                delete_parts_if_inside(path2,del_polygons)

                Update_polygons       (path2,paracel_around,'in_memory' + '\\' + 'path2_layer')
                Update_polygons       ('in_memory' + '\\' + 'path2_layer',tazar,'in_memory' +'\\' + 'before_poly_to_feature')
                Feature_to_polygon('in_memory' +'\\' + 'before_poly_to_feature',Out_put)
                delete_parts_if_inside(Out_put,paracel_around)

                for row in arcpy.SearchCursor(path):
                        upd_rows = arcpy.UpdateCursor(Out_put)
                        mid_point  = row.Shape
                        midpnt     = mid_point.labelPoint                                   
                        for upd_row in upd_rows:                                                     
                                if upd_row.Shape.distanceTo(arcpy.Point(midpnt.X,midpnt.Y))== 0:
                                        upd_row.GUSH_NUM      = row.GUSH_NUM
                                        upd_row.GUSH_SUFFIX   = row.GUSH_SUFFIX
                                        upd_row.LEGAL_AREA    = row.LEGAL_AREA
                                        upd_row.PNUMTYPE      = row.PNUMTYPE
                                        upd_row.PARCEL_ID     = row.PARCEL_ID
                                        upd_row.STATUS        = row.STATUS
                                        upd_row.STATUS_TEXT   = row.STATUS_TEXT
                                        upd_row.LOCALITY_ID   = row.LOCALITY_ID
                                        upd_row.LOCALITY_NAME = row.LOCALITY_NAME
                                        upd_row.REG_MUN_ID    = row.REG_MUN_ID
                                        upd_row.REG_MUN_NAME  = row.REG_MUN_NAME
                                        upd_row.COUNTY_ID     = row.COUNTY_ID
                                        upd_row.COUNTY_NAME   = row.COUNTY_NAME
                                        upd_row.REGION_ID     = row.REGION_ID
                                        upd_row.REGION_NAME   = row.REGION_NAME
                                        upd_row.WP            = row.WP
                                        upd_row.TALAR_NUMBER  = row.TALAR_NUMBER
                                        upd_row.TALAR_YEAR    = row.TALAR_YEAR
                                        upd_row.SYS_DATE      = row.SYS_DATE
                                        upd_row.UPDATE_CODE   = row.UPDATE_CODE
                                        upd_row.OVERLAP_PRCT  = row.OVERLAP_PRCT
                                        upd_row.KEY_parcel    = row.KEY_parcel
                                        upd_rows.updateRow(upd_row)

                arcpy.MakeFeatureLayer_management      (Out_put,'Out_put_lyr',"\"LEGAL_AREA\" is null")
                arcpy.SelectLayerByLocation_management ('Out_put_lyr','INTERSECT',tazar,'5 Meters',"REMOVE_FROM_SELECTION")
                arcpy.DeleteFeatures_management        ('Out_put_lyr')

                update_rows = arcpy.UpdateCursor(Out_put)
                for row in update_rows:
                        if row.GUSH_NUM ==0:
                                update_rows.deleteRow(row)
                                update_rows.updateRow(row)

                before = int(str(arcpy.GetCount_management(path)))
                after  = int(str(arcpy.GetCount_management(Out_put)))
                if before > after:
                    print_arcpy_message     ("Stubbern seems to delete features, Cancel and return 1 step back",1)
                    arcpy.Delete_management (Out_put)
                    arcpy.Select_analysis   (path,parcal_all_Final)

        else:
             print_arcpy_message          ("No stubborn parts")
             arcpy.CopyFeatures_management(path,Out_put)
    
        arcpy.Delete_management(path2)
        arcpy.Delete_management(del_polygons)
        arcpy.Delete_management(paracel_around)


def CreateWorkingGDB(fc,Folder):

    '''
        Create GDB and copy all the layers from the source GDB to the new GDB
    '''
    
    gdb           = os.path.dirname  (fc)
    folder_source = os.path.dirname  (gdb)
    name          = os.path.basename (folder_source)
    tazar_num     = ''.join([i for i in name if i.isdigit()])
    ws = Folder + '\\' + 'Tazar_{}.gdb'.format(tazar_num)
    if arcpy.Exists(ws):
                    arcpy.Delete_management(ws)

    print 'Tazar_{}.gdb'.format(tazar_num)
    arcpy.CreateFileGDB_management(Folder,'Tazar_{}.gdb'.format(tazar_num))
    
    copy        = ['PARCEL_ALL_EDIT','PARCEL_ARC_EDIT','PARCEL_NODE_EDIT','PARCELS_inProc_edit','LINES_inProc_edit','POINTS_inProc_edit']
    return_list = []
    for fc in copy:
        try:
            arcpy.CopyFeatures_management    (gdb + '\\' + fc ,ws + '\\' + fc + '_copy')
        except:
            copy_me = get_fc_from_mxd        ('Parcels_inProc_edit')
            gdb     = os.path.dirname(copy_me)
            arcpy.CopyFeatures_management    (gdb + '\\' + fc ,ws + '\\' + fc + '_copy')
        return_list.append(ws + '\\' + fc + '_copy')

    return return_list


def add_field(fc,field,Type = 'TEXT'):
    TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
    if not TYPE:
        arcpy.AddField_management (fc, field, Type)


def Snap_border_by_pt_name(parcel_all, tazar_border, node_tazar, old_pts):

    arcpy.CalculateField_management(old_pts, "POINT_NAME", "!POINT_NAME!.lstrip()", "PYTHON")
    arcpy.CalculateField_management(node_tazar, "POINT_NAME", "!POINT_NAME!.lstrip()", "PYTHON")
    
    def VerticesToTabelWithName(fc, table,c, pts):
        #read fc vertices
        xys = []
        desc = arcpy.Describe(fc)
        pts_lyr = desc.name
        arcpy.MakeFeatureLayer_management(pts, pts_lyr)
        arcpy.SelectLayerByLocation_management(pts_lyr, "BOUNDARY_TOUCHES", fc)
        pts_rows = [[row.POINT_NAME, row.SHAPE] for row in arcpy.SearchCursor(pts_lyr)]
        c.execute('''CREATE TABLE pts(pnt_num real, x real, y real, xy text, name text)''')
        pt_num = 1
        for item in pts_rows:
            x = item[1].centroid.X
            y = item[1].centroid.Y
            name = item[0]

            try:
                c.execute("INSERT INTO pts VALUES ("+str(pt_num) + ","
                                      +str(x) + ","
                                      +str(y)  +","
                                      +"'"+str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y)))+"',"
                                      +"'"+str(name) +"')")
            except:
                c.execute("INSERT INTO pts VALUES ("+str(pt_num) + ","
                                      +str(x) + ","
                                      +str(y)  +","
                                      +"'"+str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y)))+"',"
                                      +"'"+'<Null>' +"')")
                
                print_arcpy_message("Coudent Write name",2)

            
            pt_num = 1 + 1
                
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
                        xy = str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y)))
                        names = [row[0] for row in c.execute("SELECT name FROM pts where xy ='" + str(xy) + "'")]
                        if len(names) > 0:
                                name = names[0]
                        else:
                                name = ""
                        c.execute("INSERT INTO "+table+" VALUES ("+str(fc_pnt_num) + ","
                                  +str(x) + ","
                                  +str(y) + ","
                                  +"'"+str(float("{0:.2f}".format(x)))+"-"+str(float("{0:.2f}".format(y)))+"',"
                                  +str(fc_part_num) + ","
                                  +str(fc_oid) +",0, 0" + ",'"+str(name)+"')")
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
            
        c.execute('''DROP TABLE pts''')


    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr")#, "\"UPDATE_CODE\" <> 'D' OR \"UPDATE_CODE\" IS NULL")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "WITHIN_A_DISTANCE", tazar_border, '5 Meters')

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real, name text)''')

    c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real, name text)''')


    #print "read border"
    VerticesToTabelWithName(tazar_border, "border",c, node_tazar)
    border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
    #print "read parcels"
    VerticesToTabelWithName("parcel_all_lyr", "parcels",c, old_pts)

    #print "parcel equal border by name" 
    parcel_vertices_name = [row for row in c.execute("SELECT * FROM parcels left join border on parcels.name = border.name where  border.name is not null and parcels.name <> '' and parcels.name is not null")]
    #print "get the parcels vertices"

    rows = arcpy.UpdateCursor("parcel_all_lyr")
    for row in rows:
        geometry = row.Shape
        oid = row.OBJECTID
        pts = []
        ring = []
        poly_vertices = [r for r in parcel_vertices_name if r[5] == oid]
        for part in geometry:
            counter = 0
            for pt in part:
                if str(type(pt)) <> "<type 'NoneType'>":
                    if counter == 0:
                        first_pt = pt
                    num_point = 0
                    #print str(pt.X) + "--" + str(pt.Y)
                    this_x = float("{0:.2f}".format(pt.X))
                    this_y = float("{0:.2f}".format(pt.Y))      
                    this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[1])) == this_x and float("{0:.2f}".format(p[2])) == this_y]
                    if this_vertex:
                        ###### CHECK DISTANCE IS < 10 !!!!!
                        #print str(pt.X) + " = " + str(this_vertex[0][10])
                        #print str(pt.Y) + " = " + str(this_vertex[0][11])
                        x = pt.X
                        y = pt.Y
                        x2 = this_vertex[0][10]
                        y2 = this_vertex[0][11]
                        dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                        if dis < 10:
                            #move the actual points
                            ptrows = arcpy.UpdateCursor(old_pts)
                            for ptrow in ptrows:
                                if ptrow.Shape.centroid.X == pt.X and ptrow.Shape.centroid.Y == pt.Y:
                                    ptrow.Shape = arcpy.Point(this_vertex[0][10], this_vertex[0][11])
                                    ptrows.updateRow(ptrow)     
                            ring.append([this_vertex[0][10],this_vertex[0][11]])
                        else:
                            ring.append([pt.X, pt.Y])
                    else:
                        ring.append([pt.X, pt.Y])
                        #pts.append(point)
                        
                    counter = counter + 1
                else:
                    ring.append([first_pt.X, first_pt.Y])
                    ring.append(None)
                    counter = 0

            pts.append(ring)                                           
            polygon = PtsToPolygon1(pts)
            row.Shape       = polygon
            row.UPDATE_CODE = 'U'
            rows.updateRow(row)


def collinearity(p1, p2, p3):
    """return True if 3 points are collinear.
    tolerance value will decide whether lines are collinear; may need
    to adjust it based on the XY tolerance value used for feature class"""
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]
    res = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
    return abs(res)  


def PtsPairToLine(pt1, pt2):
    array1 = arcpy.Array()
    array1.add(pt1)
    array1.add(pt2)
    polyline = arcpy.Polyline(array1)
    #array.removeAll()
    return polyline


def PtsToPolygon(pts):
    point = arcpy.Point()
    array = arcpy.Array()
    for point in pts:
        array.add(point)
    array.add(array.getObject(0))

    polygon = arcpy.Polygon(array, arcpy.SpatialReference("Israel TM Grid"))
    return polygon
        
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


def fix_tolerance(parcel_all,border,dis_search):

    print_arcpy_message("START Func: fix tolerance",1)
    
    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "WITHIN_A_DISTANCE", border, '5 Meters')

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


    c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

    gdb = os.path.dirname(border)
    border_diss = gdb + '\\' + 'border_diss'
    arcpy.Dissolve_management(border,border_diss)
    VerticesToTable2(border_diss, "border",c)
    arcpy.Delete_management (gdb + '\\' + 'border_diss')
    border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
    VerticesToTable2("parcel_all_lyr", "parcels",c)

    parcel_non_common_vertices = [row for row in c.execute('''SELECT * FROM parcels
                                                                     left join border
                                                                     on parcels.xy = border.xy
                                                                     where  border.xy is null''')]


    border_geom = arcpy.CopyFeatures_management(border, arcpy.Geometry())[0]
    vertices_on_border_outline = []
    for row in parcel_non_common_vertices:
                    x = row[1]
                    y = row[2]
                    point = arcpy.Point(x, y)    
                    if border_geom.distanceTo (point) < 5:
                                    vertices_on_border_outline.append(row)

    #print "get the parcels vertices who close to border vertices"
    close_vertices = []
    distances = []
    for p in vertices_on_border_outline:
                    x = p[1]
                    y = p[2]
                    for b in border_vertices:
                                    #if b[3] <> p[3]:
                                    x2 = b[1]
                                    y2 = b[2]
                                    dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                                    if dis < dis_search or (float("{0:.5f}".format(x)) == float("{0:.5f}".format(x2)) and float("{0:.5f}".format(y)) == float("{0:.5f}".format(y2))):
                                                    close_vertices.append(p[:8] + b[:8])
                                                    distances.append(dis)
    distance_vertices = zip(close_vertices, distances)


    rows = arcpy.UpdateCursor("parcel_all_lyr")
    for row in rows:
                    geometry = row.Shape
                    oid = row.OBJECTID
                    pts = []
                    poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
                    for part in geometry:
                                    for pt in part:
                                                    if str(type(pt)) <> "<type 'NoneType'>":
                                                                    num_point = 0
                                                                    #print str(pt.X) + "--" + str(pt.Y)
                                                                    this_x = float("{0:.5f}".format(pt.X))
                                                                    this_y = float("{0:.5f}".format(pt.Y))      
                                                                    this_vertex = [p for p in poly_vertices if float("{0:.5f}".format(p[0][1])) == this_x and float("{0:.5f}".format(p[0][2])) == this_y]
                                                                    if this_vertex:
                                                                                    if this_vertex[0][0][8] == None:
                                                                                                    if this_vertex[0][0][7] < 0.5 and this_vertex[0][0][6] == 1:
                                                                                                            print "pseodo: delete vertex"
                                                                                                    else:
                                                                                                                    point = pt
                                                                                                                    pts.append(point)
                                                                                    else:
                                                                                                    #print "tazar point in buffer"
                                                                                                    the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                                                                                    point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                                                                                    pts.append(point)
                                                                    else:
                                                                                    point = pt
                                                                                    pts.append(point)
                                                                    if num_point == 0:
                                                                                    first_point = point
                                                                    num_point = num_point + 1
                    polygon = PtsToPolygon(pts)
                    if pts[0] <> pts[-1] and first_point:
                                    pts.append(first_point)
                    row.Shape       = polygon
                    rows.updateRow(row)



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


def Snap_border_pnts(ws,border,parcel_all,Dis_search = 1):


    print_arcpy_message('START Func: Snap border pnts',1)

    tazar_border = 'in_memory\Tazar_Border_diss'
    arcpy.Dissolve_management(border,tazar_border)

    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr", "\"UPDATE_CODE\" <> 'D' OR \"UPDATE_CODE\" IS NULL")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "WITHIN_A_DISTANCE", tazar_border, '5 Meters')

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


    c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


    VerticesToTable2(tazar_border, "border",c)
    border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
    VerticesToTable2("parcel_all_lyr", "parcels",c)

    parcel_non_common_vertices = [row for row in c.execute('''SELECT * FROM parcels
                                                                     left join border
                                                                     on parcels.xy = border.xy
                                                                     where  border.xy is null''')]
    
    
    border_geom = arcpy.CopyFeatures_management(tazar_border, arcpy.Geometry())[0]
    vertices_on_border_outline = []
    for row in parcel_non_common_vertices:
                    x = row[1]
                    y = row[2]
                    point = arcpy.Point(x, y)
                    #if border_geom.touches(point):     
                    if border_geom.distanceTo (point) < 5:
                                    vertices_on_border_outline.append(row)

    close_vertices = []
    distances = []
    for p in vertices_on_border_outline:
                    x = p[1]
                    y = p[2]
                    for b in border_vertices:
                                    #if b[3] <> p[3]:
                                    x2 = b[1]
                                    y2 = b[2]
                                    dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                                    if dis < Dis_search or (float("{0:.2f}".format(x)) == float("{0:.2f}".format(x2)) and float("{0:.2f}".format(y)) == float("{0:.2f}".format(y2))):
                                                    close_vertices.append(p[:8] + b[:8])
                                                    distances.append(dis)
    distance_vertices = zip(close_vertices, distances)


    rows = arcpy.UpdateCursor("parcel_all_lyr")
    for row in rows:
                    geometry = row.Shape
                    oid = row.OBJECTID
                    pts = []
                    poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
                    for part in geometry:
                                    for pt in part:
                                                    if str(type(pt)) <> "<type 'NoneType'>":
                                                                    num_point = 0
                                                                    #print str(pt.X) + "--" + str(pt.Y)
                                                                    this_x = float("{0:.2f}".format(pt.X))
                                                                    this_y = float("{0:.2f}".format(pt.Y))      
                                                                    this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[0][1])) == this_x and float("{0:.2f}".format(p[0][2])) == this_y]
                                                                    if this_vertex:
                                                                                    if this_vertex[0][0][8] == None:
                                                                                                    if this_vertex[0][0][7] < 0.5 and this_vertex[0][0][6] == 1:
                                                                                                            print "pseodo: delete vertex"
                                                                                                    else:
                                                                                                                    #print "pseodo, but important: keep the vertex"
                                                                                                                    point = pt
                                                                                                                    pts.append(point)
                                                                                    # tazar point in buffer
                                                                                    else:
                                                                                                    # check minimum distance
                                                                                                    the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                                                                                    point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                                                                                    pts.append(point)
                                                                    # point not on sliver: keep the vertex
                                                                    else:
                                                                                    point = pt
                                                                                    pts.append(point)
                                                                    if num_point == 0:
                                                                                    first_point = point
                                                                    num_point = num_point + 1
                    polygon = PtsToPolygon(pts)
                    if pts[0] <> pts[-1] and first_point:
                                    #print "ooops.... - polygon not closed"
                                    pts.append(first_point)
                    row.Shape       = polygon
                    #row.UPDATE_CODE = 'U'
                    rows.updateRow(row)

    


    
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


def Update_polygons(fc,Update_layer,Out_put,tazar_border = '',curves = ''):

    
    desc    = arcpy.Describe(fc)
    wc,name = os.path.split(fc)

    name_copy = wc + '\\' + 'copy_up'
    arcpy.CopyFeatures_management(fc,name_copy)
    
    count_me = int(str(arcpy.GetCount_management(Update_layer)))
    if count_me > 0:
        num = 0
        while num < count_me:
            geom_del = [row.shape for row in arcpy.SearchCursor (Update_layer)][num]
            Ucursor  = arcpy.UpdateCursor (name_copy)
            for row in Ucursor:
                geom_up     = row.shape
                new_geom    = geom_up.difference(geom_del)
                try:
                    row.shape = new_geom
                    Ucursor.updateRow (row)
                except:
                    pass
            num += 1
            del Ucursor
    else:
        pass

    arcpy.Merge_management([name_copy,Update_layer],Out_put)
    arcpy.Delete_management(name_copy)
    up_cursor = arcpy.UpdateCursor(Out_put)
    for row in up_cursor:
        geom = row.shape
        if geom.area == 0:
            up_cursor.deleteRow(row)

        
    del up_cursor
    arcpy.RepairGeometry_management(Out_put)
        
    if curves != '':
        #print_arcpy_message("try to curve from inside update",status = 1)
        Fix_curves(Out_put,tazar_border,curves)
    
    return Out_put

def fix_possible_err_pts(PARCEL_ALL_FINAL, tazar_border, Possible_Error_points, parcels_tazar ,parcel_bankal, curves):

    print_arcpy_message("START Func: fix possible err pts",1)

    gdb = os.path.dirname(tazar_border)

    Update_polygons   (PARCEL_ALL_FINAL, parcels_tazar, gdb + '\\' + "PLAN_B",tazar_border,curves)

    planA = True
    
    
    if int(str(arcpy.GetCount_management(Possible_Error_points))) > 0 :
        
        arcpy.MakeFeatureLayer_management(PARCEL_ALL_FINAL, "parcel_all_lyr")
        arcpy.SelectLayerByLocation_management("parcel_all_lyr", "INTERSECT", Possible_Error_points )

        conn = sqlite3.connect(':memory:')
        c    = conn.cursor()


        c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')
        c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

        VerticesToTable2("parcel_all_lyr", "parcels",c)
        border_diss = r'in_memory\border_diss'
        arcpy.Dissolve_management(tazar_border,border_diss)
        VerticesToTable2         (border_diss, "border",c)



        parcel_non_common_vertices = [row for row in c.execute('''SELECT * FROM parcels
                                                                             left join border
                                                                             on parcels.x = border.x and parcels.y = border.y 
                                                                             where  border.xy is null''')]
        pts = []

        ##
        Dis_search  = 5

        err_vertices = [[float("{0:.2f}".format(row.Shape.centroid.X)), float("{0:.2f}".format(row.Shape.centroid.Y))] for row in arcpy.SearchCursor(Possible_Error_points)]
        #print "get the parcels vertices on border outline"
        border_geom = arcpy.CopyFeatures_management(tazar_border, arcpy.Geometry())[0]
        border_geom = border_geom.buffer(0.001)

        vertices_on_border_outline = []
        for row in parcel_non_common_vertices:
            x = row[1]
            y = row[2]
            point = arcpy.Point(x, y)
            if border_geom.disjoint(point) == False:
                if [float("{0:.2f}".format(row[1])), float("{0:.2f}".format(row[2]))] in err_vertices:
                    vertices_on_border_outline.append(row)
                else:
                    for err in err_vertices:
                        if abs(err[0] - x) < 0.1 and  abs(err[1] - y)  < 0.1:
                            vertices_on_border_outline.append(row)
                            
        border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
        parcel_vertices = [row for row in c.execute('''SELECT * FROM parcels''')]


        for p in vertices_on_border_outline:
            close_vertices = []
            distances = []
            x =p[1]
            y = p[2]
            for b in border_vertices:
                x2 = b[1]
                y2 = b[2]
                dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                close_vertices.append(p[:8] + b[:8])
                distances.append(dis)
            distance_vertices = zip(close_vertices, distances)


            rows = arcpy.UpdateCursor("parcel_all_lyr")
            for row in rows:
                first_point = 0
                geometry = row.Shape
                oid = row.OBJECTID
                pts = []
                poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
                if poly_vertices:
                    for part in geometry:
                        num_point = 0
                        for pt in part:
                            if str(type(pt)) <> "<type 'NoneType'>":
                                this_x = float("{0:.2f}".format(pt.X))
                                this_y = float("{0:.2f}".format(pt.Y))      
                                this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[0][1])) == this_x and float("{0:.2f}".format(p[0][2])) == this_y]
                                if this_vertex:
                                    if this_vertex[0][0][8] == None:
                                        #print "no border vertex in tolerance"
                                        if this_vertex[0][0][7] < 0.9:
                                            #print "pseodo: delete vertex"
                                            pass
                                        else:
                                            #print "pseodo, but important: keep the vertex"
                                            pts.append(point)
                                    else:
                                        #print "check minimum distance"
                                        the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                        if the_minimum_vertex[0][1] < Dis_search:
                                            point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                            pts.append(point)
                                        else:
                                            pass
                                            #print "pseodo not have border vertex: delete vertex"
                                else:
                                    point = pt
                                    pts.append(point)
                                    if num_point == 0:
                                        first_point = point
                                num_point = num_point + 1
                if pts:      
                    if pts[0] <> pts[-1] and first_point > 0:
                        pts.append(first_point)
                    polygon = PtsToPolygon(pts)
                    row.Shape       = polygon
                    rows.updateRow(row)
            
        arcpy.Rename_management (PARCEL_ALL_FINAL, PARCEL_ALL_FINAL + "_1")
        Delete_polygons         (PARCEL_ALL_FINAL + "_1",tazar_border,gdb + '\\'  + 'PARCEL_ALL_FINAL3')
        Update_polygons         (gdb + '\\'  + 'PARCEL_ALL_FINAL3', parcels_tazar, PARCEL_ALL_FINAL,tazar_border,curves)

        C = Check_bigger_area   (gdb + '\\' + "PLAN_B",PARCEL_ALL_FINAL)
        B = number_of_curves    (gdb + '\\' + "PLAN_B")
        P = number_of_curves    (PARCEL_ALL_FINAL)

        print_arcpy_message("C : {})".format(C),1)
        print_arcpy_message("CheckResultsIsOK : {})".format(str(CheckResultsIsOK(PARCEL_ALL_FINAL,parcels_tazar,curves,gdb,5))),1)
        print_arcpy_message("P : {})".format(P-B),1)

        if (C > 5) and (CheckResultsIsOK(PARCEL_ALL_FINAL,parcels_tazar,curves,gdb,5) == False) and (P <= B):

            print_arcpy_message('Plan B Activated',1)
            arcpy.Rename_management (PARCEL_ALL_FINAL, PARCEL_ALL_FINAL + "_C")
            arcpy.Rename_management (gdb + '\\' + "PLAN_B", PARCEL_ALL_FINAL)
            print_arcpy_message     ("Check Modad Points, some points seems to be missing", 1)
            planA = False
            main_new_old_points     (parcel_bankal,PARCEL_ALL_FINAL,tazar_border)
            arcpy.Delete_management (gdb + '\\' + 'Check_5')
        return planA
    else:
        print_arcpy_message     ('No Possible error points',1)
        arcpy.Delete_management (gdb + '\\' + 'Check_5')


def Clean_non_exist_pnts(ws,border,parcel_all,Dis_search = 1):

        print_arcpy_message("START Func: Clean non exist pnts",1)

        arcpy.MakeFeatureLayer_management(parcel_all, "parcel_lyr")
        arcpy.SelectLayerByLocation_management("parcel_lyr", "SHARE_A_LINE_SEGMENT_WITH", border)

        conn = sqlite3.connect(':memory:')
        c = conn.cursor()

        c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


        c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


        #print_arcpy_message("read border",1)
        border_diss = ws + '\\' + 'border_diss'
        arcpy.Dissolve_management (border,border_diss)
        VerticesToTable2          (border_diss, "border",c)
        arcpy.Delete_management   (ws + '\\' + 'border_diss')
        border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
        #print_arcpy_message("read parcels",1)
        VerticesToTable2("parcel_lyr", "parcels",c)

        #print_arcpy_message("parcel not equal border vertices",1) 
        parcel_non_common_vertices = [row for row in c.execute('''SELECT * FROM parcels
                                                                                                                         left join border
                                                                                                                         on parcels.xy = border.xy
                                                                                                                         where  border.xy is null''')]
        #print_arcpy_message("get the parcels vertices on border outline",1) 
        border_geom = arcpy.CopyFeatures_management(border, arcpy.Geometry())[0]
        vertices_on_border_outline = []
        for row in parcel_non_common_vertices:
                        x = row[1]
                        y = row[2]
                        point = arcpy.Point(x, y)
                        if border_geom.touches(point):
                                        vertices_on_border_outline.append(row)

         
        close_vertices = []
        distances = []
        for p in vertices_on_border_outline:
                        x = p[1]
                        y = p[2]
                        for b in border_vertices:
                                        #if b[3] <> p[3]:
                                        x2 = b[1]
                                        y2 = b[2]
                                        dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                                        if dis < Dis_search or (float("{0:.2f}".format(x)) == float("{0:.2f}".format(x2)) and float("{0:.2f}".format(y)) == float("{0:.2f}".format(y2))):
                                                        close_vertices.append(p[:8] + b[:8])
                                                        distances.append(dis)
        distance_vertices = zip(close_vertices, distances)


        rows = arcpy.UpdateCursor("parcel_lyr")
        for row in rows:
                        geometry = row.Shape
                        oid = row.OBJECTID
                        pts = []
                        poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
                        for part in geometry:
                                        for pt in part:
                                                        if str(type(pt)) <> "<type 'NoneType'>":
                                                                        num_point = 0
                                                                        #print str(pt.X) + "--" + str(pt.Y)
                                                                        this_x = float("{0:.2f}".format(pt.X))
                                                                        this_y = float("{0:.2f}".format(pt.Y))      
                                                                        this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[0][1])) == this_x and float("{0:.2f}".format(p[0][2])) == this_y]
                                                                        if this_vertex:
                                                                                        if this_vertex[0][0][8] == None:
                                                                                                        if this_vertex[0][0][7] < 0.5 and this_vertex[0][0][6] == 1:
                                                                                                                print "pseodo: delete vertex"
                                                                                                        else:
                                                                                                                        #print "pseodo, but important: keep the vertex"
                                                                                                                        point = pt
                                                                                                                        pts.append(point)
                                                                                        # tazar point in buffer
                                                                                        else:
                                                                                                        # check minimum distance
                                                                                                        the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                                                                                        point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                                                                                        pts.append(point)
                                                                        # point not on sliver: keep the vertex
                                                                        else:
                                                                                        point = pt
                                                                                        pts.append(point)
                                                                        if num_point == 0:
                                                                                        first_point = point
                                                                        num_point = num_point + 1
                                                                                    
                        if pts[0] <> pts[-1] and first_point:
                                        #print "ooops.... - polygon not closed"
                                        pts.append(first_point)
                        polygon = PtsToPolygon(pts)
                        row.Shape       = polygon
                        row.UPDATE_CODE = 'U'
                        rows.updateRow(row)





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
                layer_ID = [row.OBJECTID for row in arcpy.SearchCursor('ARCEL_ALL_FINAL_lyr',['OBJECTID','UPDATE_CODE']) if row.UPDATE_CODE is not None]
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
        arcpy.Rename_management (fc2, name)

def NewGushim(parcel_tazar, parcel_all_bankal,layer_finish):

    print_arcpy_message("START Func: NewGushim",1)
        
    arcpy.MakeFeatureLayer_management      (parcel_all_bankal, "in_memory\\bankal")
    arcpy.SelectLayerByLocation_management ("in_memory\\bankal", 'INTERSECT', parcel_tazar,"2000 Meters")
        
    arcpy.Dissolve_management              ("in_memory\\bankal", "in_memory\\sub_gush_all","GUSH_NUM", "", "SINGLE_PART")
    arcpy.Dissolve_management              (layer_finish, "in_memory\\layer_finish_gush","GUSH_NUM", "", "SINGLE_PART")     
        
    Gush_stay   = []
    Gush_change = []
        
    parcel_GUSH_bankal = [[i.GUSH_NUM,i.SHAPE] for i in arcpy.SearchCursor("in_memory\\sub_gush_all")]
    with arcpy.da.SearchCursor("in_memory\\layer_finish_gush",["GUSH_NUM","SHAPE@"]) as cursor:
                for row in cursor:
                        if parcel_GUSH_bankal:
                            if str(row[0]) == str(parcel_GUSH_bankal[0][0]):
                                    if row[1].union(parcel_GUSH_bankal[0][1]) == row[1]:
                                            Gush_stay.append(row[0])
                                    else:
                                            Gush_change.append(row[0])
        
    if len(Gush_change) > 0:
                print_arcpy_message ("there is gush that moved, name: {}".format(Gush_change),status = 1)   

        
    gushim_tazar = list(set([row.GUSH_NUM for row in arcpy.SearchCursor(parcel_tazar)]))
    gushim_all = list(set([row.GUSH_NUM for row in arcpy.SearchCursor("in_memory\\sub_gush_all")]))
    new_gushim = [g for g in gushim_tazar if g not in gushim_all]
    if len(new_gushim) > 0:
                print_arcpy_message("there is  New Gush in the tazar name {}".format(new_gushim),status = 1) 
    else:
                print_arcpy_message("there is no New Gush in the tazar",status = 1)  

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



            
def prepare_data(parcels_tazar,parcels_bankal,gdb,node_bankal,Point_modad):
                
    tazar_border       = gdb + "\\" + "tazar_border"
    parcels_old        = gdb + "\\PARCEL_ALL"
    parcel_node        = gdb + "\\" + "parcel_node"
        

    arcpy.Dissolve_management                (parcels_tazar, tazar_border, "", "", "SINGLE_PART")
    arcpy.MakeFeatureLayer_management        (parcels_bankal, "parcels_bankal_lyr")
    arcpy.SelectLayerByLocation_management   ("parcels_bankal_lyr", "INTERSECT", tazar_border, "5 Meters")
    arcpy.Select_analysis                    ("parcels_bankal_lyr", parcels_old)
    # delete all parcels in border
    arcpy.AddField_management             (parcels_old, "UPDATE_CODE", "TEXT")
    arcpy.MakeFeatureLayer_management     (parcels_old, "old_lyr")
    arcpy.SelectLayerByLocation_management("old_lyr", "WITHIN", tazar_border)
    arcpy.CalculateField_management       ("old_lyr", "UPDATE_CODE", "\"D\"", "VB")
    arcpy.MakeFeatureLayer_management     (parcels_old, "old_lyr", "\"UPDATE_CODE\" IS NULL")

    node_bankal_old = gdb +'\\'+ "old_pts_names"
    arcpy.Intersect_analysis                   ([node_bankal,parcels_old],parcel_node)
    arcpy.Select_analysis                      (parcel_node, node_bankal_old)
    
    node_tazar = arcpy.CopyFeatures_management(Point_modad, gdb +'\\' + 'node_tazar')

    #snap vertices to border by point_name
    arcpy.AddSpatialIndex_management(parcels_old)
    arcpy.AddSpatialIndex_management(tazar_border)
    arcpy.AddSpatialIndex_management(node_tazar)
    arcpy.AddSpatialIndex_management(node_bankal_old)
    Snap_border_by_pt_name(parcels_old, tazar_border, node_tazar, node_bankal_old)

    #print "erase outside parcels"
    arcpy.Dissolve_management(tazar_border, tazar_border+"_diss_tmp", "", "", "MULTI_PART")
    rows       = arcpy.UpdateCursor(parcels_old)
    other_geom = [row.Shape for row in arcpy.SearchCursor(tazar_border+"_diss_tmp")][0]
    for row in rows:
                    old_geom = row.Shape
                    new_geom = old_geom.difference(other_geom)   
                    if abs(old_geom.area - new_geom.area) > 0.0001 and new_geom.area > 0.0001:
                            row.Shape = new_geom
                            row.UPDATE_CODE = "U"
                            if abs(old_geom.area - row.Shape.area) < 0.0001:
                                    row.Shape = old_geom
                                    row.UPDATE_CODE = "P"
                                    
                    if new_geom.isMultipart == True and row.SHAPE_Area  / ( row.LEGAL_AREA / 100) > 20:
                        area = 0
                        IsBigPolygon = False
                        for part in new_geom:
                                #print arcpy.Polygon(part).area
                                if arcpy.Polygon(part).area > area:
                                        area = arcpy.Polygon(part).area
                                        big_polygon = arcpy.Polygon(part)
                                        IsBigPolygon = True
                        if IsBigPolygon:
                            row.Shape       = big_polygon
                            row.UPDATE_CODE = "U"
                            small_array     = arcpy.Array()
                            cnt             = 0
                            for i in new_geom:
                                if arcpy.Polygon(i).area < big_polygon.area:
                                    small_array.append(i)
                            if len(small_array) > 0:
                                small_polygons     = arcpy.Polygon(small_array)
                                in_rows            = arcpy.InsertCursor(parcels_old)
                                in_row             = in_rows.newRow()
                                in_row.Shape       = small_polygons
                                in_row.UPDATE_CODE = "U"
                                in_row.PARCEL      = row.PARCEL
                                in_row.GUSH_NUM    = row.GUSH_NUM
                                in_row.LEGAL_AREA  = row.LEGAL_AREA
                                in_rows.insertRow(in_row)

                    
                    rows.updateRow(row)
    arcpy.Delete_management(tazar_border+"_diss_tmp")

    # calculate small ovelaps as "D"
    arcpy.MakeFeatureLayer_management       (parcels_old, "old_lyr", "\"UPDATE_CODE\" ='U'")
    arcpy.AddField_management               (parcels_old, "OVERLAP_PRCT", "DOUBLE")
    arcpy.CalculateField_management         ("old_lyr", "OVERLAP_PRCT", "!SHAPE_Area!  / ( !LEGAL_AREA! / 100)", "PYTHON")
    arcpy.SelectLayerByAttribute_management ("old_lyr", "NEW_SELECTION", "\"OVERLAP_PRCT\" < 20")
    arcpy.CalculateField_management         ("old_lyr", "UPDATE_CODE", "\"D\"", "VB")

    # export parcels to keep (outside the border fix_slivers/ ring / govlim)
    arcpy.CopyFeatures_management           ("old_lyr",gdb + "\\PARCEL_ALL_slivers")

    return parcels_old,tazar_border

def Fix_fields(layer,gdb,sett = ''):
    
    copy_tazar = gdb + '\\' + '_Copy'
    arcpy.CopyFeatures_management    (layer,copy_tazar)
    needed_fields = [['PARCEL_ID','DOUBLE'] , ['GUSH_NUM','LONG'],['PARCEL','SHORT'],['GUSH_SUFFIX','SHORT'],['PARCEL','SHORT'],['LEGAL_AREA','DOUBLE']]

    for i in needed_fields:
        arcpy.AddField_management(copy_tazar,i[0], i[1])

    arcpy.CalculateField_management  (copy_tazar, 'GUSH_NUM', "[GUSHNUM]", "VB", ""      )
    arcpy.CalculateField_management  (copy_tazar, 'GUSH_SUFFIX', "[GUSHSUFFIX]", "VB", "")
    arcpy.CalculateField_management  (copy_tazar, 'LEGAL_AREA', "[LEGALAREA]", "VB", ""  )
    arcpy.CalculateField_management  (copy_tazar, 'LEGAL_AREA', "[LEGAL_AREA] * 1000", "VB", ""  )
    None_me = [i for i in arcpy.SearchCursor(copy_tazar) if i.PARCEL_FINAL == None]
    if None_me:
        arcpy.CalculateField_management  (copy_tazar, 'PARCEL', "int( ''.join ([i for i in !PARCELNAME! if i.isdigit()]))", "PYTHON" ) 
    else:
        arcpy.CalculateField_management  (copy_tazar, 'PARCEL','[PARCEL_FINAL]',"VB","") 

    connect_parcel_to_sett           (copy_tazar,sett)

    return copy_tazar


def topology_basic(final):
        
    gdb    = os.path.dirname(final)
    memory = r'in_memory'
    arcpy.Dissolve_management                 (final,memory + '\\'+ 'dissolve')
    Feature_to_polygon                        (memory + '\\'+ 'dissolve',memory + '\\'+'Feature_to_poly')
    Delete_polygons                           (memory + '\\'+'Feature_to_poly',memory + '\\'+ 'dissolve',gdb + '\\'+'Topolgy_Check_holes')
    count = int(str(arcpy.GetCount_management (gdb + '\\'+'Topolgy_Check_holes'))) 

    over_lap       = arcpy.Intersect_analysis([final],gdb + '\\'+'Topolgy_Check_intersect')
    over_lap_count = int(str(arcpy.GetCount_management (over_lap)))
        
    print_arcpy_message ("there is {} Overlaps".format(str(over_lap_count))) 
    print_arcpy_message ("there is {} holes".format(str(count)))

    return over_lap_count,count


def CheckResultsIsOK(parcel_all,copy_tazar,curves,gdb,num):
    Out_put = gdb + '\\' + 'Check'+'_'+str(num)
    Update_polygons                   (parcel_all,copy_tazar,Out_put,copy_tazar,curves)
    arcpy.MakeFeatureLayer_management (Out_put, "Out_put_lyr", "\"UPDATE_CODE\" = 'D'")
    arcpy.DeleteFeatures_management   ("Out_put_lyr")
    ver_lap_count,count = topology_basic  (Out_put)
    if (ver_lap_count == 0) and (count == 0):
        return True
    else:
        return False
    



def fix_holes_in_polygons_by_neer_length(parcel_all_lyr,tazar,GDB,curves):

    print_arcpy_message("START Func: fix holes in polygons by neer length",1)

    path = GDB + '\\' + "path_upd"
    Update_polygons         (parcel_all_lyr,copy_tazar,path,tazar,curves)
    
    in_memory          = r'in_memory' 
    path2              = arcpy.CopyFeatures_management(path,GDB+ '\\' +'PARCEL_ALL_FIX_HOLES')
    FEATURE_TO_POLYGON = in_memory + '\FEATURE_TO_POLYGON'
    slivers            = GDB + '\slivers'
    PARACELS_Only      = in_memory + '\PARACELS_Only'
    line               = GDB + '\Line'
    slivers_Intersect  = GDB + '\slivers_Intersect'


    arcpy.AddField_management        (path2, "KEY_parcel", "LONG")
    arcpy.CalculateField_management  (path2, "KEY_parcel", "[OBJECTID]", "VB", "")
     
    Feature_to_polygon(path2, FEATURE_TO_POLYGON)
    Delete_polygons             (FEATURE_TO_POLYGON, path2, slivers)
        
    number_of_slivers = int(str(arcpy.GetCount_management(slivers)))
    if number_of_slivers > 0:
            print_arcpy_message("there is {} holes, start working to fix them".format(str(number_of_slivers)),status = 1)
    else:
            print_arcpy_message("no holes found".format(str(number_of_slivers)),status = 1)
    
    arcpy.AddField_management        (slivers, "KEY_sliv", "LONG")
    arcpy.CalculateField_management  (slivers, "KEY_sliv", "[OBJECTID]", "VB", "")
    
    Delete_polygons             (path2, tazar, PARACELS_Only)
    
    polygon_to_line   (PARACELS_Only, line)
    
    sliver_feature_layer = GDB + '\\' + 'sliver_feature_layer'
    arcpy.MakeFeatureLayer_management      (slivers, sliver_feature_layer)
    arcpy.SelectLayerByLocation_management (sliver_feature_layer, 'BOUNDARY_TOUCHES', tazar)
    intersect_list = [sliver_feature_layer,line]
    
    arcpy.Intersect_analysis    (intersect_list, slivers_Intersect, "ALL", ".001 Meters", "INPUT")
    
    try:
            data       = [[row[0],row[1],row[2]] for row in arcpy.da.SearchCursor(slivers_Intersect,['KEY_sliv','FID_Line','SHAPE@LENGTH'])]
    except:
            data       = [[row[0],row[1],row[2]] for row in arcpy.da.SearchCursor(slivers_Intersect,['KEY_sliv','KEY_parcel','SHAPE@LENGTH'])]
        
    df         = pd.DataFrame(data,columns= ['KEY_sliv','KEY_parcel_1','SHAPE@LENGTH'])
    df["RANK"] = df.groupby('KEY_sliv')['SHAPE@LENGTH'].rank(method='first',ascending=False)
    df         = df[df['RANK'] == 1]
    
    
    data_to_gis = []
    for row in df.itertuples(index=True, name='Pandas'):
        data_to_gis.append([getattr(row, "KEY_sliv"), getattr(row, "KEY_parcel_1")])
            
    
    arcpy.AddField_management (slivers, "ID_KEY_par", "LONG")
    for data in data_to_gis:
        with arcpy.da.UpdateCursor(slivers,['KEY_sliv','ID_KEY_par']) as cursor:
            for row in cursor:
                if row[0] == data[0]:
                    row[1] = data[1]
                    cursor.updateRow (row)
                    
    x = [[x[0],x[1]] for x in arcpy.da.SearchCursor(slivers,['ID_KEY_par','SHAPE@'])]
    for i in x:
        with arcpy.da.UpdateCursor(path2,['OID@','SHAPE@']) as icursor:
            for row in icursor:
                    if row[0] == i[0]:
                            new = row[1].union(i[1])
                            row[1] = new
                            icursor.updateRow(row)
                            
    arcpy.Delete_management(path)
    arcpy.Delete_management(line)
    arcpy.Delete_management(slivers_Intersect)

def polygon_to_line(fc,layer_new):
    
    ws, fc_name = os.path.split (layer_new)
    s_r = arcpy.Describe (fc).spatialReference

    if arcpy.Exists(layer_new):
        arcpy.Delete_management(layer_new)
        
    line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)
        

    Search = arcpy.da.SearchCursor(fc,"SHAPE@"  )
    insert = arcpy.da.InsertCursor(line,"SHAPE@")


    Get_Line_list = []
    pid = 0
    for row in Search:
        for part in row[0]:
            for pt in part:
                if pt:
                    Get_Line_list.append([pid,pt.X,pt.Y])
                else:
                    pid +=1
        pid +=1

    for i in range(pid):
        points   = [arcpy.Point(n[1],n[2]) for n in Get_Line_list if n[0] == i]
        array    = arcpy.Array(points)
        polyline = arcpy.Polyline(array)
        insert.insertRow([polyline])

    arcpy.RepairGeometry_management(layer_new)


def clean_slivers_by_vertex(PARCEL_ALL,SLIVERS_CLEAN,border,gdb,Dis_search,PARCEL_ALL_lyr):

        tazar_border = 'in_memory\TazarBorderDiss'
        arcpy.Dissolve_management (border,tazar_border)

        print_arcpy_message('START Func: clean slivers by vertex',1)
    
        conn = sqlite3.connect(':memory:')
        c    = conn.cursor()
        c.execute('''CREATE TABLE old_vertices(pnt_num real, x real, y real, xy text, part real, oid real)''')
        c.execute('''CREATE TABLE new_vertices(pnt_num real, x real, y real, xy text, part real, oid real)''')


        c.execute('''CREATE TABLE vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

        c.execute('''CREATE TABLE sliver_vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

        c.execute('''CREATE TABLE border_vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

        arcpy.Select_analysis            (PARCEL_ALL, PARCEL_ALL_lyr,  "\"UPDATE_CODE\" = 'U' or \"UPDATE_CODE\" is NULL or \"UPDATE_CODE\" = 'P'")
        
        arcpy.CopyFeatures_management        (PARCEL_ALL_lyr,gdb + "\\PARCEL_ALL_lyr_COPY_DEL")
        
        VerticesToTable2(PARCEL_ALL_lyr, "vertices",c)
        VerticesToTable2(SLIVERS_CLEAN, "sliver_vertices",c)
        VerticesToTable2(tazar_border, "border_vertices",c)


        parcel_common_vertices = [row for row in c.execute('''SELECT * FROM vertices
                                                                                                 left join sliver_vertices
                                                                                                 on vertices.xy = sliver_vertices.xy
                                                                                                 where  sliver_vertices.xy is not null''')]
                                                                                                
        border_common_vertices = [row for row in c.execute('''SELECT * FROM border_vertices
                                                                                                 left join sliver_vertices
                                                                                                on border_vertices.xy = sliver_vertices.xy
                                                                                                 where  sliver_vertices.xy is not null''')]
                                                                                                 
                
        c.execute('''CREATE TABLE parcel_common_vertices
                                                                    (pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')
                                                                    

        c.execute('''CREATE TABLE border_common_vertices
                                                                    (pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')
                                                                    
        border_common_vertices
        for r in parcel_common_vertices:
                    c.execute("INSERT INTO parcel_common_vertices VALUES ("+str(r[0]) + ","
                                                                     +str(r[1]) + ","
                                                                     +str(r[2]) + ","
                                                                     +"'"+str(r[3])+"',"
                                                                     +str(r[4]) + ","
                                                                     +str(r[5]) + ","
                                                                     +str(r[6]) + ","
                                                                     +str(r[7]) +")")
                                                                     
        for r in border_common_vertices:
                    c.execute("INSERT INTO border_common_vertices VALUES ("+str(r[0]) + ","
                                                                     +str(r[1]) + ","
                                                                     +str(r[2]) + ","
                                                                     +"'"+str(r[3])+"',"
                                                                     +str(r[4]) + ","
                                                                     +str(r[5]) + ","
                                                                     +str(r[6]) + ","
                                                                     +str(r[7]) +")")



        close_vertices = []
        distances = []
        for p in parcel_common_vertices:
                x = p[1]
                y = p[2]
                for b in border_common_vertices:
                        #if b[3] <> p[3]:
                        x2 = b[1]
                        y2 = b[2]
                        dis = math.sqrt(((x-x2)**2)+((y-y2)**2))
                        if dis < Dis_search or (float("{0:.2f}".format(x)) == float("{0:.2f}".format(x2)) and float("{0:.2f}".format(y)) == float("{0:.2f}".format(y2))):
                                close_vertices.append(p[:8] + b[:8])
                                distances.append(dis)
        distance_vertices = zip(close_vertices, distances)
                                        

                                                                           
        rows = arcpy.UpdateCursor(PARCEL_ALL_lyr)
        for row in rows:
                geometry = row.Shape
                oid = row.OBJECTID
                pts = []
                poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
                for part in geometry:
                        for pt in part:
                                if str(type(pt)) <> "<type 'NoneType'>":
                                        num_point = 0
                                        #print str(pt.X) + "--" + str(pt.Y)
                                        this_x = float("{0:.2f}".format(pt.X))
                                        this_y = float("{0:.2f}".format(pt.Y))      
                                        this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[0][1])) == this_x and float("{0:.2f}".format(p[0][2])) == this_y]
                                        if this_vertex:
                                                if this_vertex[0][0][8] == None:
                                                        if this_vertex[0][0][7] < 0.7 and this_vertex[0][0][6] == 1:
                                                            print "pseodo: delete vertex"
                                                        else:
                                                                #print "pseodo, but important: keep the vertex"
                                                                point = pt
                                                                pts.append(point)
                                                # tazar point in buffer
                                                else:
                                                        # check minimum distance
                                                        the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                                        point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                                        pts.append(point)
                                        # point not on sliver: keep the vertex
                                        else:
                                                point = pt
                                                pts.append(point)
                                        if num_point == 0:
                                                first_point = point
                                        num_point = num_point + 1
                polygon = PtsToPolygon(pts)
                if pts[0] <> pts[-1] and first_point:
                        #print "ooops.... - polygon not closed"
                        pts.append(first_point)
                row.Shape       = polygon
                row.UPDATE_CODE = 'U'
                rows.updateRow(row)

        arcpy.Delete_management(gdb + "\\PARCEL_ALL_lyr_COPY_DEL")
        return PARCEL_ALL_lyr
                
def delete_curves_problems(layer,tazar):
    data_tazar  = [str(i[0])+'-'+str(i[1])+'-'+str(i[2]) for i in arcpy.da.SearchCursor(tazar,['GUSH_NUM','GUSH_SUFFIX','PARCEL'])]
    icursor = arcpy.UpdateCursor(layer)
    for raw in icursor:
         geom = raw.shape
         j  = json.loads(geom.JSON)
         if 'curve' in str(j):
             if raw.UPDATE_CODE == 'U':
                 if raw.PARCEL_ID == 0:
                     for i in data_tazar:
                         if str(raw.KEY) == i:
                             icursor.deleteRow(raw)
                             icursor.updateRow(raw)

                             
def fix_over_laps(path,tazar,gdb,tazar_copy,curves,Temp3):

    print_arcpy_message("START Func: fix over laps",1)
        
    in_memory    = r'in_memory' 
    inter        = r'in_memory' + "\\" + "inter"
    layer2_erase = gdb + "\\" + "layer2_erase"
    path2        = gdb + "\\" + "path2"

        # del sliver inside gvol_tochnit
        
    arcpy.Intersect_analysis          ([path], inter)
    Delete_polygons                   (path,inter,layer2_erase)
    delete_curves_problems            (layer2_erase,tazar_copy)

 
    arcpy.CopyFeatures_management(layer2_erase,path2)
    FEATURE_TO_POLYGON = in_memory + '\FEATURE_TO_POLYGON'
    slivers            = gdb + '\slivers_over_lap'
    PARACELS_Only      = in_memory + '\PARACELS_Only'
    line               = gdb + '\Line_overLap'
    slivers_Intersect  = gdb + '\slivers_Intersect_over_lap'

    arcpy.AddField_management        (path2, "KEY_parcel", "LONG")
    arcpy.CalculateField_management  (path2, "KEY_parcel", "[OBJECTID]", "VB", "")
     
    Feature_to_polygon(path2, FEATURE_TO_POLYGON)
    Delete_polygons                  (FEATURE_TO_POLYGON, path2, slivers)
        
    number_of_slivers = int(str(arcpy.GetCount_management(slivers)))
    if number_of_slivers > 0:
        print_arcpy_message("there is {} holes, start working to fix them".format(str(number_of_slivers)),1)
        arcpy.AddField_management        (slivers, "KEY_sliv", "LONG")
        arcpy.CalculateField_management  (slivers, "KEY_sliv", "[OBJECTID]", "VB", "")
        
        Delete_polygons           (path2, tazar, PARACELS_Only)
        
        polygon_to_line   (PARACELS_Only, line)
        
        sliver_feature_layer = gdb + '\\' + 'sliver_feature_layer'
        arcpy.MakeFeatureLayer_management      (slivers, sliver_feature_layer)
        arcpy.SelectLayerByLocation_management (sliver_feature_layer, 'BOUNDARY_TOUCHES', tazar)
        intersect_list = [sliver_feature_layer,line]
        
        arcpy.Intersect_analysis    (intersect_list, slivers_Intersect, "ALL", ".0001 Meters", "INPUT")
        
        try:
                data       = [[row[0],row[1],row[2]] for row in arcpy.da.SearchCursor(slivers_Intersect,['KEY_sliv','FID_Line','SHAPE@LENGTH'])]
        except:
                data       = [[row[0],row[1],row[2]] for row in arcpy.da.SearchCursor(slivers_Intersect,['KEY_sliv','KEY_parcel','SHAPE@LENGTH'])]
                
        df         = pd.DataFrame(data,columns= ['KEY_sliv','KEY_parcel_1','SHAPE@LENGTH'])
        df["RANK"] = df.groupby('KEY_sliv')['SHAPE@LENGTH'].rank(method='first',ascending=False)
        df         = df[df['RANK'] == 1]
        
        
        data_to_gis = []
        for row in df.itertuples(index=True, name='Pandas'):
            data_to_gis.append([getattr(row, "KEY_sliv"), getattr(row, "KEY_parcel_1")])
                
        
        arcpy.AddField_management (slivers, "ID_KEY_par", "LONG")
        for data in data_to_gis:
            with arcpy.da.UpdateCursor(slivers,['KEY_sliv','ID_KEY_par']) as cursor:
                for row in cursor:
                    if row[0] == data[0]:
                        row[1] = data[1]
                        cursor.updateRow (row)
                        
        x = [[x[0],x[1]] for x in arcpy.da.SearchCursor(slivers,['ID_KEY_par','SHAPE@'])]
        for i in x:
            with arcpy.da.UpdateCursor(path2,['OID@','SHAPE@']) as icursor:
                for row in icursor:
                        if row[0] == i[0]:
                                new = row[1].union(i[1])
                                row[1] = new
                                icursor.updateRow(row)
    else:
        print_arcpy_message("there is no overlaps found",1)


    Update_polygons         (path2,tazar_copy,Temp3,tazar,curves)
    update_curves           (Temp3, curves)
    arcpy.Delete_management (layer2_erase)
    arcpy.Delete_management (slivers)
    arcpy.Delete_management (path2)


def clean_pseudo_vertices(polygon_before, border_geom, nodes_pts):
    for part in polygon_before:
        pts_final = []
        pts_trio = []
        deleted = []
        for pt in part:
                if str(type(pt)) <> "<type 'NoneType'>":
                        pts_trio.append([pt.X, pt.Y])
                        if len(pts_trio) == 3:
                            x = pts_trio[1][0]
                            y = pts_trio[1][1]
                            if collinearity(pts_trio[0], pts_trio[1], pts_trio[2]) < 0.9 and [float("{0:.2f}".format(x)), float("{0:.2f}".format(y))] not in nodes_pts and border_geom[0].buffer(0.05).contains(arcpy.Point(x,y)):
                                    #print_arcpy_message("delete vertex",1)
                                    deleted.append([x,y])
                                    #print_arcpy_message([x,y],1)
                            else:
                                pts_final.append(arcpy.Point(x,y))
                            pts_trio = [pts_trio[1], pts_trio[2]]
                        else:
                            pts_final.append(pt)
        if deleted:
            polygon_after = PtsToPolygon(pts_final)
            return polygon_after
        else:
            return polygon_before


def clean_pseudo(parcel_all_fix_hiles, border,copy_tazar,curves,parcel_all2):

    print_arcpy_message("START Func: clean pseudo",1)

    Update_polygons         (parcel_all_fix_hiles,copy_tazar,parcel_all,tazar_border,curves)   
    update_curves           (parcel_all, curves)
    
    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "SHARE_A_LINE_SEGMENT_WITH", border)
        
    node = "in_memory" +'\\'+"node"
    arcpy.CreateFeatureclass_management("in_memory", "node", "POINT", "", "", "",border)
    rows = arcpy.InsertCursor(node)
    border_geom = arcpy.CopyFeatures_management(border, arcpy.Geometry())
    for g in border_geom:
        for part in g:
            for pt in part:
                if pt:
                    row = rows.newRow()
                    row.Shape = pt
                    rows.insertRow(row)
                    

    nodes_pts = [[float("{0:.2f}".format(row.Shape.centroid.X)), float("{0:.2f}".format(row.Shape.centroid.Y))] for row in arcpy.SearchCursor(node)]
    upd_rows = arcpy.UpdateCursor("parcel_all_lyr")
    for upd_row in upd_rows:
        polygon_before = upd_row.Shape
        polygon_after = clean_pseudo_vertices(polygon_before, border_geom, nodes_pts)
        if polygon_after:
            upd_row.Shape = polygon_after
            upd_rows.updateRow(upd_row)

    Update_polygons         (parcel_all,copy_tazar,parcel_all2,tazar_border,curves)
    Fix_curves              (parcel_all2,border,curves)

def make_polygon_to_point(layer):
    
        #arcpy.AddMessage(layer)
        
        wc,name   = os.path.split(layer)
        out_put   = wc + '\\' + name +'_point'
        
        spatial_reference = arcpy.Describe (layer).spatialReference
        ws, fc_name = os.path.split (out_put)
        #arcpy.AddMessage(out_put)
        #arcpy.AddMessage(fc_name)
        #arcpy.AddMessage(ws)
        arcpy.CreateFeatureclass_management (ws, fc_name, 'POINT', spatial_reference=spatial_reference)
        arcpy.AddField_management (out_put, 'GUSH_NUM', 'TEXT')
        arcpy.AddField_management (out_put, 'PARCEL',   'TEXT')
        arcpy.AddField_management (out_put, 'KEY',      'TEXT')
        icursor = arcpy.InsertCursor (out_put)

        with arcpy.da.SearchCursor (layer, ['SHAPE@','GUSH_NUM','PARCEL'])as cursor:
                for row in cursor:
                    geom = row[0]
                    for item in geom:
                        for pt in item:
                            if pt:
                                in_row           = icursor.newRow ()
                                point            = arcpy.Point (pt.X, pt.Y)
                                ptGeometry       = arcpy.PointGeometry (point)
                                in_row.Shape     = ptGeometry
                                in_row.GUSH_NUM  = str (row[1])
                                in_row.PARCEL    = str (row[2])
                                in_row.KEY       = str (row[1]) +'_'+ str(row[2])
                                icursor.insertRow (in_row)

        
                del cursor
        return out_put

def main_new_old_points(old,layer,tazar_border):

        print_arcpy_message("START Func: main new old points",1)
        
        Delete_curves_out_AOI                    (layer,old) 
        orig_pts = os.path.dirname(tazar_border) + '\\' + 'Orig_parcel'
        arcpy.MakeFeatureLayer_management        (old, "old_lyr")
        arcpy.SelectLayerByLocation_management   ("old_lyr", "INTERSECT", tazar_border, "5 Meters")
        arcpy.Select_analysis                    ("old_lyr", orig_pts)
        
        old_point     = make_polygon_to_point(orig_pts)
        out_layer     = make_polygon_to_point(layer)

        return old_point,out_layer

def Best_layer(list1):
    for i in list1:
        try:
            if arcpy.Exists(i):
                return i
        except:
            pass

def layer_data_Old(PARCEL_ALL,PARCEL_ALL_FINAL,out_csv):

    fields = [["GAP", "DOUBLE"],["delta", "DOUBLE"],["Check", "TEXT"]]
    for i in fields:
        add_field(PARCEL_ALL_FINAL,i[0],i[1])
        
    with arcpy.da.UpdateCursor(PARCEL_ALL_FINAL,["LEGAL_AREA","SHAPE_Area","GAP","delta","Check"]) as cursor:
        for row in cursor:
            if row[0]:
                delta  = math_delta_rashum(row[0])
                row[3] = delta
                row[2] = abs(row[1] - row[0])- delta
                row[4] = find_problem(row[0],row[1],delta)
                cursor.updateRow (row)
    del cursor

    print_arcpy_message("START Func: layer data Old",1)

    add_field(PARCEL_ALL,"KEY", "TEXT")
    with arcpy.da.UpdateCursor(PARCEL_ALL,["GUSH_NUM","PARCEL","KEY"]) as cursor:
        for row in cursor:
            row[2] = str(row[0]) + '-' + (str(row[1]))
            cursor.updateRow(row)
                        
    add_field(PARCEL_ALL_FINAL,"KEY", "TEXT")
    with arcpy.da.UpdateCursor(PARCEL_ALL_FINAL,["GUSH_NUM","PARCEL","KEY"]) as cursor:
        for row in cursor:
            row[2] = str(row[0]) + '-' + (str(row[1]))
            cursor.updateRow(row)
        
    x      = [[row[0],row[1],row[2],row[3],row[4],row[5],row[6]] for row in arcpy.da.SearchCursor (PARCEL_ALL,['GUSH_NUM','PARCEL','GUSH_SUFFIX','KEY','SHAPE_Area','LEGAL_AREA','UPDATE_CODE'])]
    df     = pd.DataFrame(data = x , columns  = ["GUSH_NUM","PARCEL",'GUSH_SUFFIX',"KEY","Calculate_Area","Area_rasum","Status"])  
    df_del = df[df['Status'] == 'D']
        
    y                   = [[row[0],row[1],row[2],row[3],row[4],row[5],row[6],math_delta_rashum(row[5]),find_problem(row[5],row[4],math_delta_rashum(row[5])),abs(row[4] - row[5])- math_delta_rashum(row[5])] for row in arcpy.da.SearchCursor (PARCEL_ALL_FINAL,['GUSH_NUM','PARCEL','GUSH_SUFFIX','KEY','SHAPE_Area','LEGAL_AREA','UPDATE_CODE'])]      
    df_y                = pd.DataFrame(data = y , columns  = ['GUSH_NUM','PARCEL','GUSH_SUFFIX',"KEY","Calculate_Area","Area_rasum","Status","delta","Check","GAP"])  
    df_y_UPD            = df_y[df_y['Status'] == 'U']
    
                        
                    
    frames = [df_del,df_y_UPD]
    result = pd.concat(frames)
    result.to_csv(out_csv)
        

    return result

def Get_Attribute_From_near_parcel(parcel_all_final,tazar_copy,sett = ''):
    if sett == '':
        Uni_data = len(list(set([i.LOCALITY_ID for i in arcpy.SearchCursor(parcel_all_final) if i.LOCALITY_ID])))
        if Uni_data == 1:
            print_arcpy_message ("No Sett layer has been given, copying around parcels",1)
            data = [[i.REGION_NAME,i.REGION_ID,i.COUNTY_NAME,i.COUNTY_ID,i.REG_MUN_ID,i.LOCALITY_NAME,i.LOCALITY_ID,i.REG_MUN_NAME,i.WP] for i in arcpy.SearchCursor(parcel_all_final) if i.LOCALITY_ID][0]
            fields = [["REGION_NAME","TEXT"],["REGION_ID","LONG"],["COUNTY_NAME","TEXT"],["COUNTY_ID","LONG"],["REG_MUN_ID","LONG"],["LOCALITY_NAME","TEXT"],["LOCALITY_ID","LONG"],["REG_MUN_NAME","TEXT"],["WP","LONG"]]
            for i in fields:
                add_field(tazar_copy,i[0],i[1])
            with arcpy.da.UpdateCursor(tazar_copy,["REGION_NAME","REGION_ID","COUNTY_NAME","COUNTY_ID","REG_MUN_ID","LOCALITY_NAME","LOCALITY_ID","REG_MUN_NAME","WP"]) as Ucursor:
                for row in Ucursor:
                    row[0] = data[0]
                    row[1] = data[1]
                    row[2] = data[2]
                    row[3] = data[3]
                    row[4] = data[4]
                    row[5] = data[5]
                    row[6] = data[6]
                    row[7] = data[7]
                    row[8] = data[8]
                    Ucursor.updateRow(row)
        else:
            print_arcpy_message ("No Sett layer has been given",2)


def Talar_Num_Year_status(parcel_all_final,tazar_copy,tazar_c,bankal_points_c,tazar_border,Tazar_Points,parcel_all_point):

        print_arcpy_message("START Func: Talar_Num_Year_status",1)

        gdb = os.path.dirname(tazar_border)

        # # # P O L Y G O N # # #

        # הכנסת מספר תל"ר

        # Get Tazar number From Name
        #add_field(tazar_copy,'TALAR_NUMBER','LONG')
        #numb      = os.path.dirname(gdb).split('.')[0]
        #taz_name  = ''.join([i for i in numb if i.isdigit()])

        # get tazar Number from tazar
        taz_name = [i.TALAR_NUM for i in arcpy.SearchCursor(tazar_c)][0]
        
        print_arcpy_message ("{}".format(str(taz_name)),1)
        add_field           (tazar_copy,"TALAR_NUMBER")
        with arcpy.da.UpdateCursor(tazar_copy,['TALAR_NUMBER']) as cursor:
            for row in cursor:
                row[0] = int(taz_name)
                cursor.updateRow(row)

        # הכנסת ישובים לתצר במידה ויש אחידות
        Get_Attribute_From_near_parcel (parcel_all_final,tazar_copy)

        # # # P O I N T S # # #

        # הוספה של שדות לשכבת נקודות תצ"ר

        bankal_points = gdb + '\\' + 'Bankal_point_Copy'
        arcpy.Select_analysis(bankal_points_c,bankal_points)

        li_fields = [["REG_STATUS","LONG"],['X_Y',"TEXT"],["POINT_NAME","TEXT"],
                     ["POINT_MARK","SHORT"],["SOURCE_CODE","SHORT"],["DETAIL_ID","LONG"],["EW_COORD","DOUBLE"],["NS_COORD","DOUBLE"],
                     ["HEIGHT","DOUBLE"],["CONTROL_ID","DOUBLE"],["PARCEL_N_ID","DOUBLE"]]

        addfields = False
        field_PROJ_NO = [i.name for i in arcpy.ListFields(bankal_points) if i.name == "PROJ_NO"]
        if field_PROJ_NO:
            li_fields.append(["PROJ_NO","LONG"])
            li_fields.append(["TASK_NO","FLOAT"])
            addfields = True
        
        for i in li_fields:
            try:
                    arcpy.AddField_management(Tazar_Points,i[0],i[1])
            except:
                    pass
                				
        if addfields:
            fields = ["REG_STATUS","SHAPE@","X_Y","POINT_NAME","POINT_MARK","SOURCE_CODE","DETAIL_ID","EW_COORD","NS_COORD","HEIGHT","CONTROL_ID","PARCEL_N_ID","PROJ_NO","TASK_NO"]
        else:
            fields = ["REG_STATUS","SHAPE@","X_Y","POINT_NAME","POINT_MARK","SOURCE_CODE","DETAIL_ID","EW_COORD","NS_COORD","HEIGHT","CONTROL_ID","PARCEL_N_ID"]
        with arcpy.da.UpdateCursor(Tazar_Points,fields) as Ucursor:
            for row in Ucursor:
                geom = row[1]
                for pt in geom:
                    x_round = round(float(pt.X),2)
                    y_round = round(float(pt.Y),2)
                    row[2] = str(x_round) +'-'+ str(y_round)
                    Ucursor.updateRow(row)

        # חיבור גאומטרי בין נקודות התצ"ר לשכבת נקודות הבנק"ל
    
        arcpy.MakeFeatureLayer_management      (bankal_points,'bankal_points_lyr2')
        arcpy.SelectLayerByLocation_management ('bankal_points_lyr2',"INTERSECT",Tazar_Points,0.01)
        if addfields:
            data   = [[i.REG_STATUS,i.shape,i.POINT_NAME,i.POINT_MARK,i.SOURCE_CODE,i.DETAIL_ID,i.EW_COORD,i.NS_COORD,i.HEIGHT,i.CONTROL_ID,i.PARCEL_N_ID,i.PROJ_NO,i.TASK_NO] for i in arcpy.SearchCursor('bankal_points_lyr2')]
        else:
            data   = [[i.REG_STATUS,i.shape,i.POINT_NAME,i.POINT_MARK,i.SOURCE_CODE,i.DETAIL_ID,i.EW_COORD,i.NS_COORD,i.HEIGHT,i.CONTROL_ID,i.PARCEL_N_ID] for i in arcpy.SearchCursor('bankal_points_lyr2')]

        with arcpy.da.UpdateCursor(Tazar_Points,fields) as cursor2:
                for row in cursor2:
                        geom = row[1]
                        for n in data:
                                midpnt = n[1].labelPoint
                                if geom.distanceTo(arcpy.Point(midpnt.X,midpnt.Y)) < 0.003:
                                    if n[2] != None:
                                        row[3]  = n[2]
                                    row[0]  = n[0]
                                    row[4]  = n[3]
                                    row[5]  = n[4]
                                    row[6]  = n[5]
                                    row[7]  = n[6]
                                    row[8]  = n[7]
                                    row[9]  = n[8]
                                    row[10] = n[9]
                                    row[11] = n[10]
                                    if addfields:
                                        row[12] = n[11]
                                        row[13] = n[12]

                                    cursor2.updateRow(row)
                                                                                        
                del cursor2


        # מחיקת כל הנקודות בבנקל קופי שבתוך התצ"ר
        arcpy.MakeFeatureLayer_management     (bankal_points,'bankal_points_lyr')
        arcpy.SelectLayerByLocation_management('bankal_points_lyr',"INTERSECT",tazar_border,0.01)
        arcpy.DeleteFeatures_management       ('bankal_points_lyr')
        arcpy.Append_management               (Tazar_Points,bankal_points,"NO_TEST")



        # מחיקת הנקודות בבנק"ל קופי שלא יושבים על החלקות הסופיות (אחרי התיקון הגאומטרי)

        
        lines_all = [str(round(pt.X,2)) + '-' + str(round(pt.Y,2)) for row in arcpy.SearchCursor(parcel_all_final) for part in row.shape for pt in part if pt]

        with arcpy.da.UpdateCursor(bankal_points,['SHAPE@']) as cursor3:
                for row in cursor3:
                        key = str(round(row[0].centroid.X,2)) +'-'+ str(round(row[0].centroid.Y,2))
                        if key not in data:
                                cursor3.deleteRow()


        # הוספה של וורטקסים שיצאו מהחלקות לאחר השינוי הגאומטרי לשכבת הנקודות המעודכנת
        arcpy.MakeFeatureLayer_management      (parcel_all_point,'parcel_all_point_lyr')
        arcpy.SelectLayerByLocation_management ('parcel_all_point_lyr',"INTERSECT",bankal_points,0.01)
        arcpy.DeleteFeatures_management        ('parcel_all_point_lyr')
        arcpy.Append_management                (parcel_all_point,bankal_points,"NO_TEST")

        # מחיקת כפילויות אם יש
        add_field                 (bankal_points,'X_Y','TEXT')
        with arcpy.da.UpdateCursor(bankal_points,['SHAPE@','X_Y']) as Ucursor:
            for row in Ucursor:
                geom = row[0]
                for pt in geom:
                    x_round = round(float(pt.X),2)
                    y_round = round(float(pt.Y),2)
                    row[1] = str(x_round) +'-'+ str(y_round)
                    Ucursor.updateRow(row)
                    
        del_identical   (bankal_points,'X_Y')

        arcpy.Delete_management(parcel_all_point)


        
def PtsToLine(pts):
    array = arcpy.Array()
    for pt in pts:    
        array.add(pt)
    polyline = arcpy.Polyline(array)
    #array.removeAll()
    return polyline


def Create_PARCEL_ARC(PARCEL_ARC_lyr, old_pts_names, PARCEL_ALL_FINAL, border_tazar, tazar,curves,arc):

    print_arcpy_message("START Func: Create PARCEL ARC",1)

    gdb = os.path.dirname(border_tazar)

    Line_Orig   = gdb + '\\'+ 'Line_Orig'
    arcpy.Intersect_analysis    ([PARCEL_ALL_FINAL,PARCEL_ARC_lyr],Line_Orig,"ALL") # just to see what was before

    Line_Final = gdb + "\\Line_Final_by_points"
    arcpy.Select_analysis(PARCEL_ARC_lyr, Line_Final, "\"OBJECTID\" < 0")

    oldpts = []
    rows = arcpy.SearchCursor(old_pts_names)
    for row in rows:
        oldpts.append([float("{0:.1f}".format(row.Shape.centroid.X)), float("{0:.1f}".format(row.Shape.centroid.Y))])

    newlines = []

    def geometryInList(geom ,geom_list):
        results = [g for g in geom_list  if float("{0:.2f}".format((g.intersect(geom, 2)).length)) ==  float("{0:.2f}".format(geom.length))]   
        if len(results) > 0:
            return True
        else:
            return False
        
    rows = arcpy.SearchCursor(PARCEL_ALL_FINAL)
    in_rows = arcpy.InsertCursor(Line_Final)
    for row in rows:
        polygon = row.Shape
        #print row.OBJECTID
        for part in polygon:
            li = []
            for pt in part:
                li.append(pt)
            count = 0
            temp = []
            isVertex = False
            for p in li:
                if count < len(li) - 1:
                    try:
                        pt1 = arcpy.Point(li[count].X, li[count].Y)
                        pt2 = arcpy.Point(li[count + 1].X, li[count + 1].Y)
                        pid = [float("{0:.1f}".format(pt2.X)), float("{0:.1f}".format(pt2.Y))]
                    except:
                        pass

                    # get length
                    #length = arcpy.PointGeometry(pt1).distanceTo(arcpy.PointGeometry(pt2))
                    #if length < 2:
                    if pid not in oldpts:
                        isVertex = True
                        temp.append(pt1)
                    #elif length >= 2 and isVertex == True:
                    elif pid in oldpts and isVertex == True:
                        #print "isVertex == True"
                        
                        temp.append(pt1)
                        temp.append(pt2)
                        line = PtsToLine(temp)
                        
                        if not geometryInList(line ,newlines):
                            #in_rows = arcpy.InsertCursor(Line_Final)
                            in_row = in_rows.newRow()
                            in_row.Shape = line
                            in_rows.insertRow(in_row)

                            newlines.append(line)
    
                        temp = []
                        isVertex = False
                    else:  
                        line = PtsPairToLine(pt1, pt2)
                        if not geometryInList(line ,newlines):
                            #in_rows = arcpy.InsertCursor(Line_Final)
                            in_row = in_rows.newRow()
                            in_row.Shape = line
                            in_rows.insertRow(in_row)
                            
                            newlines.append(line)

                    count = count + 1
                else:
                    if pt2 <> li[-1]:
                        line = PtsPairToLine(pt1, li[-1])
                        if not geometryInList(line ,newlines):
                            #in_rows = arcpy.InsertCursor(Line_Final)
                            in_row = in_rows.newRow()
                            in_row.Shape = line
                            in_rows.insertRow(in_row)

                            newlines.append(line)

    fix_tolerance_line               (Line_Final,gdb + "\\" + "tazar_border")
    arcpy.MakeFeatureLayer_management(Line_Final, "Line_Final_lyr")
    rows = arcpy.SearchCursor(Line_Orig, "\"DISTANCE\" <> ' '")
    for row in rows:
        geom      = row.Shape
        distance  = row.DISTANCE
        angle     = row.ANGLE
        radius    = row.RADIUS
        tangent   = row.TANGENT
        arclength = row.ARCLENGTH
        side      = row.SIDE
        mlength   = row.MLENGTH
        settle_b  = row.SETTLE_B
        reg_mun   = row.REG_MUN
        arcpy.SelectLayerByLocation_management("Line_Final_lyr", "SHARE_A_LINE_SEGMENT_WITH", geom) # OR// SHARE_A_LINE_SEGMENT_WITH
        if int(arcpy.GetCount_management("Line_Final_lyr").getOutput(0)) > 0:
            upd_rows = arcpy.UpdateCursor("Line_Final_lyr")
            for updrow in upd_rows:
                updrow.DISTANCE  = distance
                updrow.ANGLE     = angle
                updrow.RADIUS    = radius
                updrow.TANGENT   = tangent
                updrow.ARCLENGTH = arclength
                updrow.SIDE      = side
                updrow.MLENGTH   = mlength
                updrow.SETTLE_B  = settle_b
                updrow.reg_mun   = reg_mun
                upd_rows.updateRow(updrow)
    

    del_fe       = [row.shape for row in arcpy.SearchCursor(border_tazar)][0]
    upd_cursor   = arcpy.UpdateCursor(Line_Final)
    for upd_row in upd_cursor:
        geom          =  upd_row.shape
        new_geom      = geom.difference(del_fe)
        upd_row.shape = new_geom
        upd_cursor.updateRow(upd_row)
        
    del upd_cursor

    with arcpy.da.SearchCursor(arc,'SHAPE@')as cursor:
        for row in cursor:
            geom = row[0]
            in_rows      = arcpy.InsertCursor(Line_Final)
            in_row       = in_rows.newRow()
            in_row.Shape = geom
            in_rows.insertRow(in_row)

    arcpy.RepairGeometry_management(Line_Final)

    arcpy.MakeFeatureLayer_management(Line_Final,"line_final_lyr")

    Temp_curves = r'in_memory' + '\\' + 'Temp_curves'
    Delete_polygons(curves,border_tazar,Temp_curves) 
    arcpy.SelectLayerByLocation_management("line_final_lyr","SHARE_A_LINE_SEGMENT_WITH",Temp_curves)
    cursor = arcpy.UpdateCursor("line_final_lyr")
    for row in cursor:
        geom = row.Shape
        j = json.loads(geom.JSON)
        if 'curve' in str(j):
            pass
        else:
            cursor.deleteRow(row)

    arcpy.Delete_management(old_pts_names)

def Delete_layers_after_use(layers):
        for i in layers:
                        try:
                                arcpy.Delete_management (i)
                        except:
                            pass 


def math_delta_rashum(area_rashum):
    area_rashum = float(area_rashum)
    delta1 = (0.3 * (math.sqrt(area_rashum)) + (0.005 * area_rashum))
    delta2 = (0.8 * (math.sqrt(area_rashum)) + (0.002 * area_rashum))
    if delta1 > delta2:
        delta = delta1
    else:
        delta = delta2
    return delta
        

def del_line_Not_on_parcels(ARC_bankal,Parcel_makor):

    #  # cuting layer , to work on less data # #

    # # Check Arc points\ID

    dicLine = {str(round(pt.X,1)) + '-' + str(round(pt.Y,1)):row.objectid for row in arcpy.SearchCursor(ARC_bankal) for part in row.shape for pt in part if str(type(pt)) <> 'NoneType'}
    data_p  = [str(round(pts.X,1)) +'-' + str(round(pts.Y,1)) for i in arcpy.SearchCursor(Parcel_makor) for n in i.shape for part in i.shape for pts in part if pts]
    del_line = list(set([i for n,i in dicLine.items()if n not in data_p]))
    
    print_arcpy_message("Deleted arc id: {}".format(del_line),1)
    if del_line:
        arcpy.MakeFeatureLayer_management      (ARC_bankal,'ARC_bankal_lyr')
        arcpy.SelectLayerByAttribute_management('ARC_bankal_lyr',"NEW_SELECTION","\"OBJECTID\" IN ("+str(del_line)[1:-1]+")")
        arcpy.DeleteFeatures_management        ('ARC_bankal_lyr')


def Check_over_lap_after_insert(Parcel_makor,parcel_all_final,tazar_c):
    parcel_makor_copy = Parcel_makor + '_copy'
    arcpy.Select_analysis                  (Parcel_makor, parcel_makor_copy)
    arcpy.Append_management                (parcel_all_final, parcel_makor_copy,"NO_TEST")
    arcpy.Append_management                (tazar_c,parcel_makor_copy,"NO_TEST")

    arcpy.Intersect_analysis               ([parcel_makor_copy],'in_memory\inter_makor')
    if int(str(arcpy.GetCount_management   ('in_memory\inter_makor'))) > 0:
        arcpy.Dissolve_management          ('in_memory\inter_makor','in_memory\Diss')
        Delete_polygons_from_source        (parcel_all_final,'in_memory\Diss')
    return parcel_all_final

def Fix_Double_arc(arc_bankal):

    arc_bankal_int = arc_bankal  + 'arc_bankal_inter'
    arc_diss       = arc_bankal + '_Symmetric_Difference'

    arcpy.Intersect_analysis               ([arc_bankal],arc_bankal_int)
    arcpy.Dissolve_management              (arc_bankal_int,arc_diss)

    if int(str(arcpy.GetCount_management(arc_diss))) > 0:
        data1 = [i.shape for i in arcpy.SearchCursor(arc_diss)][0]

        arcpy.MakeFeatureLayer_management      (arc_bankal,'arc_bankal_lyr')
        arcpy.SelectLayerByLocation_management ('arc_bankal_lyr',"INTERSECT",arc_diss,'10 Meters')

        with arcpy.da.UpdateCursor('arc_bankal_lyr',['SHAPE@']) as cursor:
            for row in cursor:
                geom      = row[0]
                new_geom  = geom.difference(data1)
                row[0]    = new_geom
                cursor.updateRow(row)

        arcpy.Append_management                 (arc_bankal_int,arc_bankal,"NO_TEST")
        arcpy.SelectLayerByAttribute_management ('arc_bankal_lyr',"CLEAR_SELECTION")

    arcpy.Delete_management(arc_diss)
    del arc_bankal_int

def Insert_needed_arc(arc_bankal,parcel_bankal,tazar_c,Keshet):

    Parcel_to_line = parcel_bankal+'_To_line'
    
    arcpy.MakeFeatureLayer_management      (parcel_bankal,'parcel_bankal_lyr')
    arcpy.SelectLayerByLocation_management ('parcel_bankal_lyr',"INTERSECT",tazar_c)
    polygon_to_line                        ('parcel_bankal_lyr',Parcel_to_line)
    arcpy.Dissolve_management              (arc_bankal,arc_bankal +'_Diss')
    data = [i.shape for i in arcpy.SearchCursor(arc_bankal +'_Diss')][0]
    with arcpy.da.UpdateCursor(Parcel_to_line,['SHAPE@']) as cursor:
        for row in cursor:
            geom      = row[0]
            new_geom  = geom.difference(data)
            row[0]    = new_geom
            cursor.updateRow(row)

    Multi_to_single(Parcel_to_line)
    arcpy.MakeFeatureLayer_management      (Parcel_to_line,'par_bankal_to_line_lyr')
    arcpy.SelectLayerByLocation_management ('par_bankal_to_line_lyr',"INTERSECT",Keshet,'0.1 Meters')
    arcpy.DeleteFeatures_management        ('par_bankal_to_line_lyr')
    arcpy.Append_management                (Parcel_to_line,arc_bankal,"NO_TEST")

    arcpy.Delete_management(arc_bankal +'_Diss')
    arcpy.Delete_management(Parcel_to_line)

    Fix_Double_arc                  (arc_bankal)
    arcpy.RepairGeometry_management (arc_bankal)


def Insert_to_Rezaf(Parcel_makor,Parcel_makor_c,parcel_all_final,tazar_c,Point_makor,Point_bantal_c,point_bankal_c_orig,ARC_parcel,ARC_bankal,arc_modad,Keshet,error_line,error_polygon):

    print_arcpy_message("START Func: Insert to Rezaf",1)

    # # # POLYGONS # # #
    arcpy.Copy_management          (parcel_all_final,parcel_all_final+"_b_rezef")
    arcpy.Copy_management          (tazar_c,tazar_c+"_b_rezef")

    # del parcels from makor that have changed
    arcpy.MakeFeatureLayer_management      (Parcel_makor,'Parcel_makor_lyr')
    arcpy.SelectLayerByLocation_management ('Parcel_makor_lyr',"CONTAINS",parcel_all_final)
    arcpy.DeleteFeatures_management        ('Parcel_makor_lyr')
    # making sure the parcel modad are been deleted
    arcpy.MakeFeatureLayer_management       (Parcel_makor,'Parcel_makor_lyr2')
    arcpy.SelectLayerByLocation_management  ('Parcel_makor_lyr2',"INTERSECT",tazar_c)
    arcpy.DeleteFeatures_management         ('Parcel_makor_lyr2')
    arcpy.SelectLayerByAttribute_management ('Parcel_makor_lyr2',"CLEAR_SELECTION")

    del_fea = [str(row[0])+'-'+str(row[1]) for row in arcpy.da.SearchCursor(parcel_all_final,['GUSH_NUM','PARCEL'])]
    arcpy.MakeFeatureLayer_management       (Parcel_makor,'Parcel_makor_lyr3')
    arcpy.SelectLayerByLocation_management  ('Parcel_makor_lyr3',"INTERSECT",parcel_all_final)
    with arcpy.da.UpdateCursor('Parcel_makor_lyr3',['GUSH_NUM','PARCEL']) as Ucurosr:
        for row in Ucurosr:
            key = str(row[0])+'-'+str(row[1])
            if key in del_fea:
                Ucurosr.deleteRow()
    del Ucurosr

    del1  = [i.OBJECTID for i in arcpy.SearchCursor(parcel_all_final) if (i.PARCEL_ID == None) and (i.GUSH_SUFFIX != None)]
    elart = [i.OBJECTID for i in arcpy.SearchCursor(parcel_all_final) if (i.PARCEL_ID == None) and (i.GUSH_SUFFIX == None)]

    if elart:
        print_arcpy_message ('You have GushFix problem',2)

    with arcpy.da.UpdateCursor(parcel_all_final,['OBJECTID']) as Ucurosr2:
        for row in Ucurosr2:
            if row[0] in del1:
                Ucurosr2.deleteRow()
    del Ucurosr2

    arcpy.Dissolve_management         (tazar_c,'in_memory' + '\\' + 'Diss_Layers')
    Delete_polygons_from_source       (parcel_all_final,'in_memory' + '\\' + 'Diss_Layers')

    # Del Overlap from parcel_all_final before append,
    Check_over_lap_after_insert       (Parcel_makor,parcel_all_final,tazar_c)

    arcpy.Append_management           (parcel_all_final,Parcel_makor,"NO_TEST") 
    arcpy.Append_management           (tazar_c,Parcel_makor,"NO_TEST")

    arcpy.SelectLayerByAttribute_management ('Parcel_makor_lyr3',"CLEAR_SELECTION")

    # delete part of curves if out of AOI
    Delete_curves_out_AOI                   (Parcel_makor,Parcel_makor_c)

    # fix holes that are multipart and got D in there type, warning need to be sound
    Fix_Parcels_of_multipart(Parcel_makor_c,Parcel_makor)

    # # # POINTS # # #

    arcpy.MakeFeatureLayer_management     (Point_makor,'Point_makor_lyr')
    arcpy.SelectLayerByLocation_management('Point_makor_lyr',"INTERSECT",parcel_all_final)
    arcpy.DeleteFeatures_management       ('Point_makor_lyr')
    arcpy.Append_management               (Point_bantal_c,Point_makor,"NO_TEST")

    arcpy.MakeFeatureLayer_management     (Point_makor,'Point_makor_lyr2')
    arcpy.SelectLayerByLocation_management('Point_makor_lyr2',"COMPLETELY_WITHIN",tazar_c)
    arcpy.DeleteFeatures_management       ('Point_makor_lyr2')

    # beacuse point_bankal_c has changed, need to bring real copy of point as point_bankal_c_orig
    Del_points_out_AOI                    (Point_makor,point_bankal_c_orig,tazar_c)

    # # # POLYLINE # # #

    # add parcel bankal #
    arcpy.MakeFeatureLayer_management       (ARC_bankal,'ARC_bankal')
    arcpy.SelectLayerByLocation_management  ('ARC_bankal',"INTERSECT",gdb + '\\' +'tazar_border')
    arcpy.DeleteFeatures_management         ('ARC_bankal')

    # add New Parts #
    arcpy.MakeFeatureLayer_management       (ARC_parcel,'ARC_parcel')
    arcpy.SelectLayerByLocation_management  ('ARC_parcel',"SHARE_A_LINE_SEGMENT_WITH",ARC_bankal)
    arcpy.DeleteFeatures_management         ('ARC_parcel')

    arcpy.MakeFeatureLayer_management       (ARC_parcel,'ARC_parcel2')
    arcpy.SelectLayerByLocation_management  ('ARC_parcel2',"SHARE_A_LINE_SEGMENT_WITH",arc_modad)
    arcpy.DeleteFeatures_management         ('ARC_parcel2')
    
    Multi_to_single                        (ARC_parcel)
    arcpy.Append_management                (ARC_parcel,ARC_bankal, "NO_TEST")

    # add arc_modad
    
    arcpy.Append_management                (arc_modad,ARC_bankal, "NO_TEST")

    # delete line that are not needed, "SHARE_A_LINE_SEGMENT_WITH"
    arcpy.MakeFeatureLayer_management       (ARC_bankal,'ARC_parcel3')
    arcpy.SelectLayerByLocation_management  ('ARC_parcel3',"SHARE_A_LINE_SEGMENT_WITH",Parcel_makor,'',"NEW_SELECTION","INVERT")
    arcpy.DeleteFeatures_management         ('ARC_parcel3')

    del_line_Not_on_parcels                 (ARC_bankal,Parcel_makor)

    # Add Arc that deleted for no reason

    Insert_needed_arc                      (ARC_bankal,Parcel_makor,tazar_c,Keshet)

    # Check_Area
    Get_Line_Area                          (ARC_bankal)

    # check Error Lines
    Find_Error_Lines                       (Parcel_makor,ARC_bankal,tazar_c,error_line)

    # delete Duplicate Line 
    Delete_Duplic_Line                     (ARC_bankal)

    # Check Error Polygons
    Find_Error_Polygons                    (Parcel_makor,error_polygon)


def Multi_to_single(layer):

    gdb       = os.path.dirname(layer)
    temp_lyer = gdb +'\\' + 'Temp'
    save_name = os.path.abspath(layer)
    arcpy.MultipartToSinglepart_management (layer,temp_lyer)
    arcpy.Delete_management                (layer)
    arcpy.Rename_management                (temp_lyer,save_name)

    return save_name
    


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
                                geom_up     = row.shape
                                new_geom    = geom_up.difference(geom_del)
                                row.shape = new_geom
                                Ucursor.updateRow (row)


                arcpy.Dissolve_management              (del_layer,diss_layer)
                arcpy.MultipartToSinglepart_management (diss_layer,Append_layer)
                arcpy.Append_management                (Append_layer,fc,"NO_TEST")



def Find_Error_Polygons(Parcel_makor,error_polygon):

    p_gdb = os.path.dirname(Parcel_makor)
    
    holes = p_gdb + '\\' + r'Topolgy_Check_holes'
    inter = p_gdb + '\\' + r'Topolgy_Check_intersect'

    if arcpy.Exists(holes):
        arcpy.Delete_management(holes)

    if arcpy.Exists(inter):
        arcpy.Delete_management(inter)

    add_field(error_polygon,'ERROR_Code')
    with arcpy.da.UpdateCursor(error_polygon,['ERROR_Code']) as cursor:
        for row in cursor:
            if row[0]:
                if row[0] in ["3","4","1"]:
                    print (row[0])
                    cursor.deleteRow()

    topology_basic(Parcel_makor)

    list_del = [i.name for i in arcpy.ListFields(inter) if str(i.name) not in ['SHAPE','OBJECTID','PARCEL','GUSH_NUM','GUSH_SUFFIX','SHAPE_Area','SHAPE_Length','OID']]
    try:
        arcpy.DeleteField_management(inter,list_del)
    except:
        pass


    add_field(holes,"ERROR_TYPE",'TEXT')
    add_field(holes,"ERROR_Code",'TEXT')
    add_field(inter,"ERROR_TYPE",'TEXT')
    add_field(inter,"ERROR_Code",'TEXT')

    arcpy.CalculateField_management(holes,'ERROR_Type', "\"holes\"",'VB')
    arcpy.CalculateField_management(inter,'ERROR_Type', "\"overlap\"",'VB')
    arcpy.CalculateField_management(inter,'ERROR_Code', "\"4\"",'VB')
    arcpy.CalculateField_management(holes,'ERROR_Code', "\"3\"",'VB')

    arcpy.Append_management(inter,error_polygon,"NO_TEST")
    arcpy.Append_management(holes,error_polygon,"NO_TEST")

    #arcpy.MakeFeatureLayer_management(Parcel_makor,"error_polygon_lyr","\"PARCEL\" is null or \"GUSH_NUM\" is null or \"GUSH_SUFFIX\" is null or \"LEGAL_AREA\" is null or \"COUNTY_NAME\" is null or \"TALAR_NUMBER\" is null")

    field_mising = p_gdb + '\\' +'Field_missing'
    #arcpy.CreateFeatureclass_management(p_gdb,'Field_missing',"POLYGON") 

    arcpy.Select_analysis(Parcel_makor,field_mising,"\"PARCEL\" is null or \"GUSH_NUM\" is null or \"GUSH_SUFFIX\" is null or \"LEGAL_AREA\" is null or \"COUNTY_NAME\" is null or \"TALAR_NUMBER\" is null or \"SYS_DATE\" is null")
    add_field(field_mising,"ERROR_TYPE",'TEXT')
    add_field(field_mising,"ERROR_Code",'TEXT')

    arcpy.CalculateField_management(field_mising,'ERROR_Code', "\"1\"",'VB')
    arcpy.CalculateField_management(field_mising,'ERROR_Type', "\"missing values\"",'VB')

    arcpy.Append_management(field_mising,error_polygon,"NO_TEST")

    arcpy.Delete_management(field_mising)


def fix_tolerance_line(layer_path,border):
    dic_point = {}
    Scursor = arcpy.SearchCursor(border)
    for i in Scursor:
        geom = i.Shape
        for part in geom:
            for pt in part:
                if pt:
                    dic_point[str([float('{0:.2f}'.format(pt.X)),float('{0:.2f}'.format(pt.Y))])] = [pt.X,pt.Y]

    Ucursor = arcpy.UpdateCursor(layer_path)
    for i in Ucursor:
        geom = i.Shape
        array = arcpy.Array()
        j = json.loads(geom.JSON)
        if 'curve' not in str(j):
            for part in geom:
                for pt in part:
                    if pt:
                        key = str([float('{0:.2f}'.format(pt.X)),float('{0:.2f}'.format(pt.Y))])
                        if dic_point.has_key(key):
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
       


def del_identical(points,field):
        before = int(str(arcpy.GetCount_management(points)))
        print "there is {} trees before chacking identical".format(str(before))

        data       = [[row[0],row[1]] for row in arcpy.da.SearchCursor(points,["OBJECTID",field])]

                        
        df         = pd.DataFrame(data,columns= ["OBJECTID",field])
        df["RANK"] = df.groupby(field).rank(method='first',ascending=False)
        df         = df[df['RANK'] > 1]
        print df

        data_to_gis = []
        for row in df.itertuples(index=True, name='Pandas'):
                data_to_gis.append([getattr(row, "OBJECTID")])

        flat_list = [item for sublist in data_to_gis for item in sublist]
        
        with arcpy.da.UpdateCursor(points,["OBJECTID"]) as cursor:
                for row in cursor:
                        if int(row[0]) in flat_list:
                                cursor.deleteRow()

        after = int(str(arcpy.GetCount_management(points)))
        deleted = before - after
        print "deleted {} ".format(str(deleted))
        print "total   {} ".format(str(after)) 

                
def find_problem(Area_rasum,Shape_area,delta):
    minus = abs(Area_rasum - Shape_area)
    if minus > delta:
        return 'Warning, Delta is to big'
    else:
        return 'Ok'


def Delete_Layers():

    print_arcpy_message("START Func: Delete Layers",1)
    
    Delete_layers_after_use([gdb + '\\'  + 'PARCEL_ALL_lyr_COPY_DEL',
                             gdb + '\\'  + 'PARCEL_ALL_FIX_HOLES',
                             gdb + '\\'  + 'PARCEL_ALL_2',
                             gdb + '\\'  + 'PARCEL_ALL',
                             gdb + '\\'  + 'PARCEL_ALL_slivers',
                             gdb + '\\'  + 'COPY_TEMP3',
                             gdb + '\\'  + 'PARCEL_ALL_FINAL_1',
                             gdb + '\\'  + 'LINES_inProc_edit_copy',
                             gdb + '\\'  + 'PARCELS_inProc_edit_copy_curves_polygon',
                             gdb + '\\'  + 'PARCELS_inProc_edit_copy',
                             gdb + '\\'  + 'PARCEL_NODE_EDIT_copy',
                             gdb + '\\'  + 'POINTS_inProc_edit_copy',
                             gdb + '\\'  + 'PARCEL_ALL_EDIT_copy',
                             gdb + '\\'  + 'parcel_node',
                             gdb + '\\'  + 'slivers',
                             gdb + '\\'  + 'Orig_parcel_point',
                             gdb + '\\'  + 'Line_Orig',
                             gdb + '\\'  + 'node_tazar',
                             gdb + '\\'  + 'Orig_parcel',
                             gdb + '\\'  + 'curves_cut',
                             gdb + '\\'  + '_Copy',
                             gdb + '\\'  + 'Clean_Pseudo',
                             gdb + '\\'  + 'fix_over_laps',
                             gdb + '\\'  + 'Line_Final_by_points',
                             gdb + '\\'  + 'PARCEL_ARC_EDIT_copy',
                             gdb + '\\'  + 'Check_1', gdb + '\\'  + 'Check_2',gdb + '\\'  + 'Check_3',gdb + '\\'  + 'Check_4'])


    
def get_number_of_points_in_line(ARC_parcel):
    add_field(ARC_parcel,'Num_of_points',Type = 'TEXT')
    cursor = arcpy.UpdateCursor(ARC_parcel)
    dic = {}
    for row in cursor:
        geom = row.shape
        num = 0
        for part in geom:
            for i in part:
                num = num+1
        row.Num_of_points = num
        cursor.updateRow(row)


def Clear_layers(mxd_path,Tazar_Border = 'tazar_border'):
    
    mxd         = arcpy.mapping.MapDocument     (mxd_path)
    df          = arcpy.mapping.ListDataFrames  (mxd)[0]
    ORDER_Layer = arcpy.mapping.ListLayers      (mxd, "", df)
    list_layers = [i.dataSource for i in ORDER_Layer if i.datasetName != Tazar_Border]
    gvol        = [i.dataSource for i in ORDER_Layer if i.datasetName == Tazar_Border][0]

    for layer in list_layers:
        #print_arcpy_message('Remove items from layer: {}'.format(os.path.basename(layer)),status = 1)
        num_before = int(str(arcpy.GetCount_management(layer)))
        
        arcpy.MakeFeatureLayer_management            (layer,'layer_lyr')
        arcpy.SelectLayerByLocation_management       ('layer_lyr',"INTERSECT",gvol,'10 Meters')
        arcpy.SelectLayerByAttribute_management      ('layer_lyr',"SWITCH_SELECTION")
        
        num_after = int(str(arcpy.GetCount_management('layer_lyr')))
        deleted   = num_before - num_after
        #print_arcpy_message                  ('Total Deleted: {}'.format(str(deleted)),status = 1)
        arcpy.arcpy.DeleteFeatures_management('layer_lyr')


def Check_bigger_area(A,B):
    '''
    Check if the diffrance between 2 layers area,
    input:
        1) layer Feature Class
        2) layer Feature Class
    Out Put:
        1) double 
    '''
    gdb = os.path.dirname(A)
    arcpy.Dissolve_management(A,gdb + '\\' + 'A')
    arcpy.Dissolve_management(B,gdb + '\\' + 'B')
    A = [i.shape.area for i in arcpy.SearchCursor(gdb + '\\' + 'A')][0]
    B = [i.shape.area for i in arcpy.SearchCursor(gdb + '\\' + 'B')][0]
    arcpy.Delete_management (gdb + '\\' + 'A')
    arcpy.Delete_management (gdb + '\\' + 'B')
    C = abs(A - B)
    return C


def Open_mxd(gdb,Folder,mxd_demo = r'\\netapp1\yovav\Psefas\Psefas\TZR\TEMP.mxd',demo_gdb = r"\\netapp1\yovav\Psefas\Psefas\TZR\demo.gdb"):

    print_arcpy_message("START Func: Open mxd",1)
    
    mxd = arcpy.mapping.MapDocument (mxd_demo)
    mxd.findAndReplaceWorkspacePaths(demo_gdb, gdb)
    df           = arcpy.mapping.ListDataFrames(mxd)[0]
    BORDER_Layer = arcpy.mapping.ListLayers(mxd, "", df)[-1]
    df.extent    = BORDER_Layer.getExtent()
    try:
            name_taz  = os.path.basename(gdb).split('.')[0]
            taz_name  = ''.join([i for i in name_taz if i.isdigit()])
            path_mxd  = Folder + "\\PSEFAS_QA"+taz_name+".mxd"
            mxd.saveACopy   (path_mxd)
            arcpy.AddMessage("Open MXD Copy")
            os.startfile    (path_mxd)
    except:
            print_arcpy_message     ("# # #    Coudent make mxd {}, you have already to much mxd open # # #".format(taz_name),status = 1)
            pass
    Clear_layers(path_mxd,Tazar_Border = 'tazar_border')

def number_of_curves(layer):
    num = 0
    for row in arcpy.SearchCursor(layer):
        geom = row.Shape
        j = json.loads(geom.JSON)
        if 'curve' in str(j):
            num +=1
    return num

def CheckIfSkipProcess(PARCEL_ALL_EDIT,PARCELS_inProc_edit,gdb):
    conti = True
    intersect = gdb + '\\' + 'inter'
    name_ID   = 'FID_' + os.path.basename(PARCEL_ALL_EDIT)
    arcpy.Intersect_analysis([PARCEL_ALL_EDIT,PARCELS_inProc_edit],intersect)
    dic      = {i[0]:round(i[1],2) for i in arcpy.da.SearchCursor(intersect,[name_ID,'SHAPE_Area'])}
    list_ref = [[i.OBJECTID,round(i.SHAPE_Area,2)] for i in arcpy.SearchCursor(PARCEL_ALL_EDIT)]
    for n in list_ref:
        if dic.has_key(n[0]):
            if n[1] == dic[n[0]]:
                pass
            else:
                conti = False
    arcpy.Delete_management(intersect)
    return conti

def Delete_polygons_from_source(Out_put,del_layer):

    desc = arcpy.Describe(Out_put)
    
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
                    print "no points in the layer"
            del Ucursor
        del del_layer_temp
                        
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

def Sub_Processing(bankal,modad_c,points,pnt_modad,Lines,line_modad,border,copy_tazar,parcel_all):
    
    def Check_If_Sub_Processing(after_del,bankal):
        No_geo_changes = True
        dic_AREA_ID = {i.PARCEL_ID:i.SHAPE_Area for i in arcpy.SearchCursor(after_del)}
        with arcpy.da.SearchCursor(bankal,['PARCEL_ID','SHAPE@AREA']) as cursor:
            for row in cursor:
                if dic_AREA_ID.has_key(row[0]):
                    changed = abs(row[1] - dic_AREA_ID[row[0]])
                    if changed > 0.1:
                        No_geo_changes = False
                        break
        return No_geo_changes

    after_del  = gdb + '\\' + 'afetr_del'

    if not arcpy.Exists(after_del):
        Delete_polygons (bankal,border,after_del)

    No_geo_changes = Check_If_Sub_Processing(after_del,bankal)
    arcpy.Delete_management (after_del)

    if No_geo_changes:
        print_arcpy_message     ("Sub Processing was acctiveted",status = 1)
        path_before      = gdb + '\\' + 'Copy_bankal'
        arcpy.Select_analysis (bankal,path_before)


        # insert: polygons
        Get_Attribute_From_near_parcel         (parcel_all,modad_c)
        Delete_polygons_from_source            (bankal,border)
        arcpy.Append_management                (modad_c,bankal,"NO_TEST")
        Parcel_data                            (bankal,path_before,copy_tazar)
        NewGushim                              (copy_tazar, bankal,'bankal_lyr')
        Insert_Talar_Number                    (bankal,modad_c)

        # insert: Points
        try:
            Points_data_fix             (pnt_modad,points)
        except:
            print_arcpy_message("CHECK FUNC: 'Points_data_fix'",2)
            
        Delete_polygons_from_source (points,border)
        arcpy.Append_management     (pnt_modad,points,"NO_TEST")

                # מחיקת כפילויות אם יש
        add_field                 (points,'X_Y','TEXT')
        with arcpy.da.UpdateCursor(points,['SHAPE@','X_Y']) as Ucursor:
            for row in Ucursor:
                geom = row[0]
                for pt in geom:
                    x_round = round(float(pt.X),1)
                    y_round = round(float(pt.Y),1)
                    row[1] = str(x_round) +'-'+ str(y_round)
                    Ucursor.updateRow(row)
                    
        del_identical   (points,'X_Y')

        # insert Lines
        
        arcpy.MakeFeatureLayer_management       (Lines,'ARC_lyr')
        arcpy.SelectLayerByLocation_management  ('ARC_lyr','HAVE_THEIR_CENTER_IN',border)
        arcpy.DeleteFeatures_management         ('ARC_lyr')
        arcpy.Append_management                 (line_modad,Lines,"NO_TEST")

        # Delete Duplicate Lines
        Delete_Duplic_Line(Lines)

        print_arcpy_message     ("# # # # # # # F I N I S H # # # # # #",status = 1)
        sys.exit()


def Insert_Talar_Number(bankal,tazar_c):

        #print_arcpy_message("START Func: Talar_Num_Year_status",1)

        arcpy.MakeFeatureLayer_management      (bankal,'Parcal_final')
        arcpy.SelectLayerByLocation_management ('Parcal_final',"INTERSECT",tazar_c,'-0.5 Meters')

        # # # P O L Y G O N # # #

        # הכנסת מספר תל"ר

        # Get Tazar number From Name
        #add_field(parcel_all_final,'TALAR_NUMBER','LONG')
        #numb      = os.path.dirname(gdb).split('.')[0]
        #taz_name  = ''.join([i for i in numb if i.isdigit()])

        # get tazar Number from tazar
        taz_name = [i.TALAR_NUM for i in arcpy.SearchCursor(tazar_c)][0]
        
        print_arcpy_message("{}".format(str(taz_name)),1)
        with arcpy.da.UpdateCursor('Parcal_final',['TALAR_NUMBER']) as cursor:
            for row in cursor:
                row[0] = int(taz_name)
                cursor.updateRow(row)



def Points_data_fix(Tazar_Points,bankal_points):


        # # # P O I N T S # # #

        # הוספה של שדות לשכבת נקודות תצ"ר

        gdb = os.path.dirname  (bankal_points)

        bankal_points_c = gdb + '\\' + 'Bankal_point_Copy'
        arcpy.Select_analysis(bankal_points,bankal_points_c)

        li_fields = [["REG_STATUS","LONG"],['X_Y',"TEXT"],["POINT_NAME","TEXT"],
                     ["POINT_MARK","SHORT"],["SOURCE_CODE","SHORT"],["DETAIL_ID","LONG"],["EW_COORD","DOUBLE"],["NS_COORD","DOUBLE"],
                     ["HEIGHT","DOUBLE"],["CONTROL_ID","DOUBLE"],["PARCEL_N_ID","DOUBLE"]]

        addfields = False
        field_PROJ_NO = [i.name for i in arcpy.ListFields(bankal_points_c) if i.name == "PROJ_NO"]
        if field_PROJ_NO:
            li_fields.append(["PROJ_NO","LONG"])
            li_fields.append(["TASK_NO","FLOAT"])
            addfields = True
        
        for i in li_fields:
            try:
                    arcpy.AddField_management(Tazar_Points,i[0],i[1])
            except:
                    pass
                				
        if addfields:
            fields = ["REG_STATUS","SHAPE@","X_Y","POINT_NAME","POINT_MARK","SOURCE_CODE","DETAIL_ID","EW_COORD","NS_COORD","HEIGHT","CONTROL_ID","PARCEL_N_ID","PROJ_NO","TASK_NO"]
        else:
            fields = ["REG_STATUS","SHAPE@","X_Y","POINT_NAME","POINT_MARK","SOURCE_CODE","DETAIL_ID","EW_COORD","NS_COORD","HEIGHT","CONTROL_ID","PARCEL_N_ID"]
        with arcpy.da.UpdateCursor(Tazar_Points,fields) as Ucursor:
            for row in Ucursor:
                geom = row[1]
                for pt in geom:
                    x_round = round(float(pt.X),2)
                    y_round = round(float(pt.Y),2)
                    row[2] = str(x_round) +'-'+ str(y_round)
                    Ucursor.updateRow(row)

        # חיבור גאומטרי בין נקודות התצ"ר לשכבת נקודות הבנק"ל
    
        arcpy.MakeFeatureLayer_management      (bankal_points_c,'bankal_points_lyr2')
        arcpy.SelectLayerByLocation_management ('bankal_points_lyr2',"INTERSECT",Tazar_Points,0.01)
        if addfields:
            data   = [[i.REG_STATUS,i.shape,i.POINT_NAME,i.POINT_MARK,i.SOURCE_CODE,i.DETAIL_ID,i.EW_COORD,i.NS_COORD,i.HEIGHT,i.CONTROL_ID,i.PARCEL_N_ID,i.PROJ_NO,i.TASK_NO] for i in arcpy.SearchCursor('bankal_points_lyr2')]
        else:
            data   = [[i.REG_STATUS,i.shape,i.POINT_NAME,i.POINT_MARK,i.SOURCE_CODE,i.DETAIL_ID,i.EW_COORD,i.NS_COORD,i.HEIGHT,i.CONTROL_ID,i.PARCEL_N_ID] for i in arcpy.SearchCursor('bankal_points_lyr2')]

        with arcpy.da.UpdateCursor(Tazar_Points,fields) as cursor2:
                for row in cursor2:
                        geom = row[1]
                        for n in data:
                                midpnt = n[1].labelPoint
                                if geom.distanceTo(arcpy.Point(midpnt.X,midpnt.Y)) < 0.003:
                                    if n[2] != None:
                                        row[3]  = n[2]
                                    row[0]  = n[0]
                                    row[4]  = n[3]
                                    row[5]  = n[4]
                                    row[6]  = n[5]
                                    row[7]  = n[6]
                                    row[8]  = n[7]
                                    row[9]  = n[8]
                                    row[10] = n[9]
                                    row[11] = n[10]
                                    if addfields:
                                        row[12] = n[11]
                                        row[13] = n[12]

                                    cursor2.updateRow(row)
                                                                                        
                del cursor2






def add_err_pts_to_mxd(our_gdb, folder, data_source):

    # copy 3 error fcs from data_source (demo.gdb) to our_gdb
    err_fc_names = ["Errors_Line", "Errors_Point", "Errors_Polygon"]
    for err_fc_name in err_fc_names:
        arcpy.DeleteRows_management(data_source + "\\" + err_fc_name)
        arcpy.Copy_management(data_source + "\\" + err_fc_name, our_gdb + "\\" + err_fc_name)
    
    mxd = arcpy.mapping.MapDocument(r"CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
    for root, dir, files in os.walk(folder):
        for file in files:
            print file
            file_full_path  = root + "\\" + file
            if file == "Errors_Line.lyr" or file == "Errors_Point.lyr" or file == "Errors_Polygon.lyr" or file == "Possible_Error_points.lyr" or file == "PARCEL_ALL_EDIT_copy.lyr" or file == "PARCEL_NODE_EDIT_copy.lyr" or file == "PARCEL_ARC_EDIT_copy.lyr":
                addLayer        = arcpy.mapping.Layer(file_full_path)
                arcpy.mapping.AddLayer(df, addLayer, "TOP")
                layer = arcpy.mapping.ListLayers(arcpy.mapping.MapDocument(r"CURRENT"), "", arcpy.mapping.ListDataFrames(mxd, "Layers")[0])[0]
                try:
                    mxd.findAndReplaceWorkspacePaths(data_source, our_gdb)
                except:
                    print "Coudnt replace Data Source"
        arcpy.RefreshActiveView()

def Delete_curves_out_AOI(parcel_new,bankal_old):

    diss_old = r'in_memory' + '\\' + 'Diss_old'
    diss_new = r'in_memory' + '\\' + 'Diss_new'
    lyr_old  = r'in_memory' + '\\' + 'lyr_old'
    lyr_new  = r'in_memory' + '\\' + 'lyr_new'


    arcpy.Dissolve_management    (bankal_old,diss_old)
    arcpy.Dissolve_management    (parcel_new,diss_new)

    Feature_to_polygon           (diss_old,lyr_old)
    Feature_to_polygon           (diss_new,lyr_new)

    Delete_polygons_from_source  (lyr_new,lyr_old)
    Delete_polygons_from_source  (parcel_new,lyr_new)

def Del_points_out_AOI(pnt_New,pnt_Old,parcel_modad):

    Point        = r'in_memory' + '\\' + 'Point'
    Pnt_to_del   = r'in_memory' + '\\' + 'Point_to_delete'

    arcpy.MakeFeatureLayer_management        (pnt_New,'pnt_New_lyr')
    arcpy.SelectLayerByLocation_management   ('pnt_New_lyr','INTERSECT',parcel_modad)
    arcpy.SelectLayerByAttribute_management  ('pnt_New_lyr',"SWITCH_SELECTION")

    arcpy.Select_analysis                    ('pnt_New_lyr',Point)
    arcpy.MakeFeatureLayer_management        (Point,'Point_lyr')
    arcpy.SelectLayerByLocation_management   ('Point_lyr','INTERSECT',pnt_Old)
    arcpy.SelectLayerByAttribute_management  ('Point_lyr',"SWITCH_SELECTION")
    arcpy.Select_analysis                    ('Point_lyr',Pnt_to_del)

    arcpy.MakeFeatureLayer_management        (pnt_New,'pnt_New_lyr2')
    arcpy.SelectLayerByLocation_management   ('pnt_New_lyr2','INTERSECT',Pnt_to_del,0.1)
    arcpy.DeleteFeatures_management          ('pnt_New_lyr2') 


def Insert_to_table(bankal,tazar_copy,GDB):

    arcpy.MakeFeatureLayer_management      (bankal,'bankal_lyr')
    arcpy.SelectLayerByLocation_management ('bankal_lyr','INTERSECT',tazar_copy, '1 Meters')

    None_me = [i for i in arcpy.SearchCursor(tazar_copy) if i.PARCEL_FINAL == None]
    if None_me:
        arcpy.CalculateField_management  (tazar_copy, 'PARCEL_FINAL', "int( ''.join ([i for i in !PARCELNAME! if i.isdigit()]))", "PYTHON" ) 

    new_shamce = False
    try:
        data = [[i.shape,str(i.PARCEL_FINAL)+'-'+str(i.GUSHNUM)+'-'+str(i.GUSHSUFFIX)] for i in arcpy.SearchCursor(tazar_copy)]
    except:
        data = [[i.shape,str(i.PARCEL)+'-'+str(i.GUSH_NUM)+'-'+str(i.GUSH_SUFFIX)] for i in arcpy.SearchCursor(tazar_copy)]
        new_shamce = True

    in_tazar_copy = []
    with arcpy.da.SearchCursor ('bankal_lyr', ['SHAPE@','PARCEL','GUSH_NUM','GUSH_SUFFIX']) as cursor:
        for row in cursor:
            geom   = row[0]
            midpnt = geom.labelPoint
            key    = str(row[1])+'-'+str(row[2])+'-'+str(row[3])
            for i in data:
                if i[0].distanceTo(midpnt) == 0:
                    in_tazar_copy.append([i[1],key])
        del cursor


    data          = [[i.shape,str(i.PARCEL)+'-'+str(i.GUSH_NUM)+'-'+str(i.GUSH_SUFFIX)] for i in arcpy.SearchCursor('bankal_lyr')]
    in_bankal     = []
    fields_parcel = ['SHAPE@','PARCEL_FINAL','GUSHNUM','GUSHSUFFIX']
    if new_shamce == True:
        fields_parcel = ['SHAPE@','PARCEL','GUSH_NUM','GUSH_SUFFIX']

    with arcpy.da.SearchCursor (tazar_copy, fields_parcel) as cursor:
        for row in cursor:
            geom   = row[0]
            midpnt = geom.labelPoint
            key    = str(row[1])+'-'+str(row[2])+'-'+str(row[3])
            for i in data:
                if i[0].distanceTo(midpnt) == 0:
                    in_bankal.append([key,i[1]])
        del cursor


    data1 = [ast.literal_eval(i) for i in list(set([str(i) for i in in_tazar_copy + in_bankal]))]


    path      = GDB
    name1     = 'CANCEL_PARCEL_EDIT'
    full_path = path +'\\'+ name1

    if not arcpy.Exists(full_path):
        arcpy.CreateTable_management(path,name1)

    fields = ['F_PARCEL_NUM','F_GUSH_SUFFIX','T_PARCEL_NUM','T_GUSH_SUFFIX']
    add_field(full_path,"F_GUSH_NUM",'LONG')
    add_field(full_path,"T_GUSH_NUM",'LONG')
    for i in fields:
        add_field(full_path,i,'SHORT')

    for row in data1:
            insert = arcpy.InsertCursor (full_path)
            in_row               = insert.newRow()
            in_row.F_GUSH_NUM    = int(row[1].split('-')[1])
            in_row.F_PARCEL_NUM  = int(row[1].split('-')[0])
            in_row.F_GUSH_SUFFIX = int(row[1].split('-')[2])
            in_row.T_GUSH_NUM    = int(row[0].split('-')[1])
            in_row.T_PARCEL_NUM  = int(row[0].split('-')[0])
            in_row.T_GUSH_SUFFIX = int(row[0].split('-')[2])
            insert.insertRow   (in_row)


def Get_Status_Field(layer):
    data_status = {i.GUSH_NUM:[i.STATUS,i.STATUS_TEXT] for i in arcpy.SearchCursor(layer) if i.GUSH_NUM != None and i.STATUS != None}

    with arcpy.da.UpdateCursor(layer,['GUSH_NUM',"STATUS","STATUS_TEXT"]) as cursor:
        for row in cursor:
            if not row[1]:
                if data_status.has_key(row[0]):
                    row[1] = data_status[row[0]][0]
                    row[2] = data_status[row[0]][1]
                    cursor.updateRow(row)
    del cursor

def Parcel_data(path_after,path_before,copy_tazar):
    
    def Get_Runing_numbers(data1):
        for i in range(len(data1)):
            if data1[i][1] == data1[i-1][1]:
                if data1[i][0]+1 == data1[i-1][0]:
                    print "its ok ,in {} value is equal with: {}".format(data1[i][2],data1[i-1][2])
                else:
                    print "in {} value is not equal with: {}".format(data1[i][2],data1[i-1][2])
            else:
                pass


    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("""CREATE TABLE Before_Table (
                        PARCEL     INTEGER,
                        GUSH_NUM   INTEGER,
                        KEY        text
                        )""")

    c = conn.cursor()
    c.execute("""CREATE TABLE Table_After (
                        PARCEL     INTEGER,
                        GUSH_NUM   INTEGER,
                        KEY        text
                        )""")

    for i in arcpy.SearchCursor(path_before):
        c.execute ("INSERT INTO Before_Table VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM)+"-"+ str(i.GUSH_SUFFIX)+"')")

    for i in arcpy.SearchCursor(path_after):
        c.execute ("INSERT INTO Table_After VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM) +"-"+ str(i.GUSH_SUFFIX)+ "')")


    count_before = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Before_Table group by KEY) t1 WHERE t1.count > 1;''')]
    count_after  = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Table_After group by KEY) t1 WHERE t1.count > 1;''')]

    if count_before:
        msg  =  "Found identical parcels on orig parcels : {}".format(count_before)
        print_arcpy_message(msg, status=2)

    if count_before:
        msg2 = "Found identical parcels on new parcels : {}".format(count_after)
        print_arcpy_message(msg2, status=2)

    #data1 = [row for row in c.execute ('''SELECT * FROM  Before_Table ORDER BY GUSH_NUM DESC, PARCEL DESC;''')]
    #Get_Runing_numbers(data1)

    add_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Table_After A LEFT JOIN Before_Table B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]
    del_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Before_Table A LEFT JOIN Table_After B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]

    gdb = os.path.dirname(path_after)
    Insert_to_table(path_before,copy_tazar,gdb)

    msg2 = "added parcels: {}  ".format(add_parcels)
    msg3 = "Deleted parcels: {}".format(del_parcels)

    print_arcpy_message(msg2, status=1)
    print_arcpy_message(msg3, status=1)

    data = {str(i.PARCEL) +'-' +str(i.GUSH_NUM)+'-'+ str(i.GUSH_SUFFIX):[i.LOCALITY_ID,i.LOCALITY_NAME,i.LEGAL_AREA] for i in arcpy.SearchCursor(copy_tazar)}
    with arcpy.da.UpdateCursor(path_after,['PARCEL','GUSH_NUM','GUSH_SUFFIX','LOCALITY_ID','LOCALITY_NAME','LEGAL_AREA']) as ucursor:
        for row in ucursor:
            key = str(row[0]) +'-' +str(row[1])+'-'+ str(row[2])
            if data.has_key(key):
                row[3] = data[key][0]
                row[4] = data[key][1]
                row[5] = data[key][2]
                ucursor.updateRow(row)
    del ucursor

    # Make Dic:  {GUSH_NUM:[STATUS,STATUS_TEXT]} and copy this values to PARCEL LAYER if with Nulls
    Get_Status_Field(path_after)


def Fix_Parcels_of_multipart(bankal_copy,parcel_bankal):

    gdb = os.path.dirname(bankal_copy)
    Diss_path = gdb + '\\' + 'Diss'
    Diss_new  = gdb  + '\\' + 'New'

    Orig_Holes   = gdb + '\\' + '_Orig_Holes'

    Holes_to_add   = gdb  + '\\' + '_holes_to_add'
    Parcels_to_add = gdb  + '\\' + 'Parcels_to_add'

    arcpy.Dissolve_management               (bankal_copy,Diss_path)
    arcpy.Dissolve_management               (parcel_bankal,Diss_new)

    Feature_to_polygon                      (Diss_path,Orig_Holes)
    Delete_polygons_from_source             (Orig_Holes,Diss_path)

    Feature_to_polygon                      (Diss_new,Holes_to_add)
    Delete_polygons_from_source             (Holes_to_add,Diss_new)

    arcpy.MakeFeatureLayer_management       (Holes_to_add,'Holes_to_add_lyr')
    arcpy.SelectLayerByLocation_management  ('Holes_to_add_lyr','INTERSECT',Orig_Holes)
    arcpy.DeleteFeatures_management         ('Holes_to_add_lyr')

    with arcpy.da.UpdateCursor(Holes_to_add,["SHAPE@AREA"]) as cursor:
        for row in cursor:
            if row[0] < 2:
                cursor.deleteRow()

    if int(str(arcpy.GetCount_management(Holes_to_add))) > 0:
        arcpy.Intersect_analysis  ([Holes_to_add,bankal_copy],Parcels_to_add)
        arcpy.Append_management   (Parcels_to_add,parcel_bankal,"NO_TEST")
        id_new_holes = [str(i.PARCEL) + '-' + str(i.GUSH_NUM) for i in arcpy.SearchCursor(Parcels_to_add)]
        print_arcpy_message ("you have undefind holes at {}".format(id_new_holes))

    arcpy.Delete_management(Diss_path)
    arcpy.Delete_management(Diss_new)
    arcpy.Delete_management(Orig_Holes)
    arcpy.Delete_management(Holes_to_add)
    arcpy.Delete_management(Parcels_to_add)


def Get_Line_Area(Line_Final):
    def calc_fronts_rules(length_bankal,lenght_madod):
        try:
            delta = abs(round(float(length_bankal),2) - round(float(lenght_madod),2))
            if length_bankal >= 50:
                if delta > 10:
                    return "Warining! Check Length, Delta is {}, and max is 10".format(delta)
                else:
                    return "Ok"
            if length_bankal < 50:
                    if delta > 6:
                        return "Warining! Check Length Delta is {}, and max is 6".format(delta)
                    else:
                        return "Ok"
        except:
            pass

    arcpy.AddField_management(Line_Final,"Check","TEXT")
    upd_cursor2   = arcpy.UpdateCursor(Line_Final)
    for upd_row in upd_cursor2:
            geom = upd_row.shape
            if upd_row.DISTANCE != None:
                upd_row.Check = calc_fronts_rules(upd_row.DISTANCE,geom.length)
                upd_cursor2.updateRow(upd_row)

    del upd_cursor2

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


def dis(x1,y1,x2,y2):
    dist = math.sqrt(((x1-x2)**2) + ((y1-y2)**2))
    return dist


def Layer_To_Edge_list(layer):

        add_field(layer,'ERROR_TYPE')
        data = [[row.OBJECTID,pt.X,pt.Y,str(row.ERROR_TYPE)] for row in arcpy.SearchCursor(layer) for part in row.shape for pt in part]

        df            = pd.DataFrame(data,columns=["OBJECTID","X","Y","TYPE"])
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
                                if df_edge[n][3] == df_list[i][3]:
                                        dist = dis(df_edge[n][1],df_edge[n][2],data[i][1],data[i][2])
                                        if dist != 0:
                                                min_list.append(dist)
                                                dict1[dist] = df_list[i]

                if min_list:
                        min_l = min(min_list)
                        new_list.append([df_edge[n][:-1],dict1[min_l][:-1],min_l])
                else:
                        print "part have no match type"


        return new_list


def Delete_By_length(layer,dis=0.2):
    with arcpy.da.UpdateCursor(layer,['SHAPE@LENGTH']) as ucursor:
        for row in ucursor:
            if row[0] < dis:
                ucursor.deleteRow()
    del ucursor

def Connect_Lines(layer,layer_new,min_dis):

        new_list = Layer_To_Edge_list(layer)

        Diss = 'in_memory\Diss_layer'

        ws, fc_name = os.path.split (layer_new)
        s_r         = arcpy.Describe (layer).spatialReference

        if arcpy.Exists(layer_new):
                arcpy.Delete_management(layer_new)

        line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)

        add_field(line,'Type',Type = 'TEXT')

        insert = arcpy.InsertCursor(line)

        for i in range(len(new_list)):
                if new_list[i][2] < min_dis:
                        print new_list[i]
                        points   = [arcpy.Point(new_list[i][0][1],new_list[i][0][2]),arcpy.Point(new_list[i][1][1],new_list[i][1][2])]
                        array    = arcpy.Array(points)
                        polyline = arcpy.Polyline(array)
                        feat     = insert.newRow ()
                        feat.setValue ("Type", new_list[i][0][3])
                        feat.shape    = polyline
                        insert.insertRow(feat)

        arcpy.RepairGeometry_management(layer_new)

        arcpy.Append_management                (layer,layer_new,"NO_TEST")
        arcpy.Dissolve_management              (layer_new,Diss)
        arcpy.MultipartToSinglepart_management (Diss,layer_new)

        Delete_By_length                (layer_new,0.2)
        add_field                       (layer_new,'ERROR_Code')
        add_field                       (layer_new,'ERROR_TYPE')
        arcpy.CalculateField_management (layer_new,'ERROR_TYPE',"\"Proposed Line\"", "VB")
        arcpy.CalculateField_management (layer_new,'ERROR_Code',"\"999\"", "VB")

        return layer_new

def Find_Error_Lines(path,path_ARC,tazar,error_line):

    # temp Layers
    new_point  = gdb + '\\' + 'JunctionsParcels'
    POINT_ARC  = gdb + '\\' + 'Junctions_ARCS'
    New_line   = gdb + '\\' + 'New_Line_Error_lines'
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
        arcpy.SelectLayerByLocation_management ('new_point_lyr','WITHIN_A_DISTANCE',tazar,'100 Meters',"REMOVE_FROM_SELECTION","INVERT")
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

            Connect_Lines           (line,New_line,5)
            arcpy.Append_management (New_line,error_line,"NO_TEST")
            arcpy.Append_management (New_line,path_ARC,"NO_TEST")
            arcpy.Delete_management (New_line)
            print_arcpy_message     ("Tool Found: {} stubbern arcs".format(str(num_found)), status=2)
        else:
            print_arcpy_message("No stubbern arcs found", status=1)

        arcpy.Delete_management(line)



def connect_parcel_to_sett(layer,sett):

    list_fields = [['LOCALITY_ID','LONG'],['LOCALITY_NAME','TEXT']]
    add_op = [add_field(layer,i[0],i[1]) for i in list_fields]

    if sett != '':
        
        arcpy.MakeFeatureLayer_management      (sett,'sett_layer')
        arcpy.SelectLayerByLocation_management ('sett_layer','INTERSECT',layer)
        data = [[i.shape,i.SETL_CODE,i.SETL_NAME] for i in arcpy.SearchCursor('sett_layer')]
        with arcpy.da.UpdateCursor (layer, ['SHAPE@','LOCALITY_ID','LOCALITY_NAME']) as cursor:
            for row in cursor:
                geom   = row[0]
                midpnt = geom.labelPoint
                for i in data:
                    if i[0].distanceTo(midpnt) == 0:
                        row[1] = i[1]
                        row[2] = i[2]
                        cursor.updateRow(row)

        del cursor


def Near_AOI(tazar,bankal):
    '''
    input:
        1) parcel all 
        2) bankal      
    out put:
        1) True\False if near AOI or 1 circal before
        2) New parcel, make buffer of 50 metetrs out AOI area.
    '''

    Near_AOI = False
    gdb = os.path.dirname(tazar)

    bankal_Diss      = gdb         + '\\' + 'Diss'
    bankal_Fix_holes = gdb         + '\\' + 'Fix_holes'
    parcel_by_buffer = gdb         + '\\' + 'TEMP_Parcel'
    intersect        = 'in_memory' + '\\' + 'intersect'
    delete_tazar     = 'in_memory' + '\\' + 'delete_tazar'

    Feature_to_polygon       (bankal,bankal_Fix_holes)
    arcpy.Dissolve_management(bankal_Fix_holes,bankal_Diss)


    arcpy.MakeFeatureLayer_management      (tazar,'tazar_lyr')
    arcpy.SelectLayerByLocation_management ('tazar_lyr',"SHARE_A_LINE_SEGMENT_WITH",bankal_Diss)

    Delete_polygons                        (tazar,bankal_Diss,delete_tazar)

    if (int(str(arcpy.GetCount_management('tazar_lyr'))) > 0) or (int(str(arcpy.GetCount_management(delete_tazar))) > 0):
        arcpy.Buffer_analysis           ('tazar_lyr',parcel_by_buffer,50,'OUTSIDE_ONLY',"FLAT","ALL")
        Delete_polygons_from_source     (parcel_by_buffer,bankal_Diss)
        #arcpy.Append_management         (parcel_by_buffer,parcel_all,"NO_TEST")
        print_arcpy_message             ("תצר נמצא ליד אזור ללא חלקות, יש לשים לב")
        Near_AOI = True

    arcpy.Delete_management(bankal_Diss)
    arcpy.Delete_management(bankal_Fix_holes)
    del intersect
    del delete_tazar

    return Near_AOI


if __name__ == '__main__':


    scriptPath = os.path.abspath(__file__)
    Scripts    = os.path.dirname(scriptPath)
    ToolShare  = os.path.dirname(Scripts)
    Scratch    = ToolShare + "\\Scratch"
    ToolData   = ToolShare + "\\ToolData"
    
    parcels_bankal    =              arcpy.GetParameterAsText(0)
    Folder            =              Scratch
    #open_Mxd_bool     = GetBoolValue(arcpy.GetParameterAsText(2),'Open MXD'  )
    #delete_layers     = GetBoolValue(arcpy.GetParameterAsText(3),'Del layers')
    Dis_search        =              arcpy.GetParameterAsText(1)
    Dis_border_pnts   =              arcpy.GetParameterAsText(2)
    sett              = r''

    print_arcpy_message     ("# # # # # # # S T A R T # # # # # #",status = 1)

    # Read Data from MXD or GDB
    parcel_bankal,arc_bankal,point_bankal,parcel_modad,arc_modad,point_modad = Get_layer_gdb(parcels_bankal)

    if Dis_border_pnts == "1":
        print_arcpy_message("Dis_border_pnts == 1", status = 1)
        Dis_border_pnts = get_default_Snap_border (point_bankal,parcel_modad)

    list_of_layers  = CreateWorkingGDB(parcel_bankal,Folder)

    parcel_bankal_c = list_of_layers[0] # חלקות בנק"ל
    arc_bankal_c    = list_of_layers[1] # חזיתות בנק"ל
    point_bankal_c  = list_of_layers[2] # נקודות מפנה בנק"ל

    parcel_modad_c  = list_of_layers[3] # חלקות תצ"ר
    arc_modad_c     = list_of_layers[4] # חזיתות תצ"ר
    point_modad_c   = list_of_layers[5] # נקודות מפנה תצ"ר

    gdb = os.path.dirname(parcel_bankal_c)

    # Prepare Data
    ChangeFieldNames                          (parcel_modad_c,arc_modad_c,point_modad_c)
    parcel_all,tazar_border = prepare_data    (parcel_modad_c,parcel_bankal_c,gdb,point_bankal_c,point_modad_c)
    curves                  = generateCurves  (parcel_modad_c)
    copy_tazar              = Fix_fields      (parcel_modad_c,gdb,sett)
    #Find_Near_AOI          = Near_AOI        (parcel_modad_c,parcel_bankal_c)

    # Starting Geometry Tools processing

    add_err_pts_to_mxd      (gdb, ToolData + "\\lyr_files", ToolData + "\\demo.gdb")

    conti    = True
    if CheckResultsIsOK(parcel_all,copy_tazar,curves,gdb,1):
        print 'Tazar already fixed'
        conti    = False
        if CheckIfSkipProcess(parcel_bankal_c,parcel_modad_c,gdb):
            print_arcpy_message     ("Exit",status = 1)
            sys.exit(0)

    Sub_Processing  (parcel_bankal,parcel_modad_c,point_bankal,point_modad,arc_bankal,arc_modad,tazar_border,copy_tazar,parcel_all) # checking to Continue without geom changes, only parcalzia

    if conti:
        Snap_border_pnts     (gdb,tazar_border,parcel_all,Dis_border_pnts)
        if CheckResultsIsOK  (parcel_all,copy_tazar,curves,gdb,2):
            conti    = False
            print 'Finished in Snap_border_pnts' 

    if conti:
        clean_slivers_by_vertex (parcel_all,gdb + "\\PARCEL_ALL_slivers",tazar_border,gdb,3,gdb + "\\" + "PARCEL_ALL_2")
        if CheckResultsIsOK     (gdb + "\\" + "PARCEL_ALL_2",copy_tazar,curves,gdb,3):
            conti    = False
            print 'clean_slivers_by_vertex'

    if conti:
        fix_holes_in_polygons_by_neer_length (gdb + "\\" + "PARCEL_ALL_2",tazar_border,gdb,curves)
        Snap_border_pnts                     (gdb,tazar_border,gdb + '\\' +'PARCEL_ALL_FIX_HOLES',0.35)
        if CheckResultsIsOK                  (gdb + '\\' +'PARCEL_ALL_FIX_HOLES',copy_tazar,curves,gdb,4):
            Clean_non_exist_pnts             (gdb,tazar_border,gdb + '\\' + 'Check_4',Dis_search = 2)
            clean_pseudo                     (gdb + '\\' + 'Check_4', tazar_border,copy_tazar,curves,gdb + '\\' + 'Clean_Pseudo')
            conti = False
            print 'fix_holes_in_polygons_by_neer_length'


    best_Check = Best_layer([gdb + '\\' + 'Clean_Pseudo',gdb + '\\' + 'Check_4',gdb + '\\' + 'Check_3',gdb + '\\' + 'Check_2',gdb + '\\' + 'Check_1'])

    fix_over_laps        (best_Check,tazar_border,gdb,copy_tazar,curves,gdb+ '\\' +'fix_over_laps')

    stubborn_parts       (gdb + '\\' +'fix_over_laps',parcel_bankal_c,copy_tazar,curves,gdb + '\\'  + 'PARCEL_ALL_FINAL')

    # Cuntinue Points Vrtx Fixing

    fix_tolerance        (gdb + '\\' + 'PARCEL_ALL_FINAL',gdb + "\\" + "tazar_border",Dis_border_pnts)

    orig_point,New_point = main_new_old_points  (parcel_bankal_c,gdb + '\\' + 'PARCEL_ALL_FINAL',tazar_border)

    possi_error_points   = get_no_node_vertex   (New_point,tazar_border,point_modad_c,orig_point)

    planA                = fix_possible_err_pts (gdb + '\\' + 'PARCEL_ALL_FINAL', tazar_border, possi_error_points,parcel_modad_c,parcel_bankal_c,curves)

    if planA:
        get_no_node_vertex  (New_point,tazar_border,point_modad_c,orig_point)

    # Check Data

    NewGushim               (copy_tazar, parcel_bankal_c,gdb + '\\' + 'PARCEL_ALL_FINAL')

    table = layer_data_Old  (gdb + '\\' + 'PARCEL_ALL',gdb + '\\' + 'PARCEL_ALL_FINAL',os.path.dirname(gdb) + "\\PSEFAS_QA_"+os.path.basename(gdb).split('.')[0]+".csv")

    # Extract Data

    Talar_Num_Year_status   (gdb + '\\' + 'PARCEL_ALL_FINAL',copy_tazar,parcel_modad_c,point_bankal_c,tazar_border,point_modad_c,New_point)
    
    Create_PARCEL_ARC       (arc_bankal_c, gdb +'\\'+ "old_pts_names", gdb + '\\' + 'PARCEL_ALL_FINAL',tazar_border, parcel_modad_c, gdb + '\\' + "curves_cut",arc_modad_c)

    Fix_curves              (gdb + '\\' + 'PARCEL_ALL_FINAL',tazar_border,curves)

    Insert_to_Rezaf         (parcel_bankal,parcel_bankal_c,gdb + '\\' + 'PARCEL_ALL_FINAL',copy_tazar,point_bankal,gdb + '\\' + 'Bankal_point_Copy',point_bankal_c,gdb + '\\' + 'Line_Final_by_points',arc_bankal,arc_modad_c,curves,gdb + '\\' + 'Errors_Line',gdb + '\\' + 'Errors_Polygon')

    Parcel_data             (parcel_bankal,parcel_bankal_c,copy_tazar)

    #Delete_Layers           ()
    
    
    #if open_Mxd_bool:
        #Open_mxd(gdb,Folder)

print_arcpy_message     ("# # # # # # # F I N I S H # # # # # #",status = 1)
