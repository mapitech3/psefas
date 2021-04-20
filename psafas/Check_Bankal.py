# -*- coding: utf-8 -*-

import arcpy
import pandas as pd
import os,datetime


arcpy.env.overwriteOutPut = True


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


class Layer_Engine():

    def __init__(self,layer,columns = 'all'):

        if columns == 'all':
            columns = [str(f.name.encode('UTF-8')) for f in arcpy.ListFields(layer)]
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
            self.data_shape          = [str(round(j.X,0)) + '-' + str(round(j.Y,0))  for i in arcpy.da.SearchCursor (self.layer,['SHAPE@']) if i[0] for n in i[0] for j in n if j]
            self.set_                = set(self.data_shape)
            self.df_shape            = pd.DataFrame(data = self.data_shape , columns = ['SHAPE'])
        else:
            self.data_shape          = [str(round(i[0].centroid.X,2)) + '-' + str(round(i[0].centroid.Y,2)) for i in arcpy.da.SearchCursor (self.layer,['SHAPE@']) if i[0]]
            self.set_                = set(self.data_shape)
            self.df_shape            = pd.DataFrame(data = self.data_shape , columns = ['SHAPE'])

    def compare_vertexs(self,set_Compare):
        uniq = [[float(i.split('-')[0]),float(i.split('-')[1])] for i in list(self.set_ - set_Compare)]
        return uniq

    def Count_More_then1(self):
        self.df_shape['count']  = self.df_shape.groupby('SHAPE')['SHAPE'].transform('count')
        df_shape2               = self.df_shape[self.df_shape['count'] > 1]
        if not df_shape2.empty:
            df_shape2[['X','Y']] = df_shape2['SHAPE'].str.split('-',1,expand = True)
            df_shape2            = df_shape2.drop(['count','SHAPE'],axis = 1)
            list1                = df_shape2.values.tolist()
            return list1
        else:
            return []


def add_field(fc,field,Type = 'TEXT'):
    if arcpy.Exists(fc):
        TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
        if not TYPE:
            arcpy.AddField_management (fc, field, Type, "", "", 500)
        
def Convert_list_to_point(layer,list_,type_value):
    if list_:
        arcpy.CopyFeatures_management    ([arcpy.PointGeometry(arcpy.Point(i[0],i[1])) for i in list_],layer)
        add_field                        (layer,'type',Type = 'TEXT')
        arcpy.CalculateField_management  (layer,'type',"\"" + type_value + "\"","PYTHON_9.3")
    else:
        return []


def CutEqualParts(list1, num):
    avg = len(list1) / float(num)
    out = []
    last = 0.0

    while last < len(list1):
        out.append(list1[int(last):int(last + avg)])
        last += avg
    
    return  sorted([str(i).replace('[', '(').replace(']', ')') for i in out],reverse=False)


def Get_fc_from_List(fc_List,name):
    return [i for i in fc_List if name in i][0]

def Delete_polygons(fc,del_layer,Out_put):

    desc = arcpy.Describe(fc)

    fc = arcpy.CopyFeatures_management(fc,Out_put)
    
    if desc.ShapeType == u'Point':
        del_layer_temp = 'in_memory' + '\\' + 'Temp'
        if arcpy.Exists(del_layer_temp):
            arcpy.Delete_management(del_layer_temp)
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
            if arcpy.Exists(temp):
                arcpy.Delete_management(temp)
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

    if arcpy.Exists(r'in_memory\Dissolve_temp'):
        arcpy.Delete_management(r'in_memory\Dissolve_temp')
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

def topology_basic(final,gdb):

    memory        = r'in_memory'
    Diss          = memory + '\\' + 'dissolve'
    feat_to_poly  = memory + '\\' + 'Feature_to_poly'
    topo_holes    = gdb    + '\\' + 'Topolgy_Check_holes'
    topo_inter    = gdb    + '\\' + 'Topolgy_Check_intersect'

    if arcpy.Exists(Diss):
        arcpy.Delete_management(Diss)

    if arcpy.Exists(feat_to_poly):
        arcpy.Delete_management(feat_to_poly)

    arcpy.Dissolve_management                 (final,Diss)
    Feature_to_polygon                        (Diss,feat_to_poly)
    Delete_polygons                           (feat_to_poly,Diss,topo_holes)

    arcpy.Intersect_analysis([final],topo_inter)

    arcpy.Delete_management(Diss)
    arcpy.Delete_management(feat_to_poly)

    return topo_holes,topo_inter

def GetCount(layer):
    return int(str(arcpy.GetCount_management(layer)))

def createFolder(dic):
	try:
		if not os.path.exists(dic):
			os.makedirs(dic)
	except OSError:
		print ("Error Create dic")
		

print_arcpy_message("#  #  #  #  #  S T A R T  #  #  #  #  #",status = 1)

# # # # # # # # Inputs # # # # # # # # 

 ############################### TEST ##############################
# path = r'C:\Users\medad\OneDrive\שולחן העבודה\Check_Bankal\Data\Test.gdb'
 ################################################################



# path = r"C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Tazar_For_run\EditTazar89705\CadasterEdit_Tazar.gdb"

