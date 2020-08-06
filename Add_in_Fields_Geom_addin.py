# -*- coding: utf-8 -*-
import arcpy
import pythonaddins
import os
import json

class Fix_Edit(object):
    """Implementation for Add_in_Fields_Geom_addin.Fix_Edit (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
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

        def fix_tolerance(layer_path,border):
            
            gdb         = os.path.dirname(border)
            border_diss = gdb + '\\' + 'border_diss'
            arcpy.Dissolve_management(border,border_diss)

            dic_point = {}
            Scursor = arcpy.SearchCursor(border_diss)
            for i in Scursor:
                geom = i.Shape
                for part in geom:
                    for pt in part:
                        if pt:
                            dic_point[str([float('{0:.0f}'.format(pt.X)),float('{0:.0f}'.format(pt.Y))])] = [pt.X,pt.Y]

            arcpy.Delete_management (gdb + '\\' + 'border_diss')

            Ucursor = arcpy.UpdateCursor(layer_path)
            for i in Ucursor:
                ring = []
                pts = []
                geom = i.Shape
                j = json.loads(geom.JSON)
                if 'curve' not in str(j):
                    for part in geom:
                        counter = 0
                        part1 = []
                        for pt in part:
                            if str(type(pt)) <> "<type 'NoneType'>":
                                if counter == 0:
                                    first_pt = pt
                                key = str([float('{0:.0f}'.format(pt.X)),float('{0:.0f}'.format(pt.Y))])
                                if dic_point.has_key(key):
                                    ring.append([dic_point[key][0],dic_point[key][1]])
                                else:
                                    ring.append([pt.X, pt.Y])
                                counter = counter + 1
                            else:
                                ring.append([first_pt.X, first_pt.Y])
                                ring.append(None)
                                counter = 0

                    pts.append(ring)
                    polygon = PtsToPolygon1(pts)
                    i.Shape = polygon
                    Ucursor.updateRow(i) 
                else:
                    print "Skip curve"
                    pass

        def del_line_Not_on_parcels(ARC_bankal,Parcel_makor):

            dicLine = {str(round(pt.X,2)) + '-' + str(round(pt.Y,2)):row.objectid for row in arcpy.SearchCursor(ARC_bankal) for part in row.shape for pt in part}
            data_p  = [str(round(pts.X,2)) +'-' + str(round(pts.Y,2)) for i in arcpy.SearchCursor(Parcel_makor) for n in i.shape for part in i.shape for pts in part if pts]
            del_line = list(set([i for n,i in dicLine.items()if n not in data_p]))
            
            if del_line:
                arcpy.MakeFeatureLayer_management      (ARC_bankal,'ARC_bankal')
                arcpy.SelectLayerByAttribute_management('ARC_bankal',"NEW_SELECTION","\"OBJECTID\" IN ("+str(del_line)[1:-1]+")")
                arcpy.DeleteFeatures_management        ('ARC_bankal')


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


        def Insert_needed_arc(arc_bankal,parcel_bankal,tazar_c,Keshet):
            arcpy.MakeFeatureLayer_management      (parcel_bankal,'parcel_bankal_lyr')
            arcpy.SelectLayerByLocation_management ('parcel_bankal_lyr',"INTERSECT",tazar_c)
            polygon_to_line                        ('parcel_bankal_lyr',parcel_bankal+'_To_line')
            arcpy.Dissolve_management              (arc_bankal,arc_bankal +'_Diss')
            data = [i.shape for i in arcpy.SearchCursor(arc_bankal +'_Diss')][0]
            with arcpy.da.UpdateCursor(parcel_bankal+'_To_line',['SHAPE@']) as cursor:
                for row in cursor:
                    geom      = row[0]
                    new_geom  = geom.difference(data)
                    row[0]    = new_geom
                    cursor.updateRow(row)

            arcpy.MakeFeatureLayer_management      (parcel_bankal+'_To_line','par_bankal_to_line_lyr')
            arcpy.SelectLayerByLocation_management ('par_bankal_to_line_lyr',"INTERSECT",Keshet,'0.1 Meters')
            arcpy.DeleteFeatures_management        ('par_bankal_to_line_lyr')

            arcpy.Append_management(parcel_bankal+'_To_line',arc_bankal,"NO_TEST")
            arcpy.Delete_management(arc_bankal +'_Diss')
            arcpy.Delete_management(parcel_bankal+'_To_line')

        def Delete_layers_from_MXD(list_layers):
            mxd  = arcpy.mapping.MapDocument    ('current')
            df   = arcpy.mapping.ListDataFrames (mxd, "Layers")[0]
            lyrs = arcpy.mapping.ListLayers     (mxd, '*', df)
            for lyr in lyrs:
                if lyr.isFeatureLayer:
                    if lyr.name in list_layers:
                        try:
                            arcpy.mapping.RemoveLayer(df,lyr)
                        except:
                            pass

            arcpy.RefreshActiveView()
                
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

        def get_no_node_vertex(point,gdb):
            
            old_node     = gdb + '\\' + 'PARCEL_NODE_EDIT_copy'
            tazar_border = gdb + '\\' + 'tazar_border'
            node         = gdb + '\\' + 'POINTS_inProc_edit_copy'

            arcpy.MakeFeatureLayer_management     (gdb + "\\" + "Possible_Error_points",'lyr')
            arcpy.DeleteFeatures_management       ('lyr')  

            arcpy.MakeFeatureLayer_management     (point,"points_lyr")
            arcpy.SelectLayerByLocation_management("points_lyr","BOUNDARY_TOUCHES",tazar_border,0.003)
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",node,0.003,"REMOVE_FROM_SELECTION")
            arcpy.SelectLayerByLocation_management("points_lyr","INTERSECT",old_node,0.003,"REMOVE_FROM_SELECTION")

            arcpy.Append_management               ("points_lyr",gdb + "\\" + "Possible_Error_points","NO_TEST")


        mxd = arcpy.mapping.MapDocument('current')

        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        lyrs = arcpy.mapping.ListLayers (mxd, '*', df)
        dirname = {"Point":'','Line':'','Polygon':'','Border':'','modad_point':''}
        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if str(lyr.datasetName )== "Parcel_node_edit":
                    dirname["Point"] = str(lyr.dataSource)
                if str(lyr.datasetName )== "Parcel_arc_edit":
                    dirname["Line"] = str(lyr.dataSource)
                if str(lyr.datasetName )== "Parcel_all_edit":
                    dirname["Polygon"] = str(lyr.dataSource)
                if str(lyr.datasetName )== "Parcels_inProc_edit":
                    dirname["Border"] = str(lyr.dataSource)
                if str(lyr.datasetName )== "PARCEL_ALL_EDIT_copy":
                    dirname["gdb"] = str(os.path.dirname(lyr.dataSource))
                if str(lyr.datasetName )== "Points_inProc_edit":
                    dirname["modad_point"] = str(os.path.dirname(lyr.dataSource))
                    
        fix_tolerance(dirname["Polygon"], dirname["Border"])

        arcpy.MakeFeatureLayer_management       (dirname["Line"],'ARC_parcel3')
        arcpy.SelectLayerByLocation_management  ('ARC_parcel3',"SHARE_A_LINE_SEGMENT_WITH",dirname["Polygon"],'',"NEW_SELECTION","INVERT")
        arcpy.DeleteFeatures_management         ('ARC_parcel3')

        del_line_Not_on_parcels                 (dirname["Line"],dirname["Polygon"])

        pnt_new = make_polygon_to_point         (dirname["Polygon"])
        arcpy.Select_analysis(pnt_new,pnt_new +'_copy')

        arcpy.MakeFeatureLayer_management       (dirname["Point"],'Point_lyr')
        arcpy.SelectLayerByLocation_management  ('Point_lyr','INTERSECT',pnt_new,'',"NEW_SELECTION","INVERT")

        arcpy.DeleteFeatures_management         ('Point_lyr')

        keshet = dirname["gdb"] + '\\'+ 'PARCELS_inProc_edit_copy_curves_polygon'
        Insert_needed_arc(dirname["Line"],dirname["Polygon"],dirname["Border"],keshet)

        get_no_node_vertex(pnt_new +'_copy',dirname["gdb"])
        
        list_layers = ["ARC_bankal","Point_lyr","parcel_bankal_lyr","border_diss","Parcel_arc_edit",
        "par_bankal_to_line_lyr","Parcel_arc_edit_Diss","Parcel_all_edit_To_line","ARC_parcel3",
        "Parcel_all_edit_point","Parcel_all_edit_point_copy","lyr","points_lyr"]
        
        Delete_layers_from_MXD(list_layers)
        
        arcpy.RefreshActiveView()

class Restore_Parcel(object):
    """Implementation for Add_in_Fields_Geom_addin.Restore_Parcel (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        def add_field(fc,field,Type = 'TEXT'):
            TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
            if not TYPE:
                arcpy.AddField_management (fc, field, Type)

        mxd = arcpy.mapping.MapDocument('current')
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        lyrs = arcpy.mapping.ListLayers (mxd, '*', df)
        dirname = {"FINAL":[],'ORIG':[]}
        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if str(lyr.datasetName )== "Parcel_all_edit":
                    dirname["FINAL"].append('חלקות לעריכה')
                if str(lyr.datasetName )== "PARCEL_ALL_EDIT_copy":
                    dirname["ORIG"].append('חלקות בנק"ל מקור')
        
        try:
            list1 = []
            add_field(dirname["FINAL"][0],'KEY',Type = 'TEXT')
            with arcpy.da.UpdateCursor(dirname["FINAL"][0],['GUSH_NUM','GUSH_SUFFIX','PARCEL','KEY']) as Scursor:
                for row in Scursor:
                    KEY = str(row[0]) +'-'+ str(row[1]) +'-'+ str(row[2])
                    row[3] = KEY
                    Scursor.updateRow(row)
                    list1.append(KEY)
            print list1

            if len(list1) < 8:
                add_field(dirname["ORIG"][0],'KEY',Type = 'TEXT')
                with arcpy.da.UpdateCursor(dirname["ORIG"][0],['GUSH_NUM','GUSH_SUFFIX','PARCEL','KEY']) as cursor:
                    for row in cursor:
                        row[3] = str(row[0]) +'-'+ str(row[1]) +'-'+ str(row[2])
                        cursor.updateRow(row)

                dic1 = {str(i.KEY):i.shape for i in arcpy.SearchCursor(dirname["ORIG"][0]) if str(i.KEY) in list1}

                with arcpy.da.UpdateCursor(dirname["FINAL"][0],["SHAPE@","KEY"]) as cursor1:
                    for row in cursor1:
                        if dic1.has_key(str(row[1])):
                            row[0] = dic1[str(row[1])]
                            cursor1.updateRow (row)

                print dic1

            else:
                pythonaddins.MessageBox ("plz choose less features for update", 'INFO', 0)
                            
            arcpy.RefreshActiveView()
        except:
            print "Didnt Find layers"

class UpdateGeometry(object):
    """Implementation for Add_in_Fields_Geom_addin.UpdateGeometry (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        
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
                                
                                                                

        def topology_basic(final):

            no_holes     = False
            no_intersect = False
            
            gdb    = os.path.dirname(final)
            memory = r'in_memory'
            arcpy.Dissolve_management                 (final,memory + '\\'+ 'dissolve')
            Feature_to_polygon                        (memory + '\\'+ 'dissolve',memory + '\\'+'Feature_to_poly')
            if arcpy.Exists(gdb + '\\'+'Topolgy_Check_holes'):
                arcpy.Delete_management(gdb + '\\'+'Topolgy_Check_holes')
            Delete_polygons                           (memory + '\\'+'Feature_to_poly',memory + '\\'+ 'dissolve',gdb + '\\'+'Topolgy_Check_holes')
            count = int(str(arcpy.GetCount_management (gdb + '\\'+'Topolgy_Check_holes')))
            if count == 0:
                arcpy.Delete_management(gdb + '\\'+'Topolgy_Check_holes')
                pythonaddins.MessageBox('all ok, no holes in layer','INFO',0)
                no_holes = True
                

            if arcpy.Exists(gdb + '\\'+'Topolgy_Check_intersect'):
                arcpy.Delete_management(gdb + '\\'+'Topolgy_Check_intersect')
                
            over_lap       = arcpy.Intersect_analysis(final,gdb + '\\'+'Topolgy_Check_intersect')
            over_lap_count = int(str(arcpy.GetCount_management (over_lap)))
            if over_lap_count == 0:
                arcpy.Delete_management(gdb + '\\'+'Topolgy_Check_intersect')
                pythonaddins.MessageBox('all ok, no intersect in layer','INFO',0)
                no_intersect = True

            arcpy.Delete_management(memory + '\\'+ 'dissolve')
            arcpy.Delete_management(memory + '\\'+ 'Feature_to_poly')
            arcpy.Delete_management(memory + '\\'+ 'dissolve_temp')

            return count,over_lap_count


        mxd = arcpy.mapping.MapDocument('current')
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        print "ok"
        if df:
            lyr = arcpy.mapping.ListLayers(mxd,"חלקות לעריכה", df)[0]
            no_holes,no_intersect = topology_basic(lyr.dataSource)
            List_to_add = [['3','חורים',str(no_holes)],['4','חפיפות',str(no_intersect)]]
            Error_Table                           (os.path.dirname(lyr.dataSource),List_to_add)
            lyrs = arcpy.mapping.ListLayers(mxd,"*", df)
            for lyr in lyrs:
                if lyr.name in ["dissolve","Feature_to_poly", "Dissolve_temp"]:
                    arcpy.mapping.RemoveLayer(df,lyr)
                if no_holes:
                    if lyr.name == 'Topolgy_Check_holes':
                        arcpy.mapping.RemoveLayer(df,lyr)
                if no_intersect:
                    if lyr.name == 'Topolgy_Check_intersect':
                        arcpy.mapping.RemoveLayer(df,lyr)
                        
        arcpy.RefreshActiveView()
