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
Scratch    = ToolShare + "\\Scratch2"
ToolData   = ToolShare + "\\ToolData"

parcels_bankal         = arcpy.GetParameterAsText(0)
Folder                 = Scratch
Dis_limit_border_pnts  = 1
sett                   = ToolData + '\\' + r'Set.gdb\Sett'
CURRENT                = r'CURRENT'


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
add_err_pts_to_mxd                 (GDB, ToolData + "\\lyr_files", ToolData + "\\demo.gdb",CURRENT) # parcels_bankal[1] = Current


if CheckResultsIsOK(AOI,tazar_border,1):
    AOI_best  = AOI
    Continue  = False

    # # # # # # # # בודק אם יש שינוי בגבולת אך ללא שינוי בתוך התצר, במידה ואין שינוי בגבולות, מחליף בין היישויות
Sub_Processing(parcel_bankal,parcel_modad_c,point_bankal,point_modad,arc_bankal,arc_modad,tazar_border,parcel_modad_c,AOI,GDB)

if Continue:
    Dis_border_pnts = get_default_Snap_border (Point_bankal_Cut,parcel_modad_c,Dis_limit_border_pnts) 
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
Create_Line_AOI         (AOI_final,tazar_border,Curves,arc_bankal_c,arc_modad_c,AOI_Line)

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
