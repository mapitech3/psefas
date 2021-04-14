
# -*- coding: utf-8 -*-

import uuid,os
import arcpy
import pythonaddins

class ButtonClass1(object):
    """Implementation for Insert_to_razaf_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
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
                

        def add_field(fc,field,Type = 'TEXT'):

            TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
            if not TYPE:
                arcpy.AddField_management (fc, field, Type, "", "", 500)


        def fix_Schama(AOI_Final,PARCEL_ALL_EDIT):

            li_fields_needed = [str(f.name) + '-' + str(f.type) for f in arcpy.ListFields (PARCEL_ALL_EDIT)]
            li_exists        = [str(f.name) + '-' + str(f.type) for f in arcpy.ListFields (AOI_Final)]
            list_to_del      = [i for i in li_exists if i not in li_fields_needed]
            exe              = [arcpy.DeleteField_management(AOI_Final,i.split('-')[0]) for i in list_to_del]

            # check if len of AOI_Final is equal to len of PARCEL_ALL_EDIT and add missing fields
            fields_added  =  [str(f.name) + '-' + str(f.type) for f in arcpy.ListFields (AOI_Final)]
            if len(li_fields_needed) != len(fields_added):
                set_field_need   = set(li_fields_needed)
                set_fields_added = set(fields_added)
                add_to_layer     = set_field_need   - set_fields_added
                print (add_to_layer)
                exe2             = [add_field(AOI_Final,i.split('-')[0],i.split('-')[1]) for i in add_to_layer]

                missing_layers     = set_fields_added   - set_field_need
                print (missing_layers)


        def Delete_polygons(fc,del_layer,Out_put = ''):

            '''
            fc        = השכבה הראשית- שכבה ממנה רוצים למחוק
            del_layer = שכבה שתמחק את השכבה הראשית
            Out_put   = שכבת הפלט, במידה ולא תוכנס שכבה, ימחק מהשכבה הראשית
            '''
            
            desc = arcpy.Describe(fc)

            if not Out_put == '':
                fc = arcpy.CopyFeatures_management(fc,Out_put)
            else:
                Out_put = fc
            
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
                        else:
                            pass
                    del Ucursor
                del del_layer_temp
                                
            else:
                count_me = int(str(arcpy.GetCount_management(del_layer)))
                if count_me > 0:
                    temp = 'in_memory' +'\\'+'_temp'
                    arcpy.Dissolve_management(del_layer,temp)
                    if int(str(arcpy.GetCount_management(temp))) > 0:
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

        def Update_Large_Layers(AOI_Final,PARCEL_ALL_EDIT,del_layer = ''):

            if del_layer == '':
                del_layer = AOI_Final

            add_uuid = str(uuid.uuid4())[::4]
            temp_lyr = r'in_memory\temp_lyr' + add_uuid

            fix_Schama                            (AOI_Final,PARCEL_ALL_EDIT)
            arcpy.MakeFeatureLayer_management      (PARCEL_ALL_EDIT,temp_lyr)
            arcpy.SelectLayerByLocation_management (temp_lyr,"INTERSECT",AOI_Final,'0.1 meters')
            Delete_polygons                        (temp_lyr,del_layer)
            arcpy.Append_management                (AOI_Final,PARCEL_ALL_EDIT)

        Current = 'CURRENT'
        # Current     = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Tazar_For_run\EditTazar89690\EditTazar89690.mxd'

        SDE_parcels = r'C:\Users\Administrator\Desktop\medad\python\Work\Mpy\Test_finish_proc\GDB.gdb\PARCEL_ALL_EDIT'

        mxd      = arcpy.mapping.MapDocument(Current)
        df      = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        lyr = arcpy.mapping.ListLayers(mxd,"קווים להכנסה", df)[0]
        gdb = os.path.dirname(lyr.dataSource)

        AOI_Final       = gdb + '\\' + 'Parcel_all_edit'

        Update_Large_Layers (AOI_Final,SDE_parcels)
        print_arcpy_message('Bankal has Changes successfully')



# work = ButtonClass1()

# work.onClick()