# -*- coding: utf-8 -*-
import arcpy
import pythonaddins
import os


class error_layer(object):
    """Implementation for Choose_Next_feature_addin.combobox (ComboBox)"""
    def __init__(self):
        self.items = ["Errors_Polygon", "Errors_Line","Errors_Point"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = '12345678901234567890'
        self.width = '12345678901234567890'

    def onSelChange(self, selection):



        mxd = arcpy.mapping.MapDocument('current')
        df  = arcpy.mapping.ListDataFrames(mxd)[0]
        lyrs = arcpy.mapping.ListLayers (mxd, '*', df)
        for lyr in lyrs:
            arcpy.SelectLayerByAttribute_management(lyr,"CLEAR_SELECTION")
            if lyr.isFeatureLayer:
                if str(os.path.basename(lyr.dataSource)) in ["Errors_Polygon","Errors_Line","Errors_Point"]:
                    if selection == "Errors_Polygon":
                        if str(os.path.basename(lyr.dataSource))== "Errors_Polygon":
                            lyr.visible = True  
                        else:
                            lyr.visible = False
                    if selection == "Errors_Line":
                        if str(os.path.basename(lyr.dataSource))== "Errors_Line":
                            lyr.visible = True
                        else:
                            lyr.visible = False
                    if selection == "Errors_Point":
                        if str(os.path.basename(lyr.dataSource))== "Errors_Point":
                            lyr.visible = True
                        else:
                            lyr.visible = False
        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()


    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass


class Forward(object):
    """Implementation for Choose_feat_addin.button_1 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):

        mxd = arcpy.mapping.MapDocument('current')
        df  = arcpy.mapping.ListDataFrames(mxd)[0]
        lyrs = arcpy.mapping.ListLayers (mxd, '*', df)

        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if str(os.path.basename(lyr.dataSource)) in ["Errors_Polygon","Errors_Line","Errors_Point"]:
                    if lyr.visible == True:
                        try:
                            count_feat = [i.OBJECTID for i in arcpy.SearchCursor(lyr)][0] + 1
                        except:
                            count_feat = min([i.OBJECTID for i in arcpy.SearchCursor(lyr.dataSource)])
                            print "MIN"
                            pass
                        
                        
                        arcpy.SelectLayerByAttribute_management(lyr,"NEW_SELECTION","\"OBJECTID\" = "+str(count_feat)+"")

                        df.zoomToSelectedFeatures()

class backward(object):
    """Implementation for Choose_feat_addin.button_1 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):

        mxd = arcpy.mapping.MapDocument('current')
        df  = arcpy.mapping.ListDataFrames(mxd)[0]
        lyrs = arcpy.mapping.ListLayers (mxd, '*', df)

        for lyr in lyrs:
            if lyr.isFeatureLayer:
                if str(os.path.basename(lyr.dataSource)) in ["Errors_Polygon","Errors_Line","Errors_Point"]:
                    if lyr.visible == True:
                        try:
                            count_feat = [i.OBJECTID for i in arcpy.SearchCursor(lyr)][0] - 1
                        except:
                            count_feat = min([i.OBJECTID for i in arcpy.SearchCursor(lyr.dataSource)])
                            print "MIN"
                            pass
                        
                        
                        arcpy.SelectLayerByAttribute_management(lyr,"NEW_SELECTION","\"OBJECTID\" = "+str(count_feat)+"")

                        df.zoomToSelectedFeatures()