path =  arcpy.GetParameterAsText(0) # GDB work space

arcpy.env.workspace = path
fc_List = arcpy.ListFeatureClasses()


path_polys  = path + '\\' + Get_fc_from_List(fc_List,'PARCEL_ALL' )
path_lines  = path + '\\' + Get_fc_from_List(fc_List,'PARCEL_ARC')
path_points = path + '\\' + Get_fc_from_List(fc_List,'PARCEL_NODE')

print (path_polys)
print (path_lines)
print (path_points)


 ############################### Prepare data ##############################



print_arcpy_message("#  #  Prepare data #  # ",status = 1)

createFolder('C:\\temp')
path_folder = r'C:\temp'
d           = datetime.datetime.now()
time        = str(d.hour) + '_' + str(d.minute) + '_' + str(d.day)
gdb_name    = path_folder + '\\' + 'ALL_ERRORS_' + time + '.gdb'
error_layer = gdb_name + '\\' + 'Errors'
if not arcpy.Exists(gdb_name):
    arcpy.CreateFileGDB_management      (path_folder,'ALL_ERRORS_' + time + '.gdb')
    arcpy.CreateFeatureclass_management (gdb_name,'Errors','POINT')
    add_field                           (error_layer,'type')

full_path_pack = path_folder + '\\Temp_errors.gdb'
arcpy.CreateFileGDB_management      (path_folder,'Temp_errors.gdb')

# # # # # # # # Read Data # # # # # # # # 

print_arcpy_message("Read data",status = 1)

poly_class  = Layer_Engine(path_polys)
poly_class.Extract_shape()

point_class  = Layer_Engine(path_points)
point_class.Extract_shape()

line_class  = Layer_Engine(path_lines)
line_class.Extract_shape()

point_dupli      = full_path_pack + '\\' + 'Point_Duplicate'
poly_comp_line   = full_path_pack + '\\' + 'poly_Compare_line'
line_comp_poly   = full_path_pack + '\\' + 'line_compare_poly'
line_Cross_Poly  = full_path_pack + '\\' + 'line_Cross_Poly'

line_dupli_temp  = full_path_pack + '\\' + 'line_dupli_temp'
line_dupli       = gdb_name       + '\\' + 'line_Error'


# # # # # # # # Point # # # # # # # # 

print_arcpy_message("Working on Points",status = 1)

list_dupli = point_class.Count_More_then1()
Convert_list_to_point  (point_dupli,list_dupli,'Point_Duplicate')


# # # # # # # # polygon # # # # # # # # 

print_arcpy_message("Working on Polygons",status = 1)

list_poly_comp_line  = poly_class.compare_vertexs(line_class.set_)
Convert_list_to_point  (poly_comp_line,list_poly_comp_line,'poly_Compare_line')

# # # # # # # # Line # # # # # # # #  

print_arcpy_message("Working on Lines",status = 1)

list_comp_line  = line_class.compare_vertexs(poly_class.set_)
Convert_list_to_point  (line_comp_poly,list_comp_line,'Line_Compare_poly')


arcpy.Intersect_analysis         ([line_class.layer],line_dupli_temp)
add_field                        (line_dupli_temp,'type',Type = 'TEXT')
arcpy.CalculateField_management  (line_dupli_temp,'type',"\"" + 'Line_Intersect' + "\"","PYTHON_9.3")
arcpy.Copy_management            (line_dupli_temp,line_dupli)

arcpy.MakeFeatureLayer_management      (line_class.layer,'Line_layer')
arcpy.SelectLayerByLocation_management ('Line_layer',"WITHIN_CLEMENTINI",poly_class.layer)
arcpy.CopyFeatures_management          ('Line_layer',line_Cross_Poly)
add_field                              (line_Cross_Poly,'type',Type = 'TEXT')
arcpy.CalculateField_management        (line_Cross_Poly,'type',"\"" + 'line_Cross_Poly' + "\"","PYTHON_9.3")

# Check Topo

topo_holes,topo_inter = topology_basic(poly_class.layer,gdb_name)

# # # # # # # # Insert # # # # # # # #  

print_arcpy_message("Insert to Errors layer",status = 1)

layers_list = [n for n in [poly_comp_line,line_comp_poly,point_dupli] if arcpy.Exists(n)]
if layers_list:
    arcpy.Append_management(layers_list,error_layer,'NO_TEST')

arcpy.Append_management(line_Cross_Poly,line_dupli,'NO_TEST')

arcpy.Delete_management(full_path_pack)

layers_errors = [n for n in [poly_comp_line,line_comp_poly,point_dupli,line_dupli,topo_holes,topo_inter] if arcpy.Exists(n)]
errors_sum    = sum([GetCount(i) for i in layers_errors])
if errors_sum == 0:
    print_arcpy_message     ('Layer Passed checks successfully',1)
    arcpy.Delete_management (gdb_name)
else:
    print_arcpy_message ('there is: {}, Problem with bankal'.format(errors_sum),2)
    print_arcpy_message ('watch error gdb for more information: {}'.format(gdb_name),1)


print_arcpy_message("#  #  #  #  #  F I N I S H  #  #  #  #  #",status = 1)


