# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # PSAFAS HAK # # # # # # # # # # # # # # # 


import os
import arcpy

from Layer_Class   import *
from Basic_Func    import *
from Advanced_Func import *
from Psafas_Tools  import * 


arcpy.env.overwriteOutput = True


# שכבות קבועות
parcel_bankal = r'C:\Users\medad\Desktop\Mpy\Work_on.gdb\PARCEL_ALL' # שכבת רצף 
Point_bankal  = r'C:\Users\medad\Desktop\Mpy\Work_on.gdb\PARCEL_ALL_Point'
sett       = r''                                                  # שכבת ישובים

# קלט לכלי
parcels         = r'C:\Users\medad\Desktop\Mpy\sources\Hak_data\14704\SRVToGDB_14704_0.gdb\DS_Srv\parcels'
Dis_border_pnts = 2

# למחוק לאחר הפיתוח
CURRENT                    = r"C:\Users\medad\Desktop\Mpy\PSAFAS_HK.mxd"   # only for Development, Delete foe run on GIS
Dis_limit_border_pnts      = 2

print_arcpy_message ("# # # # # # # #      S T A R T     # # # # # # # # #",1)

scriptPath = os.path.abspath(__file__)
Scripts    = os.path.dirname(scriptPath)
Folder     = os.path.dirname(Scripts)
Scratch    = Folder + "\\Scratch4"
ToolData   = Folder + "\\ToolData"

# הכנת בסיס הנתונים והשמות

GDB_Source = getLayerPath(parcels,CURRENT)
GDB        = CreateWorkingGDB(GDB_Source,Scratch,['lines','parcels','points'],'parcels') # last input need to be a name from MXD like: שכבות לעריכה
print 'GDB: {}'.format(GDB)

points_copy  = GDB + '\\' + 'points_copy'
lines_copy   = GDB + '\\' + 'lines_copy'
parcels_copy = GDB + '\\' + 'parcels_copy'

ChangeFieldNames         (parcels_copy,lines_copy,points_copy)  # שינוי שמות השדות לפורמט בנק"ל
connect_parcel_to_sett   (parcels_copy,sett)                    # הזנה של שמות ומספרי מפתח של ישובים לחלקות

# שכבות עזר

Continue   = True                   # בדיקת צורך בהמשך פעולות גאומטריות, יהיה שלילי כאשר לא היו בעיות גאומטריות 
AOI2       = GDB + '\\' + 'AOI2'    # clean_slivers_by_vertex
AOI3       = GDB + '\\' + 'AOI3'    # after using: fix_holes_by_neer_length
AOI_final  = ''                     # return the last AOI Layer


# הכנת אזור עבודה, קשתות, גבול תצר

AOI,tazar_border,Curves,parcel_Bankal_cut,Point_bankal_Cut = PrePare_Data (parcel_bankal,parcels_copy,points_copy,Point_bankal,GDB,'name','point_name')

# בדיקת אזור העבודה, חורים חפיפות

holes_1 = GDB + '\\' + 'Holes_Check_1'     # Created in CheckResultsIsOK
if CheckResultsIsOK(AOI,tazar_border,1):
    sys.exit(0)

# # # # # # # #    Start Geometry actions    # # # # # # # #


Dis_border_pnts = get_default_Snap_border (Point_bankal_Cut,parcels_copy,Dis_limit_border_pnts) 

Snap_border_pnts        (GDB , tazar_border ,AOI,Dis_border_pnts) # סתימת חורים ע"י הזזת נקודות גבול
Fix_curves              (AOI , tazar_border ,Curves)
clean_pseudo            (AOI , tazar_border ,Curves)


if CheckResultsIsOK(AOI,tazar_border,2):
    # # # # Check if there is holes
    AOI_final  = AOI
    Continue   = False


if Continue:
    # # # # Work Only if there is still Holes
    clean_slivers_by_vertex  (AOI,holes_1,tazar_border,3,AOI2)
    Fix_curves               (AOI2, tazar_border ,Curves) 
    clean_pseudo             (AOI2, tazar_border ,Curves)
    # # # # Check if all holes are closed after the Geometry tool
    if CheckResultsIsOK(AOI2,tazar_border,3):
        AOI_final  = AOI2
        Continue   = False


if Continue:
    # # # # Work Only if there is still Holes
    fix_holes_by_neer_length (AOI2 , tazar_border ,AOI3 )      # סתימת חורים ע"י שיוך לפי קו גדול משותף גדול ביותר
    Fix_curves               (AOI3, tazar_border ,Curves) 
    clean_pseudo             (AOI3, tazar_border ,Curves)
              
    AOI_final = AOI3


fix_tolerance            (AOI_final,tazar_border)
CheckResultsIsOK         (AOI3,tazar_border,3)                # בדיקת סופית, כמה חורים נשארו
get_no_node_vertex       (AOI_final,tazar_border,points_copy,Point_bankal_Cut)        

# # # # # # # #    Finish Geometry actions    # # # # # # # #


# # # # # # # # insert Parcels to AOI

Delete_polygons         (AOI_final    , tazar_border , ''      )
arcpy.Append_management (parcels_copy , AOI_final    ,'NO_TEST')

Calculate_Area_Rashum   (AOI_final)

print_arcpy_message     ("# # # # # # # #     F I N I S H     # # # # # # # # #",1)
