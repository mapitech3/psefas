# -*- coding: utf-8 -*-


# # # # # # # # # # # # # # # Advanced Func # # # # # # # # # # # # # # # 

import os
import arcpy
import pandas
import sqlite3
import math

from Layer_Class   import *
from Basic_Func    import *


'''
stubborn_parts
fix_holes_Overlaps_By_Length
Snap_border_pnts
clean_pseudo
Move_Vertices_By_Name
Update_Polygons
Connect_Lines
Clean_non_exist_pnts
'''

def stubborn_parts(path,bankal,tazar,Out_put,curves = ''):

    '''
    [INFO]- חוסם חורים ע"י מילוי של האזור הבעייתי, עובד במידה ואין חורים שמשותפים לכמה חלקות
    INPUT - 
    1) path     =  שכבת רצף
    2) bankal   -  שכבת ההבנקל הרחבה 
    3) tazar    - חלקות המודד
    4) curves   - במידה ויש קשתות, ניתן למחוק חלקות שנראות בדיוק כמו קשת

    OUTPUT - 
    1) Out_put  - שכבת הרצף לאחר התיקון, במידה ויש פגיעה, יחזור אחרוה
    '''

    print_arcpy_message("START Func: stubborn parts",1)

    memory = r'in_memory'
    gdb    = os.path.dirname(path)

    ## Create_layers
    inter            = memory + "\\" + "inter"
    sliver_curves    = memory + '\\'+ 'sliver_curves'
    path2            = memory + '\\'+ 'COPY_TEMP'
    Featur_to_poly   = memory + '\\' + 'Featur_to_poly'
    paracel_around   = memory +"\\"+ "paracel2_around"
    Parcel_deleted   = memory +"\\"+ "Parcel_deleted"
    parcal_all_Final = Out_put

    # מחיקה של קשתות שהן בדיוק כמו חלקות - יכול להיות בעיה אם החלקה היא קשת
    if curves:
        arcpy.MakeFeatureLayer_management(path,'path_lyr')
        arcpy.SelectLayerByLocation_management('path_lyr',"ARE_IDENTICAL_TO",curves)
        if int(str(arcpy.GetCount_management('path_lyr'))) > 0:
                        #print_arcpy_message("found identical rings")
                        arcpy.DeleteFeatures_management('path_lyr')             
            

    # מחיקה של חפיפות בשביל שהיו על תקן חורים
    arcpy.Intersect_analysis          ([path], inter)
    Delete_polygons                   (path,inter)

    ## יצירה של החורים לפיהם נמחק את הפוליגונים של הבנקל 
    Feature_to_polygon             (path,Featur_to_poly)
    Delete_polygons                (Featur_to_poly,path,sliver_curves)

    arcpy.CopyFeatures_management  (path,path2)

    arcpy.Select_analysis (path2,path2+"_path2_born") # DELETE
    # בדיקה שהחורים נוגעים התצ"ר והם רלוונטים
    arcpy.MakeFeatureLayer_management      (sliver_curves, 'sliver_curves_lyr')
    arcpy.SelectLayerByLocation_management ('sliver_curves_lyr', 'BOUNDARY_TOUCHES', tazar)

    num_slivers = int(str(arcpy.GetCount_management('sliver_curves_lyr')))
    if num_slivers > 0:

            print_arcpy_message ("you still have {} slivers, rebuild geometry and attributes".format(num_slivers),1)

            # #  #   #  #  #  #  יצירה של חלקות במעטפת נוספת מסביב לחלקה

            # מחיקה של החלקה מהבנקל שנוגעת בחור
            arcpy.MakeFeatureLayer_management     (path2, "FINAL2_lyr", "\"PARCEL_ID\" > 0") 
            arcpy.SelectLayerByLocation_management("FINAL2_lyr","SHARE_A_LINE_SEGMENT_WITH",sliver_curves)
            arcpy.Select_analysis                 ("FINAL2_lyr",Parcel_deleted) # שמירה על החלקה שאנחנו מוחקים
            arcpy.DeleteFeatures_management       ("FINAL2_lyr")

            # שליפת החלקות החדשות מסביב לחלקה שנעלמה
            arcpy.MakeFeatureLayer_management     (bankal, "paracel2_lyr") 
            arcpy.SelectLayerByLocation_management("paracel2_lyr","INTERSECT",Parcel_deleted)
            arcpy.Select_analysis                 ("paracel2_lyr", paracel_around)
            delete_parts_if_inside                (paracel_around,path2)          # מחיקת חלקות העבודה, השארת רק החלקות החדשות שנוספו מהבנקל 
            delete_parts_if_inside                (paracel_around,Parcel_deleted) # מחיקת החלקה עם החור, השארת רק החלקות החדשות שנוספו מהבנקל

            # חיבור השכבות החדשות לשכבת הרצף
            Update_Polygons                       (path2,paracel_around) 
            arcpy.Select_analysis (path2,path2 +'before_Feat_To_Poly')  # DELETEEEEEEEEEEEEEEEEE

            Feature_to_polygon                    (path2,Out_put)

            # חיבור המידע של השכבות לשכבה החדשה
            Spatial_Connection_To_LabelPoint      (Out_put,path)
            Spatial_Connection_To_LabelPoint      (Out_put,paracel_around)

            delete_parts_if_inside                (Out_put,paracel_around) # מחיקת שכבות הבנק"ל מסביב לאזור העבודה

            # בדיקה אם התיקון פגם בתוצאה, במידה וכן, יחזור אחורה
            before    = int(str(arcpy.GetCount_management(path)))
            after     = int(str(arcpy.GetCount_management(Out_put)))
            None_in_f = len(Layer_Management(Out_put).None_in_fields(['PARCEL']))

            if (before > after) or (None_in_f > 0):
                print_arcpy_message     ("Stubbern seems to delete features, Cancel and return 1 step back",1)
                arcpy.Select_analysis   (Out_put,Out_put + 'AFTER STUBBURN_PARTS') # #################delete
                arcpy.Delete_management (Out_put)
                arcpy.Select_analysis   (path,parcal_all_Final)

    else:
            print_arcpy_message          ("No stubborn parts")
            arcpy.CopyFeatures_management(path,Out_put)
      

