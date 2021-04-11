# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # P S A F A S    T O O L S # # # # # # # # # # # # # # # 

import os,ast,sys
import arcpy

from Layer_Class   import *
from Basic_Func    import *
from Advanced_Func import *

'''
Delete_small_double_parcel
NewGushim
CheckIfSkipProcess
Sub_Processing
PrePare_Data
CheckResultsIsOK
Calculate_Area_Rashum
Get_Attr_From_parcel
connect_parcel_to_sett
get_default_Snap_border
get_no_node_vertex
clean_slivers_by_vertex
add_err_pts_to_mxd
ChangeFieldNames
Parcel_data
Insert_to_table
update_curves
Fix_Multi_part_Bankal
names_curves
Update_Layer_Curves_By_ID
Delete_curves_out_AOI
Get_Status_Field
Create_Line_AOI
Find_stubbern_lines
dissolve_parts             #  not in use
'''

def Delete_small_double_parcel(path):

    Multi_to_single(path)

    data       = [[str(row[0]) +'-' + str(row[1])+ '-' + str(row[2]),row[3]] for row in arcpy.da.SearchCursor(path,["GUSH_NUM","GUSH_SUFFIX","PARCEL","SHAPE@AREA",])]
    df         = pd.DataFrame(data = data,columns = ['KEY','area'])
    df['Rank'] = df.groupby('KEY')['area'].rank(method='dense',ascending=False)
    to_del     = {i[1]:i[0] for i in df[df['Rank'] > 1].values.tolist()}
    len_del    = len(to_del)

    if len_del > 0:
        print_arcpy_message("Found: {} parcels that are double parcels, trying to fix it".format(str(len_del)),2)
        with arcpy.da.UpdateCursor(path,["GUSH_NUM","GUSH_SUFFIX","PARCEL","SHAPE@AREA"]) as Ucursor:
            for row in Ucursor:
                key = row[3]
                if to_del.get(key):
                    if to_del[key] == str(row[0]) +'-' + str(row[1])+ '-' + str(row[2]):
                        Ucursor.deleteRow()


def NewGushim(parcel_tazar, parcel_all_bankal,layer_f):

    print_arcpy_message("START Func: NewGushim",1)

    layer_finish = layer_f+'Temp'
    
    arcpy.Select_analysis                  (layer_f,layer_finish)
    arcpy.MakeFeatureLayer_management      (parcel_all_bankal, "in_memory\\bankal")
    arcpy.SelectLayerByLocation_management ("in_memory\\bankal", 'INTERSECT', parcel_tazar,"2000 Meters")
        
    arcpy.Dissolve_management              ("in_memory\\bankal", "in_memory\\sub_gush_all","GUSH_NUM", "", "SINGLE_PART")
    arcpy.Dissolve_management              (layer_finish, "in_memory\\layer_finish_gush","GUSH_NUM", "", "SINGLE_PART")     
        
    Gush_stay   = []
    Gush_change = []
        
    parcel_GUSH_bankal = [[i.GUSH_NUM,i.SHAPE] for i in arcpy.SearchCursor("in_memory\\sub_gush_all")]
    with arcpy.da.SearchCursor("in_memory\\layer_finish_gush",["GUSH_NUM","SHAPE@"]) as cursor:
                for row in cursor:
                        if parcel_GUSH_bankal:
                            if str(row[0]) == str(parcel_GUSH_bankal[0][0]):
                                    if row[1].union(parcel_GUSH_bankal[0][1]) == row[1]:
                                            Gush_stay.append(row[0])
                                    else:
                                            Gush_change.append(row[0])
        
    if len(Gush_change) > 0:
                print_arcpy_message ("there is gush that moved, name: {}".format(Gush_change),status = 1)   

        
    gushim_tazar = list(set([row.GUSH_NUM for row in arcpy.SearchCursor(parcel_tazar)]))
    gushim_all = list(set([row.GUSH_NUM for row in arcpy.SearchCursor("in_memory\\sub_gush_all")]))
    new_gushim = [g for g in gushim_tazar if g not in gushim_all]
    if len(new_gushim) > 0:
                print_arcpy_message("there is  New Gush in the tazar name {}".format(new_gushim),status = 1) 
    else:
                print_arcpy_message("there is no New Gush in the tazar",status = 1) 

    arcpy.Delete_management(layer_finish)


def Sub_Processing(bankal,modad_c,points,pnt_modad,Lines,line_modad,border,copy_tazar,parcel_all,gdb):
    
    def Check_If_Sub_Processing(after_del,bankal):
        No_geo_changes = True
        dic_AREA_ID = {i.PARCEL_ID:i.SHAPE_Area for i in arcpy.SearchCursor(after_del)}
        with arcpy.da.SearchCursor(bankal,['PARCEL_ID','SHAPE@AREA']) as cursor:
            for row in cursor:
                if dic_AREA_ID.has_key(row[0]):
                    changed = abs(row[1] - dic_AREA_ID[row[0]])
                    if changed > 0.1:
                        No_geo_changes = False
                        break
        return No_geo_changes

    after_del  = gdb + '\\' + 'afetr_del'

    if not arcpy.Exists(after_del):
        Delete_polygons (bankal,border,after_del)

    No_geo_changes = Check_If_Sub_Processing(after_del,bankal)
    arcpy.Delete_management (after_del)

    if No_geo_changes:
        print_arcpy_message     ("Sub Processing was acctiveted",status = 1)
        path_before      = gdb + '\\' + 'Copy_bankal'
        arcpy.Select_analysis (bankal,path_before)


        # insert: polygons
        Update_Polygons (bankal,modad_c,'')

        Parcel_data                (bankal,path_before,copy_tazar)
          
        # insert: Points
        Delete_polygons          (points,border)
        arcpy.Append_management  (pnt_modad,points,"NO_TEST")


                # מחיקת כפילויות אם יש
        add_field                 (points,'X_Y','TEXT')
        arcpy.CalculateField_management(points, "X_Y", "calc(!shape.centroid.X!,!shape.centroid.Y!)", "PYTHON_9.3", "def calc (x,y):\\n    return str(round(x,1)) + '-' + str(round(y,1))")

        del_identical   (points,'X_Y')

        # insert Lines

        Layer_Management        (Lines).Select_By_Location('HAVE_THEIR_CENTER_IN',border)

        arcpy.Append_management (line_modad,Lines,"NO_TEST")

        # Delete Duplicate Lines
        Delete_Duplic_Line(Lines)

        print_arcpy_message     ("# # # # # # # F I N I S H # # # # # #",status = 1)
        sys.exit()


