# -*- coding: utf-8 -*-

import pythonaddins
import sqlite3
import os
import math
import xml.etree.ElementTree as ET
import arcpy, urllib2, urllib


arcpy.env.overwriteOutput = True

class Calc_Area(object):
    """Implementation for Add_in_Fields_addin.Calc_Area (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        def math_delta_rashum(area_rashum):
            area_rashum = float(area_rashum)
            delta1 = (0.3 * (math.sqrt(area_rashum)) + (0.005 * area_rashum))
            delta2 = (0.8 * (math.sqrt(area_rashum)) + (0.002 * area_rashum))
            if delta1 > delta2:
                delta = delta1
            else:
                delta = delta2
            return delta
            
                                    
        def find_problem(Area_rasum,Shape_area,delta):
            minus = abs(Area_rasum - Shape_area)
            if minus > delta:
                return 'Warning, Delta is to big'
            else:
                return 'Ok'

        
        mxd = arcpy.mapping.MapDocument('current')
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        print "ok"
        if df:
            lyr = arcpy.mapping.ListLayers(mxd,"חלקות לעריכה", df)[0]
            if lyr:				
                fields = [["GAP", "DOUBLE"],["delta", "DOUBLE"],["Check", "TEXT"]]
                for i in fields:
                    try:
                        print i[0]
                        arcpy.AddField_management(lyr,i[0], i[1])
                    except:
                        pass

                with arcpy.da.UpdateCursor(lyr,["LEGAL_AREA","SHAPE_Area","GAP","delta","Check"]) as up_cursor:
                    for row in up_cursor:
                        delta  = math_delta_rashum(row[0])
                        row[3] = delta
                        row[2] = abs(row[1] - row[0])- delta
                        row[4] = find_problem(row[0],row[1],delta)
                        up_cursor.updateRow (row)
                del up_cursor

                data_check = [i for i in arcpy.SearchCursor(lyr) if i.Check == 'Warning, Delta is to big']
                if len(data_check) == 0:
                    pythonaddins.MessageBox('All fields are ok','INFO',0)

class Finish_Editing(object):
    """Implementation for Add_in_tools_addin.cheack_fields (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):

        def add_field(fc,field,Type = 'TEXT'):
            TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
            if not TYPE:
                arcpy.AddField_management (fc, field, Type)

        def del_fields_psafas(fc_to_delete_fields_from):
                list_of_fileds_to_del = ['GAP','delta','Check','KEY']
                field_names = [f.name for f in arcpy.ListFields(fc_to_delete_fields_from)]
                for field in field_names:
                        if field in list_of_fileds_to_del:
                                try:
                                        arcpy.DeleteField_management(fc_to_delete_fields_from, field)
                                except:
                                        print field + " Can't be deleted"
                pass

        def Insert_to_table(bankal,tazar_copy,GDB):

            arcpy.MakeFeatureLayer_management      (bankal,'bankal_lyr')
            arcpy.SelectLayerByLocation_management ('bankal_lyr','INTERSECT',tazar_copy, '1 Meters')

            None_me = [i for i in arcpy.SearchCursor(tazar_copy) if i.PARCEL_FINAL == None]
            if None_me:
                arcpy.CalculateField_management  (tazar_copy, 'PARCEL_FINAL', "int( ''.join ([i for i in !PARCELNAME! if i.isdigit()]))", "PYTHON" ) 

            new_shamce = False
            try:
                data = [[i.shape,str(i.PARCEL_FINAL)+'-'+str(i.GUSHNUM)+'-'+str(i.GUSHSUFFIX)] for i in arcpy.SearchCursor(tazar_copy)]
            except:
                data = [[i.shape,str(i.PARCEL)+'-'+str(i.GUSH_NUM)+'-'+str(i.GUSH_SUFFIX)] for i in arcpy.SearchCursor(tazar_copy)]
                new_shamce = True

            in_tazar_copy = []
            with arcpy.da.SearchCursor ('bankal_lyr', ['SHAPE@','PARCEL','GUSH_NUM','GUSH_SUFFIX']) as cursor:
                for row in cursor:
                    geom   = row[0]
                    midpnt = geom.labelPoint
                    key    = str(row[1])+'-'+str(row[2])+'-'+str(row[3])
                    for i in data:
                        if i[0].distanceTo(midpnt) == 0:
                            in_tazar_copy.append([i[1],key])
                del cursor


            data          = [[i.shape,str(i.PARCEL)+'-'+str(i.GUSH_NUM)+'-'+str(i.GUSH_SUFFIX)] for i in arcpy.SearchCursor('bankal_lyr')]
            in_bankal     = []
            fields_parcel = ['SHAPE@','PARCEL_FINAL','GUSHNUM','GUSHSUFFIX']
            if new_shamce == True:
                fields_parcel = ['SHAPE@','PARCEL','GUSH_NUM','GUSH_SUFFIX']

            with arcpy.da.SearchCursor (tazar_copy, fields_parcel) as cursor:
                for row in cursor:
                    geom   = row[0]
                    midpnt = geom.labelPoint
                    key    = str(row[1])+'-'+str(row[2])+'-'+str(row[3])
                    for i in data:
                        if i[0].distanceTo(midpnt) == 0:
                            in_bankal.append([key,i[1]])
                del cursor


            data1 = [ast.literal_eval(i) for i in list(set([str(i) for i in in_tazar_copy + in_bankal]))]


            path      = GDB
            name1     = 'CANCEL_PARCEL_EDIT'
            full_path = path +'\\'+ name1

            if not arcpy.Exists(full_path):
                arcpy.CreateTable_management(path,name1)

            fields = ['F_PARCEL_NUM','F_GUSH_SUFFIX','T_PARCEL_NUM','T_GUSH_SUFFIX']
            add_field(full_path,"F_GUSH_NUM",'LONG')
            add_field(full_path,"T_GUSH_NUM",'LONG')
            for i in fields:
                add_field(full_path,i,'SHORT')

            arcpy.DeleteRows_management(full_path)
            for row in data1:
                    insert = arcpy.InsertCursor (full_path)
                    in_row               = insert.newRow()
                    in_row.F_GUSH_NUM    = int(row[1].split('-')[1])
                    in_row.F_PARCEL_NUM  = int(row[1].split('-')[0])
                    in_row.F_GUSH_SUFFIX = int(row[1].split('-')[2])
                    in_row.T_GUSH_NUM    = int(row[0].split('-')[1])
                    in_row.T_PARCEL_NUM  = int(row[0].split('-')[0])
                    in_row.T_GUSH_SUFFIX = int(row[0].split('-')[2])
                    insert.insertRow   (in_row)

        def Parcel_data(path_after,path_before,GDB,tazar):

            conn = sqlite3.connect(":memory:")
            c = conn.cursor()
            c.execute("""CREATE TABLE Before_Table (
                                PARCEL      INTEGER,
                                GUSH_NUM    INTEGER,
                                KEY         text,
                                GUSH_SUFFIX INTEGER
                                )""")

            c = conn.cursor()
            c.execute("""CREATE TABLE Table_After (
                                PARCEL      INTEGER,
                                GUSH_NUM    INTEGER,
                                KEY         text,
                                GUSH_SUFFIX INTEGER
                                )""")

            for i in arcpy.SearchCursor(path_before):
                c.execute ("INSERT INTO Before_Table VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM)+"-"+ str(i.GUSH_SUFFIX)+"',"+str(i.GUSH_SUFFIX)+")")

            for i in arcpy.SearchCursor(path_after):
                c.execute ("INSERT INTO Table_After VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM) +"-"+ str(i.GUSH_SUFFIX)+"',"+str(i.GUSH_SUFFIX)+")")

            count_before = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Before_Table group by KEY) t1 WHERE t1.count > 1;''')]
            count_after  = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Table_After group by KEY) t1 WHERE t1.count > 1;''')]

            if count_before:
                msg  =  " # # # WARNING # # # Found identical parcels on orig parcels : {}".format(count_before)
                pythonaddins.MessageBox  (msg,'INFO',0)

            if count_before:
                msg2 = " # # # WARNING # # # Found identical parcels on new parcels : {}".format(count_after)
                pythonaddins.MessageBox  (msg2,'INFO',0)


            add_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Table_After A LEFT JOIN Before_Table B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]
            del_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Before_Table A LEFT JOIN Table_After B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]

            # Create Table
            Insert_to_table(path_before,tazar,GDB)

            msg2 = "added parcels: {}  ".format(add_parcels)
            msg3 = "Deleted parcels: {}".format(del_parcels)

            pythonaddins.MessageBox("added parcels:   {}  ".format(add_parcels),'INFO',0)
            pythonaddins.MessageBox("Deleted parcels: {}  ".format(del_parcels),'INFO',0)



        ## MAIN ##
        MXD = arcpy.mapping.MapDocument    ('CURRENT')
        df  = arcpy.mapping.ListDataFrames  (MXD, "Layers")[0]
        lyr = {"path_after":'',"path_before":'','GDB':'','Tazar':''}
        if df:
                for i in df:
                        if i.name.encode('UTF-8') in ['PARCEL_ALL_EDIT','PARCEL_NODE_EDIT','PARCEL_ARC_EDIT','חלקות לעריכה','קווים לעריכה','נקודות לעריכה']:
                            del_fields_psafas(i)
                        if i.name.encode('UTF-8') == 'חלקות בנק"ל מקור':
                            lyr["path_before"] = i
                        if i.name.encode('UTF-8') == 'חלקות לעריכה':
                            lyr["path_after"] = i
                            lyr['GDB']        = str(os.path.dirname(i.dataSource))
                        if i.name.encode('UTF-8') == 'חלקות להכנסה':
                            lyr["Parcels_inProc_edit"] = i


        if lyr["path_after"] == '':
            pythonaddins.MessageBox("Layer:{} is missing  ".format('חלקות לעריכה'),'INFO',0)

        if lyr["path_before"] == '':
            pythonaddins.MessageBox("Layer:{} is missing  ".format('חלקות בנק"ל מקור'),'INFO',0)

        if (lyr["path_after"] != '') and (lyr["path_before"] != ''):
            Parcel_data(lyr["path_after"],lyr["path_before"],lyr['GDB'],lyr["Parcels_inProc_edit"])


            
