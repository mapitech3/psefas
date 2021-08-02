
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arcpy,math,uuid
import pandas as pd
import numpy as np
import sqlite3,json,os,random,sys
import xml.etree.ElementTree as ET
import pythonaddins


from Checks import *

arcpy.env.overwriteOutPut = True


Empty                            =  arcpy.GetParameterAsText(0)

topology_basic_cbx               = arcpy.GetParameterAsText(1)
line_Not_on_parcels_cbx          = arcpy.GetParameterAsText(2)
Missing_arc_cbx                  = arcpy.GetParameterAsText(3)
Node_not_on_parcel_cbx           = arcpy.GetParameterAsText(4)
vertex_without_modad_point_cbx   = arcpy.GetParameterAsText(5)
missing_modad_point_cbx          = arcpy.GetParameterAsText(6)
double_arc_cbx                   = arcpy.GetParameterAsText(7)
double_node_cbx                  = arcpy.GetParameterAsText(8)
Found_bad_parcel_around_AOI_cbx  = arcpy.GetParameterAsText(9)

# # # # # # Table # # # # #
Empty                            =  arcpy.GetParameterAsText(10)

Gush_parcel_doubled_cbx          = arcpy.GetParameterAsText(11)
Parcel_data_cbx                  = arcpy.GetParameterAsText(12)
Check_area_in_tazar_cbx          = arcpy.GetParameterAsText(13)
missing_Values_in_parcel_cbx     = arcpy.GetParameterAsText(14)
Parcel_gush_number_not_vaild_cbx = arcpy.GetParameterAsText(15)

select_all_cbx                   = arcpy.GetParameterAsText(16)


if select_all_cbx == 'true':
    topology_basic_cbx               = 'true'
    line_Not_on_parcels_cbx          = 'true'
    Missing_arc_cbx                  = 'true'
    Node_not_on_parcel_cbx           = 'true'
    vertex_without_modad_point_cbx   = 'true'
    missing_modad_point_cbx          = 'true'
    double_arc_cbx                   = 'true'
    double_node_cbx                  = 'true'
    Parcel_data_cbx                  = 'true'
    Check_area_in_tazar_cbx          = 'true'
    Gush_parcel_doubled_cbx          = 'true'
    missing_Values_in_parcel_cbx     = 'true'
    Parcel_gush_number_not_vaild_cbx = 'true'
    Found_bad_parcel_around_AOI_cbx  = 'true'



lyr_dataSource = get_layer_by_fc_name('PARCELS_inProc_edit')
arcpy.AddMessage(lyr_dataSource)

if lyr_dataSource:
    # extract from script location
    scriptPath = os.path.abspath(__file__)
    Scripts    = os.path.dirname(scriptPath)
    ToolShare  = os.path.dirname(Scripts)
    Scratch    = ToolShare + "\\Scratch"
    ToolData   = ToolShare + "\\ToolData"

    # extract from MXD
    mxd           = arcpy.mapping.MapDocument   ('CURRENT')
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

if topology_basic_cbx == 'true':
    print_arcpy_message  (ErrorDictionary["3"],1)
    print_arcpy_message  (ErrorDictionary["4"],1)
    topology_basic       (layer_parcel,gdb)

if line_Not_on_parcels_cbx == 'true':
    print_arcpy_message  (ErrorDictionary["5"],1)
    line_Not_on_parcels  (layer_arc,layer_parcel, gdb)

if Missing_arc_cbx == 'true':
    print_arcpy_message (ErrorDictionary["7"],1)
    Insert_needed_arc   (layer_parcel,layer_arc,Keshet,gdb)

if Node_not_on_parcel_cbx == 'true':
    print_arcpy_message (ErrorDictionary["12"],1)
    Node_not_on_parcel  (layer_parcel,layer_node.layer,gdb)

if vertex_without_modad_point_cbx == 'true':
    print_arcpy_message (ErrorDictionary["6"],1)
    vertex_without_modad_point  (layer_parcel,parcel_modad,lyr_node_modad,gdb)

if missing_modad_point_cbx == 'true':
    print_arcpy_message (ErrorDictionary["2"],1)
    missing_modad_point (layer_node,parcel_modad,lyr_node_modad,gdb)

if double_arc_cbx == 'true':
    print_arcpy_message (ErrorDictionary["8"],1)
    double_arc          (gdb,arc_all)

if double_node_cbx == 'true':
    print_arcpy_message (ErrorDictionary["9"],1)
    double_node         (gdb,node_all)

if Parcel_data_cbx == 'true':
    print_arcpy_message ('חלקות יוצאות ונכנסות',1)
    Parcel_data         (layer_parcel.layer,ws)

if Check_area_in_tazar_cbx == 'true':
    print_arcpy_message             (ErrorDictionary["10"],1)     
    Calc_Area                       (layer_parcel.layer,ws,gdb)

if Gush_parcel_doubled_cbx == 'true':
    print_arcpy_message             (ErrorDictionary["11"],1)
    Check_accurancy_pracel          (layer_parcel.layer,gdb)

if missing_Values_in_parcel_cbx == 'true':
    print_arcpy_message             (ErrorDictionary["1"],1)
    missing_Values_in_parcel        (layer_parcel.layer,ws,gdb)

if Parcel_gush_number_not_vaild_cbx == 'true':
    print_arcpy_message             (ErrorDictionary["13"],1)
    Find_not_exists_parcel_in_Gush  (layer_parcel.layer,ws,gdb)

if Found_bad_parcel_around_AOI_cbx == 'true':
    print_arcpy_message             (ErrorDictionary["14"],1)
    Found_bad_parcel_around_AOI     (layer_parcel.layer,ws,gdb)




# service_code_sum = 0
# #cbx17
# if parcel_cbx == 'true':
#     print_arcpy_message(ErrorDictionary_services["1"],1)
#     service_code_sum = service_code_sum + 1

# #cbx18
# if gush_cbx == 'true':
#     print_arcpy_message(ErrorDictionary_services["2"],1)
#     service_code_sum = service_code_sum + 2

# #cbx19
# if value_cbx == 'true':
#     print_arcpy_message(ErrorDictionary_services["4"],1)
#     service_code_sum = service_code_sum + 4

# #cbx20
# if cancelparcel_cbx == 'true':
#     print_arcpy_message(ErrorDictionary_services["8"],1)
#     service_code_sum = service_code_sum + 8

# print_arcpy_message("run service with code " + str(service_code_sum),1)

# if service_code_sum > 0:
#     xml_string = Call_Service(gdb, service_code_sum)
#     XML_to_Table(xml_string, gdb, df)