def CheckIfSkipProcess(parcel_bankal,PARCELS_inProc_edit,gdb):

    conti = True
    intersect  = gdb + '\\' + 'inter'
    Bankal_cut = gdb + '\\' + 'cut_bankal'
    Layer_Management(parcel_bankal).Select_By_Location("INTERSECT",PARCELS_inProc_edit,"",Bankal_cut)
    name_ID    = 'FID_' + os.path.basename(Bankal_cut)
    arcpy.Intersect_analysis([Bankal_cut,PARCELS_inProc_edit],intersect)
    dic      = {i[0]:[round(i[1],1),i[2],i[3]] for i in arcpy.da.SearchCursor(intersect,[name_ID,'SHAPE_Area','GUSH_NUM','PARCEL'])}
    list_ref = [[i.OBJECTID,round(i.SHAPE_Area,1)] for i in arcpy.SearchCursor(Bankal_cut)]
    for n in list_ref:
        if dic.has_key(n[0]):
            if n[1] == dic[n[0]][0] and dic[n[0]][1] == dic[n[0]][2]:
                print (n)
                pass
            else:
                conti = False
    arcpy.Delete_management(intersect)
    arcpy.Delete_management(Bankal_cut)
    return conti

def PrePare_Data(parcel_bankal,parcels_copy,points_copy,Point_bankal,GDB,name_bankal,name_tazar):

    '''
    INPUTS
    1) parcel_bankal - שכבת החלקות של הבנק"ל
    2) parcels_copy  - שכבת החלקות של המודד
    3) points_copy   - שכבת נקודות המודד
    4) Point_bankal  - שכבת נקודות הבנק"ל
    5) GDB           - בסיס הנתונים בו ישמרו השכבות
    6) name_bankal   - שם השדה של שם הנקודה בבנק"ל
    7) name_bankal   - שם השדה של שם הנקודה בתצ"ר

    OUTPUTS
    1) AOI               - אזור העבודה החדש
    2) tazar_border      - גבול התצ"ר
    3) Curves            - קשתות של אזור העבודה
    4) parcel_Bankal_cut - חיתוך של הבנק"ל כל חלקה בטווח 10 מטר מהתצ"ר תיכנס
    5) Point_bankal_Cut  - חיתוך של נקודות הבנק"ל, כל נקודה בטווח 10 מטר מהתצ"ר תיכנס
    '''

    # #Prepare data

    parcel_Bankal_cut  = GDB + '\\' + 'Bankal_Cut'
    tazar_border       = GDB + '\\' + 'tazar_border'
    AOI                = GDB + '\\' + 'AOI'
    Point_bankal_Cut   = GDB + '\\' + 'Point_bankal_Cut'
    Holes_data         = GDB + '\\' + 'Holes_Prepare_data'


    # Create Tazar Border, Curves
    arcpy.Dissolve_management                  (parcels_copy,tazar_border)

    # Create Parcel Bankal For AOI
    Layer_Management(parcel_bankal).Select_By_Location("INTERSECT",tazar_border,"10 Meters",parcel_Bankal_cut)

    add_field                       (parcel_Bankal_cut, "AREA_Orig","DOUBLE")
    arcpy.CalculateField_management (parcel_Bankal_cut, "AREA_Orig","!shape.area!", "PYTHON_9.3")

    # Cut Points From Bankal
    Layer_Management(Point_bankal).Select_By_Location("INTERSECT",tazar_border,"10 Meters",Point_bankal_Cut)

    Move_Vertices_By_Name                      (parcel_Bankal_cut,Point_bankal_Cut,name_bankal,points_copy,name_tazar) # לשים לב לשדות שמות הנקודות

    Delete_polygons         (parcel_Bankal_cut,parcels_copy,AOI)
    arcpy.Append_management (parcels_copy,AOI,'NO_TEST')

    # מחיקה של חלקים הקטנים מ-20 אחוז של גודלם המקורי
    Multi_to_single                         (AOI)
    arcpy.AddField_management               (AOI, "OVERLAP_PRCT", "DOUBLE")
    arcpy.CalculateField_management         (AOI,"OVERLAP_PRCT", "((!SHAPE_Area!  / !AREA_Orig!) * 100)", "PYTHON")
    arcpy.MakeFeatureLayer_management       (AOI,'parcel_Bankal_cut_Layer',"\"OVERLAP_PRCT\" < 20") 
    arcpy.Select_analysis                   ('parcel_Bankal_cut_Layer',Holes_data)
    arcpy.DeleteFeatures_management         ('parcel_Bankal_cut_Layer')

    # Update_Polygons                         (AOI,parcels_copy)
    Curves = generateCurves                 (AOI)
    Update_Polygons                         (AOI,parcels_copy)

    Multi = Multi_to_single                         (AOI)
    if Multi:
        print_arcpy_message("You have Multi layer after insert new tazar")

    return AOI,tazar_border,Curves,parcel_Bankal_cut,Point_bankal_Cut