def fix_holes_Overlaps_By_Length(path,tazar,path2):

    GDB = os.path.dirname(path)

    in_memory          = r'in_memory' 
    path2              = arcpy.CopyFeatures_management(path,path2)
    FEATURE_TO_POLYGON = in_memory + '\FEATURE_TO_POLYGON'
    slivers            = GDB + '\slivers'
    PARACELS_Only      = in_memory + '\PARACELS_Only'
    inter              = in_memory + '\inter'
    line               = GDB + '\Line'
    slivers_Intersect  = GDB + '\slivers_Intersect'

    arcpy.Intersect_analysis          ([path2], inter)
    if int(str(arcpy.GetCount_management(inter))) > 0:
        Delete_polygons                   (path2,inter)

    arcpy.AddField_management        (path2, "KEY_parcel", "LONG")
    arcpy.CalculateField_management  (path2, "KEY_parcel", "[OBJECTID]", "VB", "")
        
    Feature_to_polygon(path2, FEATURE_TO_POLYGON)
    Delete_polygons             (FEATURE_TO_POLYGON, path2, slivers)
        
    number_of_slivers = int(str(arcpy.GetCount_management(slivers)))
    if number_of_slivers > 0:
            print("there is {} holes, start working to fix them".format(str(number_of_slivers)))

            arcpy.AddField_management        (slivers, "KEY_sliv", "LONG")
            arcpy.CalculateField_management  (slivers, "KEY_sliv", "[OBJECTID]", "VB", "")

            Delete_polygons             (path2, tazar, PARACELS_Only)

            Polygon_To_Line   (PARACELS_Only, line)

            sliver_feature_layer = GDB + '\\' + 'sliver_feature_layer'
            arcpy.MakeFeatureLayer_management      (slivers, sliver_feature_layer)
            arcpy.SelectLayerByLocation_management (sliver_feature_layer, 'BOUNDARY_TOUCHES', tazar)
            intersect_list = [sliver_feature_layer,line]

            arcpy.Intersect_analysis    (intersect_list, slivers_Intersect, "ALL", ".001 Meters", "INPUT")

            data       = [[row[0],row[1],row[2]] for row in arcpy.da.SearchCursor(slivers_Intersect,['KEY_sliv','FID_Line','SHAPE@LENGTH'])]
                
            df         = pd.DataFrame(data,columns= ['KEY_sliv','KEY_parcel_1','SHAPE@LENGTH'])
            df["RANK"] = df.groupby('KEY_sliv')['SHAPE@LENGTH'].rank(method='first',ascending=False)
            df         = df[df['RANK'] == 1]

            data_to_gis = [[getattr(row, "KEY_sliv"), getattr(row, "KEY_parcel_1")]for row in df.itertuples(index=True, name='Pandas')]

            arcpy.AddField_management (slivers, "ID_KEY_par", "LONG")
            for data in data_to_gis:
                with arcpy.da.UpdateCursor(slivers,['KEY_sliv','ID_KEY_par']) as cursor:
                    for row in cursor:
                        if row[0] == data[0]:
                            row[1] = data[1]
                            cursor.updateRow (row)
                            

            x = [[x[0],x[1]] for x in arcpy.da.SearchCursor(slivers,['ID_KEY_par','SHAPE@'])]
            for i in x:
                with arcpy.da.UpdateCursor(path2,['OID@','SHAPE@']) as icursor:
                    for row in icursor:
                            if row[0] == i[0]:
                                    new = row[1].union(i[1])
                                    row[1] = new
                                    icursor.updateRow(row)

                                
            arcpy.Delete_management(line)
            arcpy.Delete_management(slivers_Intersect)
    else:
            print("no holes found".format(str(number_of_slivers)))


