# -*- coding: UTF-8 -*-

    
import os
import arcpy
import uuid

def find_gdb_(Fodler):
    gdbs = []
    for root,dirs,files in os.walk(Fodler):
        if root.endswith('.gdb'):
            gdbs.append(root)
    return gdbs


def Clean_Data(gdbs):
    TOTAL_ALL = 0

    for gdb in gdbs:
        print "Working on: {}".format(gdb)
        tazar         = gdb + '\\' + 'PARCELS_inProc_edit'
        bankal_parcel = gdb + '\\' + 'PARCEL_ALL_EDIT'
        line_bankal   = gdb + '\\' + 'PARCEL_ARC_EDIT'
        point_bankal  = gdb + '\\' + 'PARCEL_NODE_EDIT'


        bankal_diss   = gdb + '\\' + 'bankal_diss'+ str(uuid.uuid4())[::11]
        bankal_Single = gdb + '\\' + 'bankal_Single'+ str(uuid.uuid4())[::11]

        temp_name = os.path.basename(os.path.dirname(gdb))+ str(uuid.uuid4())[::11]

        if arcpy.Exists(bankal_diss):
            arcpy.Delete_management(bankal_diss)

        if arcpy.Exists(bankal_Single):
            arcpy.Delete_management(bankal_Single)

        arcpy.Dissolve_management              (bankal_parcel,bankal_diss)
        arcpy.MultipartToSinglepart_management (bankal_diss,bankal_Single)
        arcpy.MakeFeatureLayer_management      (bankal_Single,temp_name)
        arcpy.SelectLayerByLocation_management (temp_name,"INTERSECT",tazar,'',"NEW_SELECTION","INVERT")
        arcpy.DeleteFeatures_management        (temp_name)


        list1 = [bankal_parcel,line_bankal,point_bankal]
        for i in list1:
            feat_before = int(str(arcpy.GetCount_management(i)))

            name = str(uuid.uuid4())[::10]
            arcpy.MakeFeatureLayer_management      (i,name)
            arcpy.SelectLayerByLocation_management (name,"INTERSECT",bankal_Single,'0.1',"NEW_SELECTION","INVERT")
            arcpy.DeleteFeatures_management        (name)

            feat_after = int(str(arcpy.GetCount_management(i)))

            deleted    = feat_before - feat_after
            TOTAL_ALL += deleted
            print "Total feature deleted from: {} is: {}".format(os.path.basename(i).split('.')[0],deleted)


    print "TOTAL ALL FEATURES: {}".format(TOTAL_ALL)


Fodler  = r'C:\Users\medad\python\GIStools\Work Tools\Psafas_tool\test_layers'
gdbs    = find_gdb_(Fodler)

Clean_Data(gdbs)