def CheckResultsIsOK(parcel_all,tazar_border,num):

    GDB       = os.path.dirname(tazar_border)
    Holes     = GDB +'\\' + 'Holes_Check_'     + str(num)
    Intersect = GDB +'\\' + 'Intersect_Check_' + str(num)

    holes,intersect = topology         (parcel_all)

    if holes:
        Layer_Management    (holes).Select_By_Location   ('INTERSECT',tazar_border,0,Holes)
        Delete_By_area        (Holes,0.1)
        holes_count         = int(str(arcpy.GetCount_management(Holes)))
        print_arcpy_message  ("holes: {}".format(holes_count,1))
    else:
        holes_count = 0
    
    if intersect:
        Layer_Management      (intersect).Select_By_Location  ('INTERSECT',tazar_border,0,Intersect)
        Delete_By_area        (Intersect,0.1)
        intersect_count       = int(str(arcpy.GetCount_management(Intersect)))
        print_arcpy_message   ("Intersect: {}".format(intersect_count),1)
    else:
        intersect_count = 0

    return True if ((holes_count == 0)  and (intersect_count == 0)) else False



def Calculate_Area_Rashum(PARCEL_ALL_FINAL):
    
    def find_problem(Area_rasum,Shape_area,delta):

        minus = abs(Area_rasum - Shape_area)
        return 'Warning, Delta is to big' if minus > delta else 'Ok'

    def math_delta_rashum(area_rashum):

        area_rashum = float(area_rashum)
        delta1 = (0.3 * (math.sqrt(area_rashum)) + (0.005 * area_rashum))
        delta2 = (0.8 * (math.sqrt(area_rashum)) + (0.002 * area_rashum))

        return delta1 if delta1 > delta2 else delta2

    fields = [add_field(PARCEL_ALL_FINAL,i[0],i[1]) for i in [["GAP", "DOUBLE"],["delta", "DOUBLE"],["Check", "TEXT"]]]
        
    with arcpy.da.UpdateCursor(PARCEL_ALL_FINAL,["LEGAL_AREA","SHAPE_Area","GAP","delta","Check"]) as cursor:
        for row in cursor:
            if row[0]:
                delta  = math_delta_rashum(row[0])
                row[3] = delta
                row[2] = abs(row[1] - row[0])- delta
                row[4] = find_problem(row[0],row[1],delta)
                cursor.updateRow (row)
    del cursor


def Get_Attr_From_parcel(parcel_all_final,tazar_copy):

    Uni_data = len(list(set([i.LOCALITY_ID for i in arcpy.SearchCursor(parcel_all_final) if i.LOCALITY_ID])))
    fields = [["REGION_NAME","TEXT"],["REGION_ID","LONG"],["COUNTY_NAME","TEXT"],["COUNTY_ID","LONG"],["REG_MUN_ID","LONG"],["LOCALITY_NAME","TEXT"],["LOCALITY_ID","LONG"],["REG_MUN_NAME","TEXT"],["WP","LONG"]]
    for i in fields: add_field(tazar_copy,i[0],i[1])
    if Uni_data == 1:
        data = [[i.REGION_NAME,i.REGION_ID,i.COUNTY_NAME,i.COUNTY_ID,i.REG_MUN_ID,i.LOCALITY_NAME,i.LOCALITY_ID,i.REG_MUN_NAME,i.WP] for i in arcpy.SearchCursor(parcel_all_final) if i.LOCALITY_ID][0]
        with arcpy.da.UpdateCursor(tazar_copy,["REGION_NAME","REGION_ID","COUNTY_NAME","COUNTY_ID","REG_MUN_ID","LOCALITY_NAME","LOCALITY_ID","REG_MUN_NAME","WP"]) as Ucursor:
            for row in Ucursor:
                row[:] = data[:]
                Ucursor.updateRow(row)
    else:
        print_arcpy_message ("Get_Attr_From_parcel coudnt give names",2)

def connect_parcel_to_sett(layer,sett,bankal_c,sett_fields = ['MUN_HEB','MACHOZ','NAFA1','SETTEL_NAM']):

    '''
    layer       = שכבה אליה יכנסו מספר מזהה ושם הישוב
    sett        = שכבת הישובים של מפ"י
    sett_fields = 1) CODE field , 2) NAME field
    '''

    list_fields   = [['REG_MUN_NAME','TEXT'],['REGION_NAME','TEXT'],['COUNTY_NAME','TEXT'],['LOCALITY_NAME','TEXT']]

    fields_name   = [i[0] for i in list_fields]

    add_op = [add_field(layer,i[0],i[1]) for i in list_fields]

    if sett != '':
        sett_fields.insert                      (0, 'SHAPE@') 
        fields_name.insert                      (0, 'SHAPE@')
        arcpy.MakeFeatureLayer_management       (sett,'sett_layer')
        arcpy.SelectLayerByLocation_management  ('sett_layer','INTERSECT',layer)
        data = [[i[0],i[1],i[2],i[3],i[4]] for i in arcpy.da.SearchCursor('sett_layer',sett_fields)]
        with arcpy.da.UpdateCursor (layer, fields_name) as cursor:
            for row in cursor:
                geom   = row[0]
                midpnt = geom.labelPoint
                for i in data:
                    if i[0].distanceTo(midpnt) == 0:
                        row[1:] = i[1:]
                        cursor.updateRow(row)

        del cursor

    arcpy.JoinField_management (layer, 'REGION_NAME',bankal_c , 'REGION_NAME',['REG_MUN_ID','REGION_ID','COUNTY_ID','LOCALITY_ID'])


