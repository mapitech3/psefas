import os,uuid,re
import arcpy

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

def mxd_making(mxd_path,gdb_path,tazar_num,gdb,out_put):

    mxd = arcpy.mapping.MapDocument (mxd_path)

    mxd.findAndReplaceWorkspacePaths(gdb_path, gdb)
    df           = arcpy.mapping.ListDataFrames(mxd)[0]
    BORDER_Layer = arcpy.mapping.ListLayers(mxd, "", df)[-1]
    df.extent    = BORDER_Layer.getExtent()

    mxd.saveACopy   (out_put + "\\EditTazar"+tazar_num+".mxd")
    arcpy.AddMessage("Open MXD Copy")
    os.startfile    (out_put + "\\EditTazar"+tazar_num+".mxd")
    arcpy.RefreshActiveView()

# Input
path_bankal       = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_ALL'
path_line         = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_ARC'
path_point        = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\Cadaster\PSEFAS_DATA.gdb\PARCEL_NODE'

path_source_tazar         = arcpy.GetParameterAsText(0) # folder of tazars to make as AOI

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

    # create and opening mxd
    mxd_making (mxd_path_template,gdb_path_template,list_path_Num[1][i],tazar_gdb,tazar_folder)




