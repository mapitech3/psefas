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


import sqlite3,json,random
import xml.etree.ElementTree as ET

from Layer_Class   import *
from Basic_Func    import *
from Advanced_Func import *
from Psafas_Tools  import * 
from PSAFAS_KR     import *
from Checks        import *



#####################  CHEACKS ########################


def Cheaks(CURRENT):


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


    topology_basic                  (layer_parcel,gdb)
    line_Not_on_parcels             (layer_arc,layer_parcel, gdb)
    Insert_needed_arc               (layer_parcel,layer_arc,Keshet,gdb)
    Node_not_on_parcel              (layer_parcel,layer_node.layer,gdb)
    vertex_without_modad_point      (layer_parcel,parcel_modad,lyr_node_modad,gdb)
    missing_modad_point             (layer_node,parcel_modad,lyr_node_modad,gdb)
    double_arc                      (gdb,arc_all)
    double_node                     (gdb,node_all)
    Parcel_data                     (layer_parcel.layer,ws)
    Calc_Area                       (layer_parcel.layer,ws,gdb)
    Check_accurancy_pracel          (layer_parcel.layer,gdb)
    missing_Values_in_parcel        (layer_parcel.layer,ws,gdb)
    Find_not_exists_parcel_in_Gush  (layer_parcel.layer,ws,gdb)
    Found_bad_parcel_around_AOI     (layer_parcel.layer,ws,gdb)



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

    # Cheaks          (out_put + "\\EditTazar"+tazar_num+".mxd")

    # ###########################################

    # arcpy.AddMessage("Open MXD Copy")
    # os.startfile    (out_put + "\\EditTazar"+tazar_num+".mxd")
    # arcpy.RefreshActiveView()



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