def get_no_node_vertex(AOI,tazar_border,Modad_node,PARCEL_ALL_node):

    '''
    [INFO] -  בודק אם המודד שכח לתת נקודת חיצונית, ולכן אין אנו יכולים לחבר אותה
    Inputs:
    1) AOI             - Result of the tool after runing
    2) tazar_border    - border of the tazar
    3) Modad_node      - points coming from the modad
    4) PARCEL_ALL_node - Point of the PARCAL_ALL before starting to change him
    OUTPUT:
    1) points layer of missing vertxes
    '''

    GDB = os.path.dirname(AOI)

    print_arcpy_message                       ("START Func: get no node vertex",1)

    Point_AOI = Layer_Management(AOI).Get_vertxs_As_Point ()

    arcpy.MakeFeatureLayer_management         (Point_AOI,"AOI_lyr")
    arcpy.SelectLayerByLocation_management    ("AOI_lyr","BOUNDARY_TOUCHES",tazar_border,0.01)
    arcpy.SelectLayerByLocation_management    ("AOI_lyr","INTERSECT",Modad_node,0.01,"REMOVE_FROM_SELECTION")
    arcpy.SelectLayerByLocation_management    ("AOI_lyr","INTERSECT",PARCEL_ALL_node,0.01,"REMOVE_FROM_SELECTION")
    arcpy.Select_analysis                     ("AOI_lyr",GDB + "\\" + "Possible_Error_points")

    return GDB + "\\" + "Possible_Error_points"



