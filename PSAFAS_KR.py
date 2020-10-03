# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # PSAFAS KR # # # # # # # # # # # # # # # 

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

def Get_layer_gdb_Copy(gdb):

    parcel_bankal_c = GDB + '\\' + 'PARCEL_ALL_EDIT_copy'
    arc_bankal_c    = GDB + '\\' + 'PARCEL_ARC_EDIT_copy'
    point_bankal_c  = GDB + '\\' + 'PARCEL_NODE_EDIT_copy'

    parcel_modad_c  = GDB + '\\' + 'PARCELS_inProc_edit_copy'
    arc_modad_c     = GDB + '\\' + 'LINES_inProc_edit_copy'
    point_modad_c   = GDB + '\\' + 'POINTS_inProc_edit_copy'

    return parcel_bankal_c,arc_bankal_c,point_bankal_c,parcel_modad_c,arc_modad_c,point_modad_c

scriptPath = os.path.abspath(__file__)
Scripts    = os.path.dirname(scriptPath)
ToolShare  = os.path.dirname(Scripts)
Scratch    = ToolShare + "\\Scratch4"
ToolData   = ToolShare + "\\ToolData"


parcels_bankal_705      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89705\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_700      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89700\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_708      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89708\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_709      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89709\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_702      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89702\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_677      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89677\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_678      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89678\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_690      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89690\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_695      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89695\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_699      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89699\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'

parcels_bankal_704      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89704\CadasterEdit_Tazar.gdb\PARCEL_ALL_EDIT'
parcels_bankal_784      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89784\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_795      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89795\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_808      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89808\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'
parcels_bankal_809      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89809\CadasterEdit_Tazar.gdb\PARCELS_inProc_edit'

Folder                 =   Scratch
Dis_limit_border_pnts  =   1
sett                   = r''


print_arcpy_message     ("# # # # # # # S T A R T # # # # # #",status = 1)

CURRENT_705 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89705\EditTazar89705_Copy.mxd'
CURRENT_700 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89700\EditTazar89700_Copy.mxd'
CURRENT_708 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89708\EditTazar89708_Copy.mxd'
CURRENT_709 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89709\EditTazar89709_Copy.mxd'
CURRENT_702 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89702\EditTazar89702_Copy.mxd'
CURRENT_677 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89677\EditTazar89677_Copy.mxd'
CURRENT_678 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89678\EditTazar89678_Copy.mxd'
CURRENT_690 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89690\EditTazar89690_Copy.mxd'
CURRENT_695 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89695\EditTazar89695_Copy.mxd'
CURRENT_699 = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89699\EditTazar89699_Copy.mxd'

CURRENT_704      = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89704\EditTazar89704_Copy.mxd'
CURRENT_784      = r"C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89784\EditTazar15_2019_Copy.mxd"
CURRENT_795      = r"C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89795\EditTazar3184_2018_Copy.mxd"
CURRENT_808      = r"C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89808\EditTazar2724_2018_Copy.mxd"
CURRENT_809      = r"C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers\Tazar_For_run\EditTazar89809\EditTazar2321_2018_Copy.mxd"

# CURRENT = r'CURRENT'


parcels_bankal_list = [[parcels_bankal_704,CURRENT_704],[parcels_bankal_705,CURRENT_705],[parcels_bankal_708,CURRENT_708],[parcels_bankal_700,CURRENT_700],\
                      [parcels_bankal_677,CURRENT_677],[parcels_bankal_699,CURRENT_699],[parcels_bankal_709,CURRENT_709],[parcels_bankal_702,CURRENT_702],\
                      [parcels_bankal_784,CURRENT_784],[parcels_bankal_695,CURRENT_695],[parcels_bankal_678,CURRENT_678],[parcels_bankal_690,CURRENT_690],\
                      [parcels_bankal_795,CURRENT_795],[parcels_bankal_809,CURRENT_809],[parcels_bankal_808,CURRENT_808]]


