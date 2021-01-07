

import arcpy
import os
from os import path

arcpy.env.overwriteOutput = True
import pandas as pd

def print_arcpy_message(msg,status = 1):
    '''
    return a message :
    
    print_arcpy_message('sample ... text',status = 1)
    >>> [info][08:59] sample...text
    '''
    msg = str(msg)
    
    if status == 1:
        prefix = '[info]'
        msg = prefix + str(datetime.datetime.now()) +"  "+ msg
        print (msg)
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




def get_GDB(Folder):
        list_gdb = []
        exists   = []
        for root, dirs, files in os.walk(Folder):
                for dir in dirs:
                        if dir.endswith(".gdb"):
                            if 'SRVToGDB' in dir:
                                if dir not in exists:
                                    print dir
                                    list_gdb.append(root + '\\' +dir)
                                    exists.append(dir)
        return list_gdb




folder  = r'F:\medad\Python_tools\Psafas_tool\ToolShare\Scratch'
f_name  = os.path.basename(folder)
Out_put = r'F:\medad\Python_tools\Psafas_tool\ToolShare\Statistics' + '\\' +f_name +'_Statistics.csv'
list_gdb = get_GDB(folder)


problems = {'holes fixed':0,'holes Problems':0,'Points fixid':0,'Points Problems':0}
tested = []

for gdb in list_gdb:

    name = os.path.basename(gdb)

    # Holes #

    try:
        line_find_holes = [i.shape.length for i in arcpy.SearchCursor(gdb + '\\' + 'slivers_Intersect')]
        holes = [i.shape.area for i in arcpy.SearchCursor(gdb + '\\' + 'Topolgy_Chack_holes')]
    
        num_holes_fix   = len(line_find_holes)
        num_holes_prob  = len(holes)
        holes_true      = num_holes_fix - num_holes_prob

        problems['holes fixed']    += holes_true
        problems['holes Problems'] += num_holes_prob
        tested.append(name)
    except:
        print_arcpy_message('gdb: {} missing the slivers_Intersect layer'.format(name),status = 1)



    # Points #

    try:
        Point_Moved = [i for i in arcpy.SearchCursor(gdb + '\\' + 'PARCEL_ALL_FINAL_point') if i.Changed == 'True']
        Point_prob  = [i for i in arcpy.SearchCursor(gdb + '\\' + 'Possible_Error_points')]

        num_Moved      = len(Point_Moved)
        num_Point_prob = len(Point_prob)
        Points_true    = num_Moved - num_Point_prob
        print Points_true
        
        problems['Points fixid']    += Points_true
        problems['Points Problems'] += num_Point_prob
    except:
        print_arcpy_message('gdb: {} missing point layers'.format(name),status = 1)


tazars                 = [os.path.basename(i).split('.')[0].split('_',1)[1] for i in tested]
problems['Tazars']     = ''.join([i +',' for i in tazars])
problems['Total_Check'] = len(tazars)

print problems

df         = pd.DataFrame.from_dict(problems,orient = "index").reset_index()
df.columns = ['index','Count']
if path.exists(Out_put):
    os.remove(Out_put)
df.to_csv   (Out_put) 
    

    