def clean_slivers_by_vertex(PARCEL_ALL,SLIVERS_CLEAN,border,Dis_search,PARCEL_ALL_lyr):

    print_arcpy_message ("START Func: clean slivers by vertex")

    '''
    [INFO] -  מוחק לפי ליניאריות ומרחק את הוורטקסים שנמצאים ליד החורים של התצ"ר
    INPUT-
    1) PARCEL_ALL     - שכבת רצף
    2) SLIVERS_CLEAN  - חורים של הרצף
    3) border         - גבול התצ"ר
    4) Dis_search     - מרחק חיפוש הוורטקסים
    5) PARCEL_ALL_lyr - שכבת הפלט
    '''

    gdb = os.path.dirname(border)

    tazar_border = 'in_memory\TazarBorderDiss'
    arcpy.Dissolve_management (border,tazar_border)

    conn = sqlite3.connect(':memory:')
    c    = conn.cursor()
    c.execute('''CREATE TABLE old_vertices(pnt_num real, x real, y real, xy text, part real, oid real)''')
    c.execute('''CREATE TABLE new_vertices(pnt_num real, x real, y real, xy text, part real, oid real)''')


    c.execute('''CREATE TABLE vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

    c.execute('''CREATE TABLE sliver_vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

    c.execute('''CREATE TABLE border_vertices(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')

    arcpy.Select_analysis            (PARCEL_ALL, PARCEL_ALL_lyr)
    
    arcpy.CopyFeatures_management        (PARCEL_ALL_lyr,gdb + "\\PARCEL_ALL_lyr_COPY_DEL")
    
    VerticesToTable2(PARCEL_ALL_lyr, "vertices",c)
    VerticesToTable2(SLIVERS_CLEAN, "sliver_vertices",c)
    VerticesToTable2(tazar_border, "border_vertices",c)


    parcel_common_vertices = [row for row in c.execute('''SELECT * FROM vertices
                                                                                                left join sliver_vertices
                                                                                                on vertices.xy = sliver_vertices.xy
                                                                                                where  sliver_vertices.xy is not null''')]
                                                                                            
    border_common_vertices = [row for row in c.execute('''SELECT * FROM border_vertices
                                                                                                left join sliver_vertices
                                                                                            on border_vertices.xy = sliver_vertices.xy
                                                                                                where  sliver_vertices.xy is not null''')]
                                                                                                

    distance_vertices = [[p[:8] + b[:8],math.sqrt(((p[1]-b[1])**2)+((p[2]-b[2])**2))] for p in parcel_common_vertices for b in border_common_vertices if math.sqrt(((p[1]-b[1])**2)+((p[2]-b[2])**2))\
         < Dis_search or (float("{0:.2f}".format(p[1])) == float("{0:.2f}".format(b[1])) and float("{0:.2f}".format(p[2])) == float("{0:.2f}".format(b[2])))]

                                           
    rows = arcpy.UpdateCursor(PARCEL_ALL_lyr)
    for row in rows:
            geometry = row.Shape
            oid = row.OBJECTID
            pts = []
            poly_vertices = [r for r in distance_vertices if r[0][5] == oid]
            for part in geometry:
                    for pt in part:
                            if str(type(pt)) <> "<type 'NoneType'>":
                                    num_point = 0
                                    #print str(pt.X) + "--" + str(pt.Y)
                                    this_x = float("{0:.2f}".format(pt.X))
                                    this_y = float("{0:.2f}".format(pt.Y))      
                                    this_vertex = [p for p in poly_vertices if float("{0:.2f}".format(p[0][1])) == this_x and float("{0:.2f}".format(p[0][2])) == this_y]
                                    if this_vertex:
                                            if this_vertex[0][0][8] == None:
                                                    if this_vertex[0][0][7] < 0.7 and this_vertex[0][0][6] == 1:
                                                        print ("pseodo: delete vertex")
                                                    else:
                                                            #print "pseodo, but important: keep the vertex"
                                                            point = pt
                                                            pts.append(point)
                                            # tazar point in buffer
                                            else:
                                                    # check minimum distance
                                                    the_minimum_vertex = [v for v in this_vertex if v[1] == min([i[1] for i in this_vertex])]
                                                    point = arcpy.Point(the_minimum_vertex[0][0][9], the_minimum_vertex[0][0][10])
                                                    pts.append(point)
                                    # point not on sliver: keep the vertex
                                    else:
                                            point = pt
                                            pts.append(point)
                                    if num_point == 0:
                                            first_point = point
                                    num_point = num_point + 1
            polygon = PtsToPolygon(pts)
            if pts[0] <> pts[-1] and first_point:
                    #print "ooops.... - polygon not closed"
                    pts.append(first_point)
            row.Shape       = polygon
            row.PARCEL_ID   > 0
            rows.updateRow(row)

    arcpy.Delete_management(gdb + "\\PARCEL_ALL_lyr_COPY_DEL")
    return PARCEL_ALL_lyr




def get_default_Snap_border(point_bankal,tazar,Distance_min):

    '''
    [INFO] - בודק את נקודות הבנקל ליד התצ"ר במידה ויש 2 נקודות בנקל קרובות אחת לשניה, הוא נותן את המרחק הזה כברירת מחדל
    INPUT-
    1) point_bankal - שכבת נוקודת בנקל
    2) tazar        - שכבת תצ"ר של המודד
    3) Distance_min - מה המינימום, יופעל במידה שמרחק הנקודות גדול מידי
    OUTPUT-
    1) המרחק בקטן ביותר בין שני נקודות בנק"ל בסמוך לתצר
    '''

    GDB = os.path.dirname(tazar)

    PntTmp = r'in_memory' + '\\' + 'PntTmp'
    buffer = r'in_memory' + '\\' + 'buffer'
    dissol = r'in_memory' + '\\' + 'dissol'
    multiP = r'in_memory' + '\\' + 'multiP'

    def Getmin(list1,Dis_min = 2):
        li = [i[2] for i in list1 if i[2] < 1]
        return min(li) - 0.01 if li else Dis_min

    arcpy.MakeFeatureLayer_management           (point_bankal,'path_lyr')
    arcpy.SelectLayerByLocation_management      ('path_lyr','WITHIN_A_DISTANCE',tazar,'5 Meters')
    arcpy.Select_analysis                       ('path_lyr',PntTmp)
    arcpy.MakeFeatureLayer_management           (PntTmp,'PntTmp_lyr')
    arcpy.SelectLayerByLocation_management      ('PntTmp_lyr',"COMPLETELY_WITHIN",tazar)
    arcpy.SelectLayerByAttribute_management     ('PntTmp_lyr',"SWITCH_SELECTION")

    arcpy.Buffer_analysis                   ('PntTmp_lyr',buffer,0.5)
    arcpy.Dissolve_management               (buffer,dissol)
    arcpy.MultipartToSinglepart_management  (dissol,multiP)


    with arcpy.da.UpdateCursor(multiP,['SHAPE@AREA']) as cursor:
        for row in cursor:
            if row[0] < 0.8:
                cursor.deleteRow()

    arcpy.MakeFeatureLayer_management       (PntTmp,'path2_lyr')
    arcpy.SelectLayerByLocation_management  ('path2_lyr','INTERSECT',multiP)

    dis_point  = [[row[0],row[1]] for row in arcpy.da.SearchCursor('path2_lyr',['OBJECTID','SHAPE@'])]
    list_dis   = [[row[1],n[0],row[0].distanceTo(n[1])] for n in dis_point for row in arcpy.da.SearchCursor('path2_lyr',['SHAPE@','OID@']) if row[0].distanceTo(n[1]) > 0]


    Min_dist = Getmin(list_dis,Distance_min)
    print_arcpy_message(Min_dist, status=1)
    return Min_dist



def ChangeFieldNames(parcel,line,point):
    '''
        Take 3 layers, Changing fields from Source layers to bankal format
    '''

    wrong = {'TALAR_NUM':'TALAR_NUMBER','GushNum':'GUSH_NUM','GushSuffix':'GUSH_SUFFIX','ParcelName':'PARCEL','LegalArea':'LEGAL_AREA','GUSHNUM':'GUSH_NUM','GUSHSUFFIX':'GUSH_SUFFIX','PARCEL_FINAL':'PARCEL','LEGALAREA':'LEGAL_AREA'}

    List_fields = [[str(i.name),wrong[str(i.name)]] for i in arcpy.ListFields(parcel) if str(i.name) in list(wrong.keys())]

    if List_fields:

        print_arcpy_message("Changing Fields",status = 1)
        list_layers = [parcel,line,point]

        for lyr in list_layers:
            for field in List_fields:
                layer   = os.path.basename(lyr)
                parcels = [os.path.basename(parcel)]
                others  = [os.path.basename(line),os.path.basename(point)]
                if layer in others:
                    if field[0] in ['GushNum','GUSHNUM']:
                        add_field(lyr,field[1],'LONG')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")
                    if field[0] in ['GushSuffix','GUSHSUFFIX']:
                        add_field(lyr,field[1],'SHORT')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")
                if layer in parcels:
                    if field[0] in ['GushNum','GUSHNUM']:
                        add_field(lyr,field[1],'LONG')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

                    if field[0] in ['GushSuffix','ParcelName','PARCEL_FINAL','GUSHSUFFIX']:
                        add_field(lyr,field[1],'SHORT')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

                    if field[0] in ['LegalArea','LEGALAREA']:
                        add_field(lyr,field[1],'DOUBLE')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"] * 1000"  , "VB", "")

                    if field[0] in ['TALAR_NUM']:
                        add_field(lyr,field[1],'LONG')
                        arcpy.CalculateField_management  (lyr, field[1]  , "["+field[0]+"]"  , "VB", "")

    try:
        arcpy.CalculateField_management  (parcel, 'PARCEL', "int( ''.join ([i for i in !ParcelName! if i.isdigit()]))", "PYTHON" ) 
    except:
        arcpy.CalculateField_management  (parcel, 'PARCEL', "int( ''.join ([i for i in !PARCEL_FINAL! if i.isdigit()]))", "PYTHON" ) 


def add_err_pts_to_mxd(our_gdb, folder, data_source,CURRENT):

    # copy 3 error fcs from data_source (demo.gdb) to our_gdb
    err_fc_names = ["Errors_Line", "Errors_Point", "Errors_Polygon"]
    for err_fc_name in err_fc_names:
        arcpy.DeleteRows_management(data_source + "\\" + err_fc_name)
        arcpy.Copy_management(data_source + "\\" + err_fc_name, our_gdb + "\\" + err_fc_name)
    
    mxd = arcpy.mapping.MapDocument(CURRENT)
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
    for root, dir, files in os.walk(folder):
        for file in files:
            file_full_path  = root + "\\" + file
            if file == "Errors_Line.lyr" or file == "Errors_Point.lyr" or file == "Errors_Polygon.lyr" or file == "Possible_Error_points.lyr" or file == "PARCEL_ALL_EDIT_copy.lyr" or file == "PARCEL_NODE_EDIT_copy.lyr" or file == "PARCEL_ARC_EDIT_copy.lyr":
                addLayer        = arcpy.mapping.Layer(file_full_path)
                arcpy.mapping.AddLayer(df, addLayer, "TOP")
                layer = arcpy.mapping.ListLayers(mxd, "", df)[0]
                try:
                    mxd.findAndReplaceWorkspacePaths(data_source, our_gdb)
                except:
                    print ("Coudnt replace Data Source")
        arcpy.RefreshActiveView()



def Parcel_data(path_after,path_before,copy_tazar):
    
    def Get_Runing_numbers(data1):
        for i in range(len(data1)):
            if data1[i][1] == data1[i-1][1]:
                if data1[i][0]+1 == data1[i-1][0]:
                    print ("its ok ,in {} value is equal with: {}").format(data1[i][2],data1[i-1][2])
                else:
                    print ("in {} value is not equal with: {}").format(data1[i][2],data1[i-1][2])
            else:
                pass


    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("""CREATE TABLE Before_Table (
                        PARCEL     INTEGER,
                        GUSH_NUM   INTEGER,
                        KEY        text
                        )""")

    c = conn.cursor()
    c.execute("""CREATE TABLE Table_After (
                        PARCEL     INTEGER,
                        GUSH_NUM   INTEGER,
                        KEY        text
                        )""")

    for i in arcpy.SearchCursor(path_before):
        c.execute ("INSERT INTO Before_Table VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM)+"-"+ str(i.GUSH_SUFFIX)+"')")

    for i in arcpy.SearchCursor(path_after):
        c.execute ("INSERT INTO Table_After VALUES (" + str(i.PARCEL) +','+ str(i.GUSH_NUM) + ",'"+str(i.PARCEL)+"-"+str(i.GUSH_NUM) +"-"+ str(i.GUSH_SUFFIX)+ "')")


    count_before = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Before_Table group by KEY) t1 WHERE t1.count > 1;''')]
    count_after  = [row for row in c.execute ('''SELECT * FROM  (SELECT *, COUNT(*) as count FROM Table_After group by KEY) t1 WHERE t1.count > 1;''')]

    if count_before:
        msg  =  "Found identical parcels on orig parcels : {}".format(count_before)
        print_arcpy_message(msg, status=2)

    if count_before:
        msg2 = "Found identical parcels on new parcels : {}".format(count_after)
        print_arcpy_message(msg2, status=2)

    #data1 = [row for row in c.execute ('''SELECT * FROM  Before_Table ORDER BY GUSH_NUM DESC, PARCEL DESC;''')]
    #Get_Runing_numbers(data1)

    add_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Table_After A LEFT JOIN Before_Table B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]
    del_parcels = [str(row[0]) for row in c.execute ('''SELECT A.KEY FROM Before_Table A LEFT JOIN Table_After B ON A.KEY = B.KEY WHERE B.KEY is NULL;''')]

    gdb = os.path.dirname(path_after)
    Insert_to_table(path_before,copy_tazar,gdb)

    msg2 = "added parcels: {}  ".format(add_parcels)
    msg3 = "Deleted parcels: {}".format(del_parcels)

    print_arcpy_message(msg2, status=1)
    print_arcpy_message(msg3, status=1)

    data = {str(i.PARCEL) +'-' +str(i.GUSH_NUM)+'-'+ str(i.GUSH_SUFFIX):[i.LOCALITY_ID,i.LOCALITY_NAME,i.LEGAL_AREA] for i in arcpy.SearchCursor(copy_tazar)}
    with arcpy.da.UpdateCursor(path_after,['PARCEL','GUSH_NUM','GUSH_SUFFIX','LOCALITY_ID','LOCALITY_NAME','LEGAL_AREA']) as ucursor:
        for row in ucursor:
            key = str(row[0]) +'-' +str(row[1])+'-'+ str(row[2])
            if data.has_key(key):
                row[3] = data[key][0]
                row[4] = data[key][1]
                row[5] = data[key][2]
                ucursor.updateRow(row)
    del ucursor

    # Make Dic:  {GUSH_NUM:[STATUS,STATUS_TEXT]} and copy this values to PARCEL LAYER if with Nulls
    Get_Status_Field(path_after)



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