def Snap_border_pnts(ws,border,parcel_all,Dis_search = 1):


    print_arcpy_message('START Func: Snap border pnts',1)

    tazar_border = 'in_memory\Tazar_Border_diss'
    arcpy.Dissolve_management(border,tazar_border)

    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "WITHIN_A_DISTANCE", tazar_border, '5 Meters')

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''CREATE TABLE border(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


    c.execute('''CREATE TABLE parcels(pnt_num real, x real, y real, xy text, part real, oid real, junction real, linearity real)''')


    VerticesToTable2(tazar_border, "border",c)
    border_vertices = [row for row in c.execute('''SELECT * FROM border''')]
    VerticesToTable2("parcel_all_lyr", "parcels",c)

    parcel_non_common_vertices = [row for row in c.execute('''SELECT * FROM parcels
                                                                     left join border
                                                                     on parcels.xy = border.xy
                                                                     where  border.xy is null''')]
    
    
    border_geom = arcpy.CopyFeatures_management(tazar_border, arcpy.Geometry())[0]

    vertices_on_border_outline = [row for row in parcel_non_common_vertices if border_geom.distanceTo (arcpy.Point(row[1], row[2])) < 5]

    distance_vertices = [[p[:8] + b[:8],math.sqrt(((p[1]-b[1])**2)+((p[2]-b[2])**2))] for p in vertices_on_border_outline for b in border_vertices if math.sqrt(((p[1]-b[1])**2)+((p[2]-b[2])**2))\
        < Dis_search or (float("{0:.2f}".format(p[1])) == float("{0:.2f}".format(b[1])) and float("{0:.2f}".format(p[2])) == float("{0:.2f}".format(b[2])))]


    rows = arcpy.UpdateCursor("parcel_all_lyr")
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
                            if this_vertex[0][0][7] < 0.5 and this_vertex[0][0][6] == 1:
                                print "pseodo: delete vertex"
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
        rows.updateRow(row)


def clean_pseudo(parcel_all, border,curves):

    def clean_pseudo_vertices(polygon_before, border_geom, nodes_pts):
        for part in polygon_before:
            pts_final = []
            pts_trio = []
            deleted = []
            for pt in part:
                    if str(type(pt)) <> "<type 'NoneType'>":
                            pts_trio.append([pt.X, pt.Y])
                            if len(pts_trio) == 3:
                                x = pts_trio[1][0]
                                y = pts_trio[1][1]
                                if collinearity(pts_trio[0], pts_trio[1], pts_trio[2]) < 0.9 and [float("{0:.2f}".format(x)), float("{0:.2f}".format(y))] not in nodes_pts and border_geom_buffer.contains(arcpy.Point(x,y)):
                                        #print_arcpy_message("delete vertex",1)
                                        deleted.append([x,y])
                                        #print_arcpy_message([x,y],1)
                                else:
                                    pts_final.append(arcpy.Point(x,y))
                                pts_trio = [pts_trio[1], pts_trio[2]]
                            else:
                                pts_final.append(pt)
            if deleted:
                polygon_after = PtsToPolygon(pts_final)
                return polygon_after
            else:
                return polygon_before


    print_arcpy_message("START Func: clean pseudo",1)

    before_vertxs = Layer_Management(parcel_all).vertxs_Count()
    
    arcpy.MakeFeatureLayer_management(parcel_all, "parcel_all_lyr")
    arcpy.SelectLayerByLocation_management("parcel_all_lyr", "SHARE_A_LINE_SEGMENT_WITH", border)
        
    node = "in_memory" +'\\'+"node"
    arcpy.CreateFeatureclass_management("in_memory", "node", "POINT", "", "", "",border)
    border_geom = arcpy.CopyFeatures_management(border, arcpy.Geometry())
    border_geom_buffer =  border_geom[0].buffer(0.05)

    Layer_Management(border).Get_vertxs_As_Point(node)     

    # להכניס גם נקודות של הבנקל לרשימת נקודות שלא צריכות להימחק
    # למה לא להשתמש בנקודות קיימות?            

    nodes_pts = [[float("{0:.2f}".format(row.Shape.centroid.X)), float("{0:.2f}".format(row.Shape.centroid.Y))] for row in arcpy.SearchCursor(node)]
    upd_rows = arcpy.UpdateCursor("parcel_all_lyr")
    for upd_row in upd_rows:
        polygon_before = upd_row.Shape
        polygon_after = clean_pseudo_vertices(polygon_before, border_geom, nodes_pts)
        if polygon_after:
            upd_row.Shape = polygon_after
            upd_rows.updateRow(upd_row)


    Fix_curves              (parcel_all,border,curves)

    after_vertxs    = Layer_Management(parcel_all).vertxs_Count()
    deleted_vertexs = before_vertxs - after_vertxs
    print_arcpy_message('Total Vertexs Deleted: {}'.format(deleted_vertexs))



def Move_Vertices_By_Name(polygon,points,field_name_points,points_to_move,field_name_to_move = 'POINT_NAME',Dis_limit_to_move = 10):

    '''
    [INFO] -  מזיז וורטקסים של פוליגון לפי השם של של הוורטקסים שלו (שכבת נקודות נפרדת), לעומת שם של שכבת נקודות אחרת
    INPUT - 
    1) polygon            - שכבת הפוליגון שתזוז
    2) points             - שכבת נקודות על הוורטקסים של השכבה הפוליגונלית, עם שמות
    3) field_name_points  - שם השדה של שכבת הנקודות בו מופיע שם הנקודה
    4) points_to_move     - שכבת הנקודות אליהם אנחנו רוצים להזיז
    5) field_name_to_move - שם השדה בו נמצת שם הנקודה אליה אנו רוצים להזיז

    OUTPUT - שכבת הפוליגונים תזוז אל הנקודות לה יש שם דומה
    '''

    Save_Source  = polygon + 'Save'
    before_inter = r'in_memory\\before_inter'
    after_inter  = r'in_memory\\after_inter'
    save_name    = polygon

    arcpy.Select_analysis(polygon,Save_Source)

    data_points = {str(round(n.X,2))    +'-' + str(round(n.Y,2)):str(i.getValue(field_name_points)) for i in arcpy.SearchCursor(points) for n in i.shape if i.getValue(field_name_points) != None and i.getValue(field_name_points) != ''}
    move_points = {str(i.getValue(field_name_to_move)):[n.X,n.Y] for i in arcpy.SearchCursor(points_to_move) for n in i.shape if i.getValue(field_name_to_move) != None and i.getValue(field_name_to_move) != ''}

    if (bool(data_points) == True) and (bool(move_points)==True):
        data_polygons = [[str(round(pts.X,2)) +'-' + str(round(pts.Y,2)),round(pts.X,2),round(pts.Y,2),'',0,0] for i in arcpy.SearchCursor(polygon) for n in i.shape for part in i.shape for pts in part if pts]

        for i in data_polygons:
            if data_points.has_key (i[0]):
                i[-3] = data_points[i[0]]
                
        for i in data_polygons:
            if move_points.has_key (i[-3]):
                i[-2] = move_points[i[-3]][0]
                i[-1] = move_points[i[-3]][1]

        data_polygons = {i[0]:i[1:] for i in data_polygons if i[-3] != '' and i[-2] != 0}

        num_inter = int(str(arcpy.GetCount_management(arcpy.Intersect_analysis(polygon,before_inter))))

        if data_polygons:
            with arcpy.da.UpdateCursor(polygon,["SHAPE@"]) as cursor:
                for row in cursor:
                    geom = row[0]
                    array = arcpy.Array()
                    count = 0
                    for part in geom:
                        for pt in part:
                            if pt:
                                key = str(round(pt.X,2))+'-' + str(round(pt.Y,2))
                                if data_polygons.has_key(key):
                                    distance = dis(data_polygons[key][-2],data_polygons[key][-5],data_polygons[key][-1],data_polygons[key][-4])
                                    if distance < Dis_limit_to_move:
                                        Point =  arcpy.Point(data_polygons[key][-2],data_polygons[key][-1])
                                    else:
                                        Point = arcpy.Point(pt.X,pt.Y)
                                else:
                                    Point = arcpy.Point(pt.X,pt.Y)
                                if count == 0:
                                    first = Point
                                array.add(Point)
                                count += 1
                            else:
                                array.add(first)
                                array.add(None)
                    New_poly = arcpy.Polygon(array)
                    row[0] = New_poly
                    cursor.updateRow(row)
            del cursor 

        num_inter_AFTER = int(str(arcpy.GetCount_management(arcpy.Intersect_analysis(polygon,after_inter))))

        if num_inter_AFTER > num_inter:
            print_arcpy_message     ("Coudnt Move By Name, Polygon Building Error",2)
            arcpy.Delete_management (polygon)
            arcpy.Rename_management (Save_Source,save_name)

def Update_Polygons(Layer_To_Update,New_Item,To_New_Layer = ''):

    Delete_polygons                            (Layer_To_Update ,New_Item,To_New_Layer)
    if To_New_Layer == '':
        To_New_Layer = Layer_To_Update
    arcpy.Append_management                    (New_Item        ,To_New_Layer, 'NO_TEST')


def Connect_Lines(layer,layer_new,min_dis):

    '''
    [INFO] - יצירת קווים המחברים בין יישויות במידה ויש ישות שלא מחוברת "עם קצה" יש לבחור במרחק מקסימלי לחיבור
    '''

    new_list = Layer_To_Edge_list(layer)

    Diss = 'in_memory\Diss_layer'

    ws, fc_name = os.path.split (layer_new)
    s_r         = arcpy.Describe (layer).spatialReference

    if arcpy.Exists(layer_new):
        arcpy.Delete_management(layer_new)

    line = arcpy.CreateFeatureclass_management (ws, fc_name, 'POLYLINE', spatial_reference=s_r)

    insert = arcpy.InsertCursor(line)

    for i in range(len(new_list)):
        if new_list[i][2] < min_dis:
            points   = [arcpy.Point(new_list[i][0][1],new_list[i][0][2]),arcpy.Point(new_list[i][1][1],new_list[i][1][2])]
            array    = arcpy.Array(points)
            polyline = arcpy.Polyline(array)
            feat     = insert.newRow ()
            feat.shape    = polyline
            insert.insertRow(feat)

    arcpy.RepairGeometry_management(layer_new)

    Delete_By_length                (layer_new,0.2)
    return layer_new


def Clean_non_exist_pnts(AOI,border,bankal,tazar_copy):

    print_arcpy_message("START FUNC: Clean_non_exist_pnts")

    gdb            = os.path.dirname(border)
    bankal_cut     = gdb + '\\' + 'Bankal_Cut_inter'
    holes_to_keep  = gdb + '\\' + 'holes_to_keep'
    holes_keeping  = gdb + '\\' + 'holes_keeping'
    pts_on_border  = gdb + '\\' + 'pnts_on_border'

    save_source    = gdb + '\\' + 'Save_Source'
    save_name      = AOI
    arcpy.Select_analysis(AOI,save_source)

    Layer_Management(bankal).Select_By_Location('INTERSECT',border,'10 Meters',bankal_cut)
        
    border_xy     = [[round(j.X,1),round(j.Y,1)] for i in arcpy.SearchCursor (border) for n in i.shape for j in n if j]     # לא נוגעים בנקודות המודד
    bankal_cut_xy = [[round(j.X,1),round(j.Y,1)] for i in arcpy.SearchCursor (bankal_cut) for n in i.shape for j in n if j] # לא נוגעים בנקודות הבנקל
    Layer_Management(Layer_Management(AOI).Get_vertxs_As_Point()).Select_By_Location('INTERSECT',border,'0.01 Meters',pts_on_border)
    pts_border_xy = [[round(row.Shape.centroid.X,1),round(row.Shape.centroid.Y,1)] for row in arcpy.SearchCursor(pts_on_border)] # לא נוגעים בנקודות החדשות על התצר
    arcpy.Dissolve_management(AOI,r'in_memory\dissolve_me')
    AOI_border_xy = [[round(j.X,1),round(j.Y,1)] for i in arcpy.SearchCursor (r'in_memory\dissolve_me') for n in i.shape for j in n if j] # לא נוגעים בנקודות גבול של אזור העבודה
  
    saved_vertexs = border_xy + bankal_cut_xy + pts_border_xy + AOI_border_xy

    Feature_to_polygon (AOI,holes_to_keep)
    Delete_polygons    (holes_to_keep,AOI)
    holes_befotre = int(str(arcpy.GetCount_management(holes_to_keep)))

    Layer_Management        (holes_to_keep).Select_By_Location('INTERSECT',border,0,holes_keeping,'invert')

    Delete_polygons(AOI,border)

    Ucursor = arcpy.UpdateCursor(AOI)
    for row in Ucursor:
        geom = row.shape
        array = arcpy.Array()
        for part in geom:
            count = 0
            for pt in part:
                if pt:
                    if [round(pt.X,1),round(pt.Y,1)] in saved_vertexs:
                        array.add(pt)
                    if count == 0:
                        first = pt
                    else:
                        pass
                    count += 1
                else:
                    array.add(first)
                    array.add(None)
                    count = 0

        New_poly = arcpy.Polygon(array)
        row.shape = New_poly
        Ucursor.updateRow(row)

    del Ucursor 

    Delete_polygons         (AOI,holes_keeping)
    arcpy.Append_management (tazar_copy,AOI,'NO_TEST')

    Feature_to_polygon (AOI,holes_to_keep)
    Delete_polygons    (holes_to_keep,AOI)
    after_befotre = int(str(arcpy.GetCount_management(holes_to_keep)))

    if holes_befotre < after_befotre:
        print_arcpy_message("There is modad  point that may be missing, return 1 step back")
        arcpy.Delete_management(AOI)
        arcpy.Rename_management(save_source,save_name)