class cheack_fields(object):
    """Implementation for Add_in_Fields_addin.cheack_fields (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        
        def add_field(fc,field,Type = 'TEXT'):
            TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
            if not TYPE:
                arcpy.AddField_management (fc, field, Type)

        def Error_Table(gdb,List_to_add):
            '''
            [INFO]
                get list where: [['Error_Type','Text'],['Error_Type','Text']]
            input:
                List_to_add = [['parcel','22-33-44'],['point','12312_56756']]
            OutPut:
                table with errors
            '''

            full_path = gdb                  + '\\' + 'Error_Table'

            if not arcpy.Exists(full_path):
                arcpy.CreateTable_management(gdb,'Error_Table')

            fields = ['Error_Code','Error_Type','Message']
            for i in fields:
                try:
                    add_field(full_path,i,'TEXT')
                except:
                    pass

            Error_Type = [i[0] for i in List_to_add]

            with arcpy.da.UpdateCursor(full_path,['Error_Code','Error_Type','Message']) as cursor:
                for row in cursor:
                    if row[0] in Error_Type[0]:
                        cursor.deleteRow()
            del cursor

            for row in List_to_add:
                insert = arcpy.InsertCursor (full_path)
                in_row               = insert.newRow()
                in_row.Error_Code    = row[0]
                in_row.Error_Type    = row[1].decode('UTF-8')
                in_row.Message       = row[2].decode('UTF-8')
                insert.insertRow   (in_row)

            return full_path

        def Check_accurancy_None(fc):

            def add_field(fc,field,Type = 'TEXT'):
                TYPE = [i.name for i in arcpy.ListFields(fc) if i.name == field]
                if not TYPE:
                    arcpy.AddField_management (fc, field, Type)
            
            list_fields = ["GUSH_NUM","GUSH_SUFFIX","PARCEL","LEGAL_AREA","PNUMTYPE","TALAR_NUMBER","TALAR_YEAR","SYS_DATE","KEY"]

            add_field(fc,'KEY',Type = 'TEXT')
            error = []
            all_good = False
            with arcpy.da.UpdateCursor(fc,list_fields) as cursor:
                for row in cursor:
                    row[-1] = str(row[0]) +'-' + str(row[1])+ '-' + str(row[2])
                    li = [i for i in zip(list_fields,row) if i[1] is None]
                    if len(li) > 0:
                        error.append(li)
                        print li
                    else:
                        all_good = True
                    cursor.updateRow(row)
            pythonaddins.MessageBox('there is None in layers: {}'.format(error),'INFO',0)
            if all_good:
                pythonaddins.MessageBox('all fields seems ok','INFO',0)

            error_list =  [['1',"שדה עם ערכים חסרים",str(i)] for i in error]
            if not error_list:
                error_list = [['1','','']]

            add_field(fc,"accurancy",'TEXT')
            x = [row[0] for row in arcpy.da.SearchCursor (fc,["KEY"])]

            all_good_2 = True
            error_dupli = []
            with arcpy.da.UpdateCursor(fc,["KEY", "accurancy"]) as cursor:
                    for row in cursor:
                            row[1] = x.count(row[0])
                            if row[1] > 1:
                                pythonaddins.MessageBox('there is parcel thats have more then 1 appearnce: {}'.format(row[0]),'INFO',0)
                                error_dupli.append(['2','חלקה המופיעה יותר מפעם אחת',str(row[0])])
                                all_good_2 = False
                            else:
                                cursor.updateRow(row)

            if all_good_2:
                pythonaddins.MessageBox('no duplicate','INFO',1)

            error_list = error_list + error_dupli

            return error_list


        mxd = arcpy.mapping.MapDocument('current')
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        if df:    
            lyr = arcpy.mapping.ListLayers(mxd,"חלקות לעריכה", df)[0]
            gdb = os.path.dirname(lyr.dataSource)
        if lyr:
            error_list = Check_accurancy_None (lyr)
            Error_Table          (gdb,error_list)


class End_Job(object):
    """Implementation for Add_in_Fields_addin.cheack_fields (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):

        def Get_Gdb_path():
            MXD = arcpy.mapping.MapDocument (r'CURRENT')
            df = MXD.activeDataFrame
            lyrs = arcpy.mapping.ListLayers(MXD, "חלקות לעריכה", df)
            if lyrs:
                if lyrs[0].isFeatureLayer:
                    return lyrs[0].workspacePath

        def Get_Mxd_path():
            MXD      = arcpy.mapping.MapDocument (r'CURRENT')
            path_mxd = MXD.filePath
            return   path_mxd

        def Call_Service():

            gdb = Get_Gdb_path()
            mxd = Get_Mxd_path()

            #url = r"http://etm:804/CadasterEditWS/CadsterEditJobs.asmx/CloseEditingTalar"
            url = "http://etm:804/CadasterEditWS/CadsterEditJobs.asmx/CheckParcelNum"
            desc_list = dict([i.split(":") for i in ((arcpy.mapping.ListDataFrames((arcpy.mapping.MapDocument(r'CURRENT')), "*")[0]).description.split(";\r\n")) if i.split(":")[0] <> u''])
            desc_list['gdbEdited'] = gdb
            values = {'gdbEdited':str(desc_list['gdbEdited']),
                    'EditId':str(desc_list['EditId']),
                    'UserName':str(desc_list['UserName']),
                    'IsProd':str(desc_list['IsProd']),
                    'editProcess':str(desc_list['editProcess'])                
                    }
            data = urllib.urlencode(values)

            print url + "?" + data
            #req = urllib2.Request(url + "?" + data, None, values)
            #print req
            response = urllib2.urlopen(url + "?" + data)
            the_page = response.read()
            print the_page
            return the_page

        def XML_to_Table(xml_string):

            MXD = arcpy.mapping.MapDocument (r'CURRENT')
            df = MXD.activeDataFrame
            lyrs = arcpy.mapping.ListLayers(MXD, "חלקות לעריכה", df)
            if lyrs:
                if lyrs[0].isFeatureLayer:
                    print lyrs[0].workspacePath
                    gdb = lyrs[0].workspacePath

                    xml_string = xml_string.replace("-","")
                    #print xml_string
                    root = ET.fromstring(xml_string)
                    data = root[0]

                    rows = [ParcelError for ParcelError in [ParcelErrors for ParcelErrors in data]]

                    if len(rows) == 0:
                        #pythonaddins.MessageBox('לא נמצאו שגיאות','INFO',0)
                        pythonaddins.MessageBox('No Errors Found','INFO',0)
                    else:
                        fields = [field.tag.replace("{http://tempuri.org/}", "") for field in rows[0].getchildren() if field.tag.replace("{http://tempuri.org/}", "") <> "ErrInfo"]
                        err_infos = rows[0][-1].getchildren()
                        for err_info in err_infos:
                            fields.append(err_info.tag.replace("{http://tempuri.org/}", ""))
                        print fields

                        
                        arcpy.CreateTable_management(gdb, "Errors")
                        for field in fields:
                            arcpy.AddField_management(gdb + "\\Errors", field, "TEXT")
                            
                        all_values = []
                        for row in rows:
                            fields = [field.tag.replace("{http://tempuri.org/}", "") for field in row.getchildren() if field.tag.replace("{http://tempuri.org/}", "") <> "ErrInfo"]
                            values = [field.text for field in row.getchildren() if field.text not in ['\n', '\n\n']]
                            err_infos = row[-1].getchildren()
                            for err_info in err_infos:
                                fields.append(err_info.tag.replace("{http://tempuri.org/}", ""))
                                values.append(err_info.text)
                            #print zip(fields, values)
                            all_values.append(zip(fields, values))

                        rows = arcpy.InsertCursor(gdb + "\\Errors")
                        for values in all_values:
                            row = rows.newRow()
                            print values
                            for row_val in values:
                                row.setValue(row_val[0], row_val[1])
                            rows.insertRow(row)


                        del row
                        del rows

                        arcpy.mapping.AddTableView(df, gdb + "\\Errors")
                        pythonaddins.MessageBox('Error table have been added to the map','INFO',0)
                        #pythonaddins.MessageBox('טבלת שגיאות נוספה למפה','INFO',0)
        # # # Main # # #

        xml_string = Call_Service()
        XML_to_Table(xml_string)
