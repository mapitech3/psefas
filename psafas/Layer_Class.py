# -*- coding: utf-8 -*-



try:
    from Basic_Func import *
except:
    pass

import os,arcpy,json
import pandas as pd

arcpy.env.overwriteOutput = True

# # # # # # # # # # # # # # # Basic Fun  # # # # # # # # # # # # # # # 


def add_field(fc,field,Type = 'TEXT'):
    try:
        TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
        if not TYPE:
            arcpy.AddField_management (fc, field, Type, "", "", 500)
    except:
        arcpy.AddField_management (fc, field, Type, "", "", 500)

def del_identical(points,field):

    before = int(str(arcpy.GetCount_management(points)))

    data       = [[row[0],row[1]] for row in arcpy.da.SearchCursor(points,["OBJECTID",field])]

    df         = pd.DataFrame(data,columns= ["OBJECTID",field])
    df["RANK"] = df.groupby(field).rank(method='first',ascending=False)
    df         = df[df['RANK'] > 1]

    data_to_gis = []
    for row in df.itertuples(index=True, name='Pandas'):
            data_to_gis.append([getattr(row, "OBJECTID")])

    flat_list = [item for sublist in data_to_gis for item in sublist]
    

    with arcpy.da.UpdateCursor(points,["OBJECTID"]) as cursor:
            for row in cursor:
                    if int(row[0]) in flat_list:
                            cursor.deleteRow()
    del cursor
                            

    after = int(str(arcpy.GetCount_management(points)))
    deleted = before - after

    return deleted



def Split_List_by_value(list1,value,del_value = False):

    list_index = [n for n,val in enumerate(list1) if val == value]

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


def Feature_to_polygon(path,Out_put):

    path_diss = arcpy.Dissolve_management(path,r'in_memory\path_diss')

    polygon = []
    cursor = arcpy.SearchCursor(path_diss)
    for row in cursor:
        geom = row.shape
        for part in geom:
            num = 0
            for pt in part:
                if str(type(pt)) != "<type 'NoneType'>":
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


# # # # # # # # # # # # # # # Layer Class # # # # # # # # # # # # # # # 

