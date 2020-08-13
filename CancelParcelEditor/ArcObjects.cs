using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using ESRI.ArcGIS.Geodatabase;
using ESRI.ArcGIS.DataSourcesGDB;
using ESRI.ArcGIS.Geoprocessor;
using ESRI.ArcGIS.Geoprocessing;
using ESRI.ArcGIS.DataManagementTools;
using ESRI.ArcGIS.Geometry;
using ESRI.ArcGIS.AnalysisTools;
using ESRI.ArcGIS.Carto;
using ESRI.ArcGIS.ArcMapUI;

namespace ArcObjectsTools
{
    class ArcObjects
    {
        public static IFeatureClass open_fc(string ws, string name)
        {
            IWorkspaceFactory GdbWsF = new FileGDBWorkspaceFactory();
            IWorkspace GdbWs = GdbWsF.OpenFromFile(ws, 0);
            // open fcs
            IFeatureWorkspace FeatWs = GdbWs as IFeatureWorkspace;
            IFeatureClass fc = FeatWs.OpenFeatureClass(name);
            return fc;
        }

        public static ITable open_table(string ws, string name)
        {
            IWorkspaceFactory GdbWsF = new FileGDBWorkspaceFactory();
            IWorkspace GdbWs = GdbWsF.OpenFromFile(ws, 0);
            // open fcs
            IFeatureWorkspace FeatWs = GdbWs as IFeatureWorkspace;
            ITable table = FeatWs.OpenTable(name);
            return table;
        }

        public static IFeatureCursor create_cursor(IFeatureClass fc)
        {
            IFeatureCursor pCursor = fc.Search(null, false);
            return pCursor;
        }
        public static ICursor create_table_cursor(ITable table)
        {
            ICursor pCursor = table.Search(null, false);
            return pCursor;
        }

        public static ICursor create_table_cursor_with_query(ITable table, string query)
        {
            IQueryFilter qf = new QueryFilter() as IQueryFilter;
            qf.WhereClause = query;
            ICursor pCursor = table.Search(qf, false);
            return pCursor;
        }

        public static IFeatureCursor create_cursor_with_query(IFeatureClass fc, string query)
        {
            IQueryFilter qf = new QueryFilter() as IQueryFilter;
            qf.WhereClause = query;
            IFeatureCursor pCursor = fc.Search(qf, false);
            return pCursor;
        }

        public static void create_fc(Geoprocessor gp, string ws, string name, string geometry_type, string spatial_reference)
        {
            CreateFeatureclass cfc = new CreateFeatureclass();
            cfc.out_path = ws;
            cfc.out_name = name;
            cfc.geometry_type = geometry_type;
            cfc.spatial_reference = spatial_reference;
            gp.Execute(cfc, null);
        }

        public static List<string> list_fcs_in_gdb(string ws)
        {
            List<string> fc_names = new List<string>();
            IWorkspaceFactory GdbWsF = new FileGDBWorkspaceFactory();
            IWorkspace GdbWs = GdbWsF.OpenFromFile(ws, 0);
            IEnumDatasetName ds_names = GdbWs.get_DatasetNames(esriDatasetType.esriDTFeatureClass);
            IDatasetName ds_name = ds_names.Next();
            while (ds_name != null)
            {
                fc_names.Add(ds_name.Name);
                ds_name = ds_names.Next();
            }
            return fc_names;
        }
        public static void add_field(Geoprocessor gp, string in_table, string field_name, string field_type)
        {
            AddField addfield = new AddField();
            addfield.in_table = in_table;
            addfield.field_name = field_name;
            addfield.field_type = field_type;
            gp.Execute(addfield, null);
        }

        public static IFeatureCursor spatialQuery(IFeatureClass inFeatureClass, IGeometry selectGeometry, ESRI.ArcGIS.Geodatabase.esriSpatialRelEnum spatialRelType)
        {
            ISpatialFilter spatialFilter = new SpatialFilter() as ISpatialFilter;
            spatialFilter.Geometry = selectGeometry;
            spatialFilter.GeometryField = inFeatureClass.ShapeFieldName;
            spatialFilter.SpatialRel = spatialRelType;

            IFeatureCursor selection_cursor = inFeatureClass.Search(spatialFilter, true);
            return selection_cursor;
        }