def Get_Status_Field(layer):
    data_status = {i.GUSH_NUM:[i.STATUS,i.STATUS_TEXT] for i in arcpy.SearchCursor(layer) if i.GUSH_NUM != None and i.STATUS != None}

    with arcpy.da.UpdateCursor(layer,['GUSH_NUM',"STATUS","STATUS_TEXT"]) as cursor:
        for row in cursor:
            if not row[1]:
                if data_status.has_key(row[0]):
                    row[1] = data_status[row[0]][0]
                    row[2] = data_status[row[0]][1]
                    cursor.updateRow(row)
    del cursor


def Delete_curves_out_AOI(parcel_new,bankal_old):

    diss_old = r'in_memory' + '\\' + 'Diss_old'
    diss_new = r'in_memory' + '\\' + 'Diss_new'
    lyr_old  = r'in_memory' + '\\' + 'lyr_old'
    lyr_new  = r'in_memory' + '\\' + 'lyr_new'


    arcpy.Dissolve_management    (bankal_old,diss_old)
    arcpy.Dissolve_management    (parcel_new,diss_new)

    Feature_to_polygon           (diss_old,lyr_old)
    Feature_to_polygon           (diss_new,lyr_new)

    Delete_polygons (lyr_new,lyr_old)
    Delete_polygons (parcel_new,lyr_new)