class Layer_Management():

    '''
    1)  Calc_XY
    2)  Select_By_Location
    3)  Multi_to_single
    4)  add_field
    5)  is_Curves
    6)  Erase
    7)  Destroy_layer
    8)  Get_vertxs_As_Point
    9)  None_in_fields
    10) Get_Closest_Distance
    11) Fill_Holes_in_Polygon
    12) Get_Label_Point_As_Point
    13) delete_identical
    '''

    def __init__(self,Layer):
        if arcpy.Exists(Layer):
            self.gdb          = os.path.dirname  (Layer)
            self.name         = os.path.basename (Layer)
            self.layer        = Layer
            self.oid          = str(arcpy.Describe(Layer).OIDFieldName)

            desc = arcpy.Describe(Layer)
            if str(desc.shapeType) == 'Point':
                self.Geom_type = 'Point'
            elif str(desc.shapeType) == 'Polyline':
                self.Geom_type = 'Polyline'
            else:
                self.Geom_type = 'Polygon'
        else:
            print ("Layer is not exist")
            pass

    def Calc_XY(self):
        add_field                       (self.layer,'X_Y','TEXT')
        arcpy.CalculateField_management (self.layer, "X_Y", "calc(!shape.centroid.X!,!shape.centroid.Y!)", "PYTHON_9.3", "def calc (x,y):\\n    return str(round(x,1)) + '-' + str(round(y,1))")
        return 'X_Y'

    def is_Curves(self):
        for row in arcpy.da.SearchCursor(self.layer,['SHAPE@']):
            geom = row[0]
            if geom:
                j    = json.loads(geom.JSON)
                if 'curve' in str(j):
                    return True
                else:
                    return False


    def fields(self):
        return [str(f.name) for f in arcpy.ListFields(self.layer)]

    def len(self):
        return int(str(arcpy.GetCount_management(self.layer)))

    def Get_Field_And_Type(self):
        return {str(f.name):str(f.type) for f in arcpy.ListFields(self.layer)}

    def vertxs_Count(self):
        if self.Geom_type != 'Point':
            return sum([row.objectid for row in arcpy.SearchCursor(self.layer) for part in row.shape for pt in part if pt])

    def  Select_By_Location(self,Connection,ref_layer,distance = 0,New_Layer = None,invert = ''):

        '''
        Connection:
        1) ARE_IDENTICAL_TO 
        2) BOUNDARY_TOUCHES
        3) ARE_IDENTICAL_TO
        4) INTERSECT
        5) HAVE_THEIR_CENTER_IN
        6) WITHIN
        7) WITHIN_A_DISTANCE
        8) COMPLETELY_WITHIN
        9) SHARE_A_LINE_SEGMENT_WITH
        DISTANCE:
        exp: "5 Meters"
        '''
        if invert != '':
            invert = "INVERT"
    
        FeatureLyr   = arcpy.MakeFeatureLayer_management(self.layer,self.name +'_Layer')
        arcpy.SelectLayerByLocation_management  (FeatureLyr,Connection,ref_layer,distance,'',invert)
        if not New_Layer:
            arcpy.DeleteFeatures_management (FeatureLyr)
        else:
            arcpy.Select_analysis           (FeatureLyr,New_Layer)

        if New_Layer:
            return New_Layer


    def Multi_to_single(self,temp_lyer = ''):
        
        temp_lyer = self.gdb + '\\' + 'Temp'
        save_name = self.layer
        arcpy.MultipartToSinglepart_management (self.layer,temp_lyer)
        arcpy.Delete_management                (self.layer)
        arcpy.Rename_management                (temp_lyer,save_name)

        return save_name


    def Erase(self,del_geom,Out_put = ''):

        if self.Geom_type == 'Polygon':
            if Out_put == '':
                Out_put = self.gdb + '\\' + self.name + 'Erased'
            Delete_polygons(self.layer,del_geom,Out_put)

            return Out_put

    def Destroy_layer(self):

        arcpy.Delete_management(self.layer)

    def Generate_Name(self,out_put = '' ,add_name= 'temp'):
        if arcpy.Exists(out_put):
            arcpy.Delete_management(out_put)
        return self.gdb + '\\' + self.name + '_'+ add_name if out_put == '' else out_put

    def Get_vertxs_As_Point(self,out_put = ''):

        if self.Geom_type != 'Point':
            out_put  = self.Generate_Name(out_put,'Point')
            arcpy.CopyFeatures_management([arcpy.PointGeometry(arcpy.Point(j.X,j.Y)) for i in arcpy.SearchCursor (self.layer) for n in i.shape for j in n if j],out_put)
            return out_put

    def Get_Label_Point_As_Point(self,out_put = ''):

        out_put  = self.Generate_Name(out_put,'Label_Point')
        arcpy.CopyFeatures_management([arcpy.PointGeometry(i.shape.labelPoint) for i in arcpy.SearchCursor (self.layer) if i.shape],out_put)
        return out_put

    def None_in_fields(self,fields_to_Check=[]):

        if not fields_to_Check:
            fields_to_Check = self.fields()

        fields_None = [i for i in arcpy.da.SearchCursor(self.layer,fields_to_Check)]
        New_list    = set([str(fields_to_Check[n]) for i in range(len(fields_None)) for n in range(len(fields_to_Check)) if fields_None[i][n] == None])
        
        return New_list

    def Get_Closest_Distance(self,layer2 = '',Return_list = False):

        if layer2 =='':
            layer2 = self.layer

        layer2_oid = str(arcpy.Describe(layer2).OIDFieldName)    
        list1      = [[i[0],i[1]] for i in arcpy.da.SearchCursor(self.layer,    ["SHAPE@",self.oid])]
        all_list   = [[row[1],round(n[0].distanceTo(row[0]),2),n[1]] for row in arcpy.da.SearchCursor(layer2,["SHAPE@",layer2_oid])for n in list1 if n[0].distanceTo(row[0]) != 0]

        df         = pd.DataFrame     (all_list,columns= ['KEY','NUM','KEY2'])
        gb         = df.groupby       ('KEY').agg({'NUM':'min'}).reset_index()
        df2        = pd.merge         (gb,df,how = 'inner',on=['NUM','KEY'])

        data_to_gis = {getattr(row, "KEY") : [getattr(row, "KEY2"),getattr(row, "NUM")] for row in df2.itertuples(index=True, name='Pandas')}
            
        add_field(self.layer,'ID_ref','LONG')
        add_field(self.layer,'Dis','DOUBLE')
        with arcpy.da.UpdateCursor(self.layer,[self.oid,'ID_ref','Dis']) as cursor:
            for row in cursor:
                if data_to_gis.has_key(row[0]):
                    row[1] = data_to_gis[row[0]][0]
                    row[2] = data_to_gis[row[0]][1]
                    cursor.updateRow (row)

        return self.layer if Return_list == False else df2.values.tolist()

    def delete_identical(self,field = ''):
        if field == '':
            field = self.Calc_XY()
        del_identical(self.layer,field)

    def Fill_Holes_in_Polygon(self,Out_put = '' , delete_layer = False ,Return_holes = False):

        if self.Geom_type == 'Polygon':
            if Out_put == '':
                Out_put = self.gdb + '\\' + self.name + '_filled'

        add_field                        (self.layer,'Holes','SHORT')
        arcpy.CalculateField_management  (self.layer, 'Holes', "0" , "VB", "")

        Feature_to_polygon(self.layer,Out_put)
        New_polygons = int(str(arcpy.GetCount_management(Out_put))) -  self.len()
        # print ('New polygons : {}'.format(str(New_polygons)))
        arcpy.CalculateField_management(Out_put, "Holes", "Re_1( !Holes! )", "PYTHON_9.3", "def Re_1(x):\\n    if x != 0:\\n        return 1\\n    else:\\n        return 0")


        if delete_layer:
            arcpy.Delete_management(Out_put)
            return New_polygons

        if Return_holes:
            arcpy.MakeFeatureLayer_management(Out_put,'Out_put_lyr',"\"Holes\" = 0")
            arcpy.DeleteFeatures_management  ('Out_put_lyr')
            return Out_put

        return Out_put