        public static IPolyline offset_line(IPolyline source, double offset_value)
        {
            IConstructCurve3 construct = new Polyline() as IConstructCurve3;

            //Rounded, Mitered, etc
            object offset = esriConstructOffsetEnum.esriConstructOffsetRounded;
            //Method call (0.001 or -0.001 determines left/right)
            construct.ConstructOffset(source, offset_value, ref offset);

            return construct as IPolyline;
        }

        public static IPoint ConstructAngleDistance(IPoint point, double angle, double distance)
        {
            //Convert the angle degrees to radians
            double angleRad = angle * 2 * Math.PI / 360;
            IConstructPoint construcionPoint = new Point() as IConstructPoint;
            construcionPoint.ConstructAngleDistance(point, angleRad, distance);
            return construcionPoint as IPoint;
        }

        public static double get_angle(IPoint pt1, IPoint pt2)
        {

            double delta_y = pt2.Y - pt1.Y;
            double delta_x = pt2.X - pt1.X;
            double a = Math.Atan2(delta_y, delta_x) * 180 / Math.PI;
            //double a = (pt1.Y - pt2.Y) / (pt1.X - pt2.X);
            return a;
        }

        public static IPoint get_mid_point(IPolyline line)
        {
            IPoint point = new Point();
            line.QueryPoint(esriSegmentExtension.esriExtendAtFrom, line.Length / 2, false, point);
            return point;
        }

        public static IPoint get_some_point(IPolyline line, double len)
        {
            IPoint point = new Point();
            line.QueryPoint(esriSegmentExtension.esriExtendAtFrom, len, false, point);
            return point;
        }


        public static IPolyline create_line(IPoint point1, IPoint point2)
        {
            IPolyline polyline = new Polyline() as IPolyline;
            IPointCollection pt_cl = polyline as IPointCollection;
            object o = Type.Missing;
            pt_cl.AddPoint(point1, ref o, ref o);
            pt_cl.AddPoint(point2, ref o, ref o);
            polyline = pt_cl as IPolyline;
            return polyline;
        }

        public static IPolygon CreatePolygonByPoints(List<IPoint> points_list)
        {

            IPolygon pPolygon;
            IPointCollection polygon_pt_cl = new Polygon();
            IPolyline pPolyline = new Polyline() as IPolyline;
            // create new pointcollection
            IPointCollection line_pt_cl = pPolyline as IPointCollection;
            object o = Type.Missing;
            foreach (IPoint point in points_list)
            {
                line_pt_cl.AddPoint(point, ref o, ref o);
            }
            //create polygon from pointcollection
            polygon_pt_cl.AddPointCollection(line_pt_cl);
            pPolygon = polygon_pt_cl as IPolygon;
            pPolygon.Close();
            return pPolygon;
        }

        public static double get_polygon_vertices(IPolygon polygon)
        {
            double vertices = 0;
            if (polygon != null)
            {
                polygon.SnapToSpatialReference();

                double x = 0;
                double y = 0;
                IPoint pt;
                int partIndx;
                int vertxIndx;
                IPointCollection pt_cl = polygon as IPointCollection;
                IEnumVertex2 en = pt_cl.EnumVertices as IEnumVertex2;
                en.Reset();
                en.Next(out pt, out partIndx, out vertxIndx);
                while (pt != null)
                {
                    x = x + pt.X - 130000;
                    y = y + pt.Y - 373600;
                    vertices = x + y;
                    en.Next(out pt, out partIndx, out vertxIndx);
                }
            }
            return vertices;
        }

        public static void ExportFeatureClass(Geoprocessor gp, string in_fc, string out_fc, string sql)
        {
            Select select = new Select();
            select.in_features = in_fc;
            select.out_feature_class = out_fc;
            select.where_clause = sql;
            gp.Execute(select, null);
        }

        public static string ListToString(List<object> li)
        {
            List<string> str_list = new List<string>();
            foreach (object x in li)
            {
                str_list.Add(x.ToString());
            }
            string str = string.Join(",", str_list.ToArray());
            str = str.Replace(",", ", ");
            return str;
        }

        public static bool IsSameGeometry(IGeometry geom1, IGeometry geom2)
        {
            geom1.SnapToSpatialReference();
            geom2.SnapToSpatialReference();
            IRelationalOperator rel1 = geom1 as IRelationalOperator;
            bool relEqual = rel1.Equals(geom2);
            return relEqual;
        }

