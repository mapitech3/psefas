# !/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding=utf8

import os,uuid,re
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

import os,ast,math
import arcpy

from Layer_Class   import *
from Basic_Func    import *
from Advanced_Func import *
from Psafas_Tools  import * 


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