def update_curves(fc,curve):
        for row in arcpy.SearchCursor(curve):
                upd_rows = arcpy.UpdateCursor(fc)
                curve_g = row.Shape
                midpnt = curve_g.centroid
                for upd_row in upd_rows:
                        if upd_row.Shape.distanceTo(midpnt)== 0:
                                diff = upd_row.Shape.difference (curve_g)
                                new_geometry = curve_g.union(diff)
                                upd_row.Shape = new_geometry
                                upd_rows.updateRow(upd_row) 

def names_curves(fc,tazar,curve):

        '''
        [INFO] -  חיבור של הקשתות לשמות של חלקות הבנקל שמתחת, צריך להיות במצב בו הקשתות נמצאות מעל הבנקל
        INPUT:
        1) fc     = שכבת הרצף
        2) curves = קשתות
        OUTPUT:
        1) curves = שכבה חדשה שמכוונת לאיזה שכבת בנקל הוא מתאים
        '''

        add_field                              (curve,'PARCEL_ID','LONG')
        arcpy.MakeFeatureLayer_management      (curve,'curvs_lyr')
        arcpy.SelectLayerByLocation_management ('curvs_lyr',"HAVE_THEIR_CENTER_IN",tazar,'',"NEW_SELECTION","INVERT")

        upd_rows = arcpy.UpdateCursor('curvs_lyr')
        for row in upd_rows:
                for Search_row in arcpy.SearchCursor(fc):
                    try: 
                        if Search_row.Shape.distanceTo(row.Shape.centroid)== 0:
                                if Search_row.PARCEL_ID > 0:
                                    if row.PARCEL_ID == None:
                                        row.PARCEL_ID = Search_row.PARCEL_ID
                                        upd_rows.updateRow(row)
                    except:
                        print ("Coudnt make Names for curves")
                        pass


def Update_Layer_Curves_By_ID(fc,tazar,curve):

    '''
    [INFO] - מחבר את הקשתות לחלקות המתאימות ומעדכן את התצ"ר בהתאם, מתשמש בשמות מפונקציה
            names_curves
    INPUT:
    1) fc     = שכבת הרצף
    2) tazar  =  שכבת התצר
    3) curves =  שכבת הקשתות

    INPUT     = שכבת הרצף מעודכנת עם השמות
    '''

    curve_temp = curve + '_temp'
    curve_diss = r'in_memory\\curve_diss'

    add_field      (curve,'PARCEL_ID','LONG')
    Delete_polygons(fc,curve)
    Update_Polygons(fc,tazar)
    Fix_curves     (fc,tazar,curve)


    Search_data = {row.PARCEL_ID:row.Shape for row in arcpy.SearchCursor(curve) if row.PARCEL_ID}

    # חיבור בין הבנקל לשכבת הקשתות

    arcpy.Select_analysis    (curve,curve_temp,"\"PARCEL_ID\" > 0 ")
    arcpy.Dissolve_management(curve_temp,curve_diss,['PARCEL_ID'])
    Search_data = {row.PARCEL_ID:row.Shape for row in arcpy.SearchCursor(curve_diss) if row.PARCEL_ID}

    Delete_polygons(fc,curve_temp)

    upd_rows = arcpy.UpdateCursor(fc)
    for row in upd_rows:
        if Search_data.has_key(row.PARCEL_ID):
            row.shape = Search_data[row.PARCEL_ID].union(row.Shape)
            upd_rows.updateRow(row) 


def Fix_Multi_part_Bankal(layer,tazar_border,parcel_Bankal_cut):

	'''
	[INFO] -  מתקן חלקות בנקל שמחוברות לתצר אבל נהרסו במהל העבודה, יתקן על מה ש-250 מטר מהתצר

	INPUT:
	1) layer             = שכבת העבודה אחרי עריכה
	2) tazar_border      = גבול התצ"ר
	3) parcel_Bankal_cut = בנקל חתוך לפני עריכה

	OUTPUT:
	1) שכבת עבודה בה כל מה ש-250 מטר מהתצר חזר להיות כמו המקור
	'''

	diss_temp        = r'in_memory'     +'\\'+'diss_temp'
	Temp_inter       = layer            +'Temp'
	after_del        = r'in_memory'     +'\\'+'after_del'
	Multi_part_inter = layer            +'Temp2'
	save_name        = layer

	arcpy.Buffer_analysis     (tazar_border,diss_temp,250)

	Delete_polygons            (parcel_Bankal_cut,diss_temp,after_del)

	arcpy.Clip_analysis       (layer,diss_temp,Temp_inter)

	fields       = Layer_Management(Temp_inter).fields()
	fields_layer = [n for n in fields if n not in ["SHAPE_Area","SHAPE_Length","OBJECTID","SHAPE@","SHAPE","GAP","delta","Check"]]

	arcpy.Dissolve_management (Temp_inter,Multi_part_inter,fields_layer)

	data = {str(i.PARCEL) +'-' +str(i.GUSH_NUM)+'-'+ str(i.GUSH_SUFFIX):i.shape for i in arcpy.SearchCursor(after_del)}

	with arcpy.da.UpdateCursor(Multi_part_inter,['PARCEL','GUSH_NUM','GUSH_SUFFIX','SHAPE@']) as cursor:
		for row in cursor:
			geom = row[-1]
			key  = str(row[0]) +'-' +str(row[1])+'-'+ str(row[2])
			if data.has_key(key):
				row[-1] = geom.union(data[key])
				cursor.updateRow(row)


	arcpy.Delete_management                (Temp_inter)
	arcpy.Delete_management                (layer)
	arcpy.Rename_management                (Multi_part_inter,save_name)