        public static void calculate_field(Geoprocessor gp, string in_table, string field_name, string expression, string ex_type)
        {
            CalculateField calculateField = new CalculateField();
            calculateField.in_table = in_table;
            calculateField.field = field_name;
            calculateField.expression = expression;
            calculateField.expression_type = ex_type;
            gp.Execute(calculateField, null);
        }

        public static void append(Geoprocessor gp, string in_table, string target)
        {
            Append ap = new Append();
            ap.inputs = in_table;
            ap.target = target;
            ap.schema_type = "NO_TEST";
            gp.Execute(ap, null);
        }

        public static IPolygon MergePolygons(IGeometry polygon1, IGeometry polygon2, IFeatureClass fc_for_spatial_reference)
        {
            IGeometry geometry_bag = new GeometryBag();
            IGeoDataset ds = fc_for_spatial_reference as IGeoDataset;
            geometry_bag.SpatialReference = ds.SpatialReference;
            IGeometryCollection gc = geometry_bag as IGeometryCollection;
            object missing = Type.Missing;
            gc.AddGeometry(polygon1, ref missing, ref missing);
            gc.AddGeometry(polygon2, ref missing, ref missing);
            ITopologicalOperator union_polygon = new Polygon() as ITopologicalOperator;
            union_polygon.ConstructUnion(geometry_bag as IEnumGeometry);
            IPolygon new_polygon = union_polygon as IPolygon;
            return new_polygon;
        }

        public static void select_by_loc(Geoprocessor gp, string in_layer, string select_layer, string method)
        {
            SelectLayerByLocation select_by = new SelectLayerByLocation();
            select_by.in_layer = in_layer;
            select_by.select_features = select_layer;
            select_by.overlap_type = method;
            gp.Execute(select_by, null);
        }

        public static void spatial_join(Geoprocessor gp, string in_layer, string join_layer, string out_fc)
        {
            ESRI.ArcGIS.AnalysisTools.SpatialJoin sj = new ESRI.ArcGIS.AnalysisTools.SpatialJoin();
            sj.target_features = in_layer;
            sj.join_features = join_layer;
            sj.out_feature_class = out_fc;
            gp.Execute(sj, null);
        }
        public static void join_table(Geoprocessor gp, string in_table, string in_field, string join_table, string join_field)
        {

            AddJoin join = new AddJoin();
            join.in_layer_or_view = in_table;
            join.in_field = in_field;
            join.join_table = join_table;
            join.join_field = join_field;
            //join.join_type = "KEEP_ALL";
            gp.Execute(join, null);
        }

        public static void join_table_keep_common(Geoprocessor gp, string in_table, string in_field, string join_table, string join_field)
        {
            AddJoin join = new AddJoin();
            join.in_layer_or_view = in_table;
            join.in_field = in_field;
            join.join_table = join_table;
            join.join_field = join_field;
            join.join_type = "KEEP_COMMON";
            gp.Execute(join, null);
        }

        public static void remove_join(Geoprocessor gp, string in_table, string join_table)
        {
            RemoveJoin remove = new RemoveJoin();
            remove.in_layer_or_view = in_table;
            remove.join_name = join_table;
            gp.Execute(remove, null);
        }

        public static void select_layer_by_att(Geoprocessor gp, string in_layer, string where, string selection_type)
        {
            SelectLayerByAttribute SelectLayetByAtt = new SelectLayerByAttribute();
            SelectLayetByAtt.in_layer_or_view = in_layer;
            SelectLayetByAtt.selection_type = selection_type;
            SelectLayetByAtt.where_clause = where;
            gp.Execute(SelectLayetByAtt, null);
        }