for parcels_bankal in parcels_bankal_list:

    print_arcpy_message     ("Working on: {}".format(parcels_bankal[0].split('\\')[-3]),1)

    layers_to_Copy  = ['PARCEL_ALL_EDIT','PARCEL_ARC_EDIT','PARCEL_NODE_EDIT','PARCELS_inProc_edit','LINES_inProc_edit','POINTS_inProc_edit']

    GDB_Source      = getLayerPath (parcels_bankal[0],parcels_bankal[1])
    GDB             = CreateWorkingGDB (GDB_Source,Folder,layers_to_Copy,'Parcels_inProc_edit')

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

    ChangeFieldNames                   (parcel_modad_c,arc_modad_c,point_modad_c)  # שינוי שמות השדות לפורמט בנק"ל
    connect_parcel_to_sett             (parcel_modad_c,sett)                         # הזנה של שמות ומספרי מפתח של ישובים לחלקות

    AOI,tazar_border,Curves,parcel_Bankal_cut,Point_bankal_Cut = PrePare_Data    (parcel_bankal_c,parcel_modad_c,point_modad_c,point_bankal_c,GDB,'POINT_NAME','POINT_NAME')
    Fix_curves                                                                   (AOI,tazar_border,Curves)

    add_err_pts_to_mxd                 (GDB, ToolData + "\\lyr_files", ToolData + "\\demo.gdb",parcels_bankal[1]) # parcels_bankal[1] = Current

    if CheckResultsIsOK(AOI,tazar_border,1):
        AOI_best  = AOI
        if CheckIfSkipProcess(parcel_Bankal_cut,parcel_modad_c,GDB):
            print_arcpy_message     ("Exit",status = 1)
            sys.exit(0)

     # # # # # # # # בודק אם יש שינוי בגבולת אך ללא שינוי בתוך התצר, במידה ואין שינוי בגבולות, מחליף בין היישויות
    Sub_Processing(parcel_bankal,parcel_modad_c,point_bankal,point_modad,arc_bankal,arc_modad,tazar_border,parcel_modad_c,AOI,GDB)

    if Continue:
        Dis_border_pnts = get_default_Snap_border (Point_bankal_Cut,parcel_modad_c,Dis_limit_border_pnts) 
        Snap_border_pnts        (GDB , tazar_border ,AOI,Dis_border_pnts) # סתימת חורים ע"י הזזת נקודות גבול
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
        AOI_best  = AOI2
         # # # # # # # Check if all holes are closed after the Geometry tool
        if CheckResultsIsOK(AOI2,tazar_border,3):
            Continue   = False

    if Continue:
         # # # # # # # Work Only if there is still Holes
        fix_holes_Overlaps_By_Length  (AOI2 , tazar_border ,AOI3)      # סתימת חורים ע"י שיוך לפי קו גדול משותף גדול ביותר
        clean_pseudo                  (AOI3, tazar_border ,Curves)
        Update_Layer_Curves_By_ID     (AOI3,parcel_modad_c,Curves)
        Fix_curves                    (AOI3,tazar_border,Curves)

        AOI_best = AOI3

    CheckResultsIsOK(AOI_best,tazar_border,5)

    stubborn_parts            (AOI_best,parcel_bankal_c,parcel_modad_c,AOI_final,Curves)
    Update_Layer_Curves_By_ID (AOI_final,parcel_modad_c,Curves)
    Fix_curves                (AOI_final,tazar_border,Curves)

    fix_tolerance            (AOI_final,tazar_border)
    get_no_node_vertex       (AOI_final,tazar_border,point_modad_c,Point_bankal_Cut)

    Fix_Multi_part_Bankal    (AOI_final,tazar_border,parcel_Bankal_cut) # מתקן חלקות רחוקות שנפגעו בגלל שיש בהן חורים
    Delete_curves_out_AOI    (AOI_final,parcel_bankal)
    Update_Polygons          (AOI_final,parcel_modad_c)
    CheckResultsIsOK         (AOI_final,tazar_border,6)                # בדיקת סופית, כמה חורים נשארו

    #  #  #  #  #  # # Prepare Insert to Razaf  #  #  #  #  #  #  # 
    print_arcpy_message ("  #   #   #    # Preper data For Insert  #   #   #   #  ")

    Calculate_Area_Rashum   (AOI_final)
    NewGushim               (parcel_modad_c, parcel_bankal,AOI_final)
    Get_Point_AOI           (AOI_final,point_bankal_c,point_modad_c,AOI_Point)
    Create_Line_AOI         (AOI_final,tazar_border,Curves,arc_bankal_c,arc_modad_c,AOI_Line)


    #  #  #  #  #  #  # insert To Razaf #  #  #  #  #  #  #  # #

    print_arcpy_message ("  #   #   #    # insert To Razaf  #   #   #   #  ")

    # # # Polygons 

    # Update_Polygons  (parcel_bankal,AOI_final)

    # # # # Lines

    # Layer_Management        (arc_bankal).Select_By_Location('INTERSECT',parcel_modad_c,'10 Meters')
    # delete_Line_by_polygon  (arc_bankal,AOI_Line,True)
    # arcpy.Append_management (AOI_Line,arc_bankal,'NO_TEST')

    # # # # Points

    # bankal_pnts = Layer_Management (point_bankal).Select_By_Location('INTERSECT',AOI_final)
    # arcpy.Append_management        (AOI_Point,point_bankal)

    #    #   #    #  #

    print_arcpy_message ("  #   #   #    #  Last Checks  #   #   #   #  ")

    Parcel_data         (parcel_bankal,parcel_bankal_c,parcel_modad_c)


# print_arcpy_message     ("# # # # # # # #     F I N I S H     # # # # # # # # #",1)