def Get_Point_AOI(AOI_final,point_bankal,point_modad,AOI_Point):

    '''
    [INFO] - מייצר שכבת נקודות מתאימה ל
    AOI Final
    חיבור של שכבת הבנקל לשכבת המודד, ללא הנקודות שנמחקו
    '''
    Layer_Management(point_bankal).Select_By_Location('INTERSECT',AOI_final,'0.001 Meters',AOI_Point)

    layer1 = Layer_Management    (AOI_Point)
    Fix_Pnt_Tolerance            (AOI_final,AOI_Point)
    layer1.Select_By_Location    ('COMPLETELY_WITHIN',AOI_final)

    pnt_save = [str(round(pt.X,1)) + '-' + str(round(pt.Y,1)) for row in arcpy.SearchCursor(AOI_final) for part in row.shape for pt in part if pt]
    with arcpy.da.UpdateCursor(AOI_Point,['SHAPE@']) as cursor:
        for row in cursor:
            if str(round(row[0].centroid.X,1)) + '-' + str(round(row[0].centroid.Y,1)) not in pnt_save:
                cursor.deleteRow()

    arcpy.Append_management      (point_modad,AOI_Point,'NO_TEST')

    layer1.delete_identical()
    arcpy.DeleteField_management(layer1.layer,'X_Y')

    return AOI_Point

    

def delete_Line_by_polygon(AOI_Line,tazar_border,Dissolve = False,num = 0.001):

    save_name = tazar_border

    if Dissolve:
        tazar_diss = 'in_memory\\' + os.path.basename(tazar_border+"_Temp")
        arcpy.Dissolve_management(tazar_border,tazar_diss)
        save_name = tazar_border
    
    if int(str(arcpy.GetCount_management(save_name))) > 0:
        data = [i.shape for i in arcpy.SearchCursor(save_name) if i.shape][0]
        with arcpy.da.UpdateCursor(AOI_Line,['SHAPE@']) as cursor:
            for row in cursor:
                if row[0]:
                    geom      = row[0]
                    new_geom  = geom.difference(data.buffer(num))
                    row[0]    = new_geom
                    cursor.updateRow(row)

def Create_Line_AOI(aoi,tazar_border,curves,bankal_line,modad_line,New_Line):

    print_arcpy_message('START Func: Create_Line_AOI',1)

    gdb = os.path.dirname(tazar_border)
    bankal_cut   = gdb + '\\' + 'bankal_cut'
    curves_temp  = gdb + '\\' + 'curves_temp'
    Return_line  = gdb + '\\' + 'Return_line'

    Polygon_To_Line_holes    (aoi,New_Line)
    Split_Line_By_Vertex     (New_Line)
    delete_Line_by_polygon   (New_Line,tazar_border)

    Layer_Management         (curves).Select_By_Location('COMPLETELY_WITHIN',tazar_border,'1 Meters',curves_temp,'invert')

    Layer_Management         (New_Line).Select_By_Location('INTERSECT',curves_temp)

    Layer_Management         (bankal_line).Select_By_Location ('INTERSECT',aoi,0,bankal_cut)

    Layer_Management         (bankal_cut).Select_By_Location ('INTERSECT',curves_temp,0,Return_line)  # החזרה של הקווים שנמחקו בעקבות הקשתות

    Layer_Management         (bankal_cut).Select_By_Location ('INTERSECT',aoi,'1 Meters',None,'invert')

    delete_Line_by_polygon   (bankal_cut,tazar_border,False,1)

    arcpy.Append_management  (bankal_cut,New_Line,'NO_TEST')
    Layer_Management         (Return_line).Select_By_Location('INTERSECT',tazar_border,0,None,'invert') 

    arcpy.Append_management  (Return_line,New_Line,'NO_TEST')

    Multi_to_single          (New_Line)

    del_line_Not_on_parcels  (New_Line,aoi)

    Delete_Duplic_Line       (New_Line)

    fix_tolerance_line       (New_Line,tazar_border)

    Delete_layers_after_use([bankal_cut,curves_temp])


    return New_Line


def Find_stubbern_lines(bankal_arc,aoi,tazar_border):

    gdb = os.path.dirname(tazar_border)

    Line_bankal = gdb + '\\' + 'Line_bankal_cut'
    new_line    = gdb + '\\' + 'AOI_Bankal_line'

    Layer_Management         (bankal_arc).Select_By_Location('INTERSECT',aoi,0,Line_bankal)
    Connect_Lines            (Line_bankal,new_line,50)

    # מחיקות קווים שעלולים להיות בעיתיים
    delete_Line_by_polygon   (new_line,tazar_border)
    Layer_Management         (new_line).Select_By_Location('INTERSECT',tazar_border,'0.1 Meters',None,'invert')
    Layer_Management         (new_line).Select_By_Location("WITHIN_CLEMENTINI",aoi)

    arcpy.Append_management  (new_line,bankal_arc,'NO_TEST')

    Delete_layers_after_use([new_line,Line_bankal])