    	public static ICursor create_join_cursor(IFeatureWorkspace featureWorkspace, string tables, string sub_fields, string where_clause )
        {
            // Create the query definition.
            IQueryDef queryDef = featureWorkspace.CreateQueryDef();

            // Provide a list of tables to join.
            queryDef.Tables = tables;// "streets, altname";

            // Set the subfields and the WhereClause (in this case, the join condition).
            queryDef.SubFields = sub_fields; //"streets.NAME, streets.TYPE, altname.ST_NAME, altname.ST_TYPE"
            queryDef.WhereClause = where_clause;

            // Get a cursor of the results and find the indexes of the fields to display.
            //using (ComReleaser comReleaser = new ComReleaser())
            //{
              ICursor cursor = queryDef.Evaluate();
                return cursor;
            //}

                //comReleaser.ManageLifetime(cursor);
                //int streetsNameIndex = cursor.FindField("streets.NAME");
                //int streetsTypeIndex = cursor.FindField("streets.TYPE");
                //int altnameNameIndex = cursor.FindField("altname.ST_NAME");
                //int altnameTypeIndex = cursor.FindField("altname.ST_TYPE");

                //// Use the cursor to step through the results, displaying the names and altnames of each 
                //// street.
                //IRow row = null;
                //while ((row = cursor.NextRow()) != null)
                //{
                //    Console.WriteLine("Street name: {0} {1}. - Alt. name: {2} {3}.",
                //        row.get_Value(streetsNameIndex), row.get_Value(streetsTypeIndex),
                //        row.get_Value(altnameNameIndex), row.get_Value(altnameTypeIndex));
                //}
            //}

        }

    	public static List<string> ListFeatureClasses(Geoprocessor gp, string ws)
        {
            // List all feature classes in the workspace starting with d.
            gp.SetEnvironmentValue("workspace", ws);
            IGpEnumList fcs = gp.ListFeatureClasses("*", "", "");
            string fc = fcs.Next();
            List<string> li = new List<string>();
            while (fc != "")
            {

                //Console.WriteLine(fc);
                li.Add(fc);
                fc = fcs.Next();
            }
            return li;
        }

    	public static void DeleteFeatureClass(Geoprocessor gp, string input_fc)
        {
            //object dt = "";
            //bool ex = gp.Exists(input_fc, ref dt);
            //if (ex == true)
            //{
            Delete delete = new Delete();
            delete.in_data = input_fc;
            gp.Execute(delete, null);
            //}
        }



        public static IFeatureLayer getLayerFromMxd(IMap map, string layer_name)
        {
            IEnumLayer layers = map.get_Layers();
            ILayer layer;
            IFeatureLayer featureLayer = null;
            layer = layers.Next();
            while (layer != null)
            {
                if (layer is FeatureLayer)
                {
                    if (layer.Name.ToString() == layer_name)
                    {
                        Console.WriteLine(layer.Name.ToString());
                        featureLayer = layer as IFeatureLayer;
                    }
                }
                layer = layers.Next();
            }

            return featureLayer;
        }

        public static string getLayerPathFromMxd(IMap map, string layer_name)
        {
            string layergdb = "";
            IEnumLayer layers = map.get_Layers();
            ILayer layer;
            layer = layers.Next();
            while (layer != null)
            {
                if (layer is FeatureLayer)
                {
                    if (layer.Name.ToString() == layer_name)
                    {
                        Console.WriteLine(layer.Name.ToString());
                        IFeatureLayer featureLayer = layer as IFeatureLayer;
                        IDataset ds = featureLayer.FeatureClass as IDataset;
                        layergdb = ds.Workspace.PathName;
                    }
                }
                layer = layers.Next();
            }

            return layergdb;
        }


        public static void ZoomToSelection(IMapDocument pMxDoc, IFeatureLayer pFeatureLayer, string where_clause)
        {

            IMap pMap = (IMap)pMxDoc.ActiveView;
            pMap.ClearSelection();
            ILayer pLayer = pFeatureLayer as ILayer;
            IFeatureSelection pFeatureSelection = pLayer as IFeatureSelection;
            IFeatureClass pFeatureClass = pFeatureLayer.FeatureClass;
            IQueryFilter pFilter = new QueryFilter();
            IEnvelope pEnv = new Envelope() as IEnvelope;

            pFilter.WhereClause = where_clause;

            IFeatureCursor pFeatureCursor = pFeatureClass.Search(pFilter, false);
            IFeature pFeature = pFeatureCursor.NextFeature();

            while (pFeature != null)
            {

                pFeatureSelection.Add(pFeature);
                pEnv.Union(pFeature.ShapeCopy.Envelope);

                IGeometry pgeom = (IGeometry)pFeature.Shape;
                //pMap.SelectByShape(pgeom, null, false);
                pFeature = pFeatureCursor.NextFeature();

            }


            pMxDoc.ActiveView.Extent = pEnv;
            pMxDoc.ActiveView.Refresh();

        }
    }
}
