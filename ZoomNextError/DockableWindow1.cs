using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using ESRI.ArcGIS.Geodatabase;
using ESRI.ArcGIS.DataSourcesGDB;
using ESRI.ArcGIS.Geoprocessor;
using ESRI.ArcGIS.Geoprocessing;
using ESRI.ArcGIS.DataManagementTools;
using ESRI.ArcGIS.Geometry;
using ESRI.ArcGIS.AnalysisTools;
using ESRI.ArcGIS.Carto;
using AO = ArcObjectsTools.ArcObjects;


namespace ZoomNextError
{
    /// <summary>
    /// Designer class of the dockable window add-in. It contains user interfaces that
    /// make up the dockable window.
    /// </summary>
    public partial class DockableWindow1 : UserControl
    {
        public DockableWindow1(object hook)
        {
            InitializeComponent();
            this.Hook = hook;
        }

        /// <summary>
        /// Host object of the dockable window
        /// </summary>
        private object Hook
        {
            get;
            set;
        }

        /// <summary>
        /// Implementation class of the dockable window add-in. It is responsible for 
        /// creating and disposing the user interface class of the dockable window.
        /// </summary>
        public class AddinImpl : ESRI.ArcGIS.Desktop.AddIns.DockableWindow
        {
            private DockableWindow1 m_windowUI;

            public AddinImpl()
            {
            }

            protected override IntPtr OnCreateChild()
            {
                m_windowUI = new DockableWindow1(this.Hook);
                return m_windowUI.Handle;
            }

            protected override void Dispose(bool disposing)
            {
                if (m_windowUI != null)
                    m_windowUI.Dispose(disposing);

                base.Dispose(disposing);
            }



        }

        public static int current_OID = -1;
        public static int Last_OID = -1;
        public static int next_OID = -1;
        public static int counter_items = 0;
        List<int> List_acc = new List<int>();
        public static string get(List<int> list1)
        {
            string Collect = "";
            foreach (object i in list1)
            {
                Collect = Collect + i.ToString()+",";
            }
            Collect = Collect.Remove(Collect.Length - 1);
            return Collect;
        }

        private void button1_Click(object sender, EventArgs e)
        {
            IMapDocument mxd = ZoomNextError.ArcMap.Application.Document as IMapDocument;
            IMap map = mxd.get_Map(0);
            string gdb = AO.getLayerPathFromMxd(map, "חלקות לעריכה");



            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            else
            {
                ITable table = AO.open_table(gdb, "Errors");
                int sum_items = table.RowCount(null);
                if (table != null)
                {
                    counter_items++;
                    int counter = 0;
                    ICursor cursor = AO.create_table_cursor_with_query(table, "\"OBJECTID\" > " + current_OID.ToString());
                    IRow row = cursor.NextRow();
                    while (counter < 1 && row != null)
                    {
                        if (counter_items < sum_items)
                        {
                            counter++;
                            current_OID = row.OID;
                            //MessageBox.Show(current_OID.ToString());
                            string GushNum = row.Value[row.Fields.FindField("GushNum")];
                            string ParcelNum = row.Value[row.Fields.FindField("ParcelNum")];
                            string GushSfx = row.Value[row.Fields.FindField("GushSfx")];
                            object ErrDescription = row.Value[row.Fields.FindField("ErrDescription")];

                            string query = "OBJECTID < 0";
                            if (GushNum == "0" && ParcelNum == "0" && ErrDescription != null)
                            {
                                if (ErrDescription.ToString().Contains("OID:"))
                                {
                                    //MessageBox.Show(System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value);
                                    string oid = System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value;
                                    query = "OBJECTID = " + oid;
                                }
                            }
                            else
                            {
                                query = "GUSH_NUM = " + GushNum +
                                    " AND PARCEL = " + ParcelNum +
                                    " AND GUSH_SUFFIX = " + GushSfx;
                            }


                            IFeatureLayer flayer = AO.getLayerFromMxd(map, "חלקות לעריכה");

                            AO.ZoomToSelection(mxd, flayer, query);
                            List_acc.Add(row.OID);
                            //MessageBox.Show(get(List_acc));
                            row = cursor.NextRow();

                            if (ErrDescription != null)
                            {
                                label3.Text = ErrDescription.ToString();
                                label5.Text = sum_items.ToString() +" / " + List_acc.Count.ToString();
                            }
                            else
                            {
                                label3.Text = "ללא תיאור";
                                label5.Text = "";
                            }

                        }
                        else
                        {
                            current_OID   = -1;
                            counter_items = 0;
                        }
                    }
                }
            }

            
        }

        private void button2_Click(object sender, EventArgs e)
        {

            IMapDocument mxd = ZoomNextError.ArcMap.Application.Document as IMapDocument;
            IMap map = mxd.get_Map(0);
            string gdb = AO.getLayerPathFromMxd(map, "חלקות לעריכה");

            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }

            if (List_acc.Count > 1)
            {
                counter_items = counter_items - 1;
                Last_OID = List_acc[List_acc.Count - 1];
                ITable table   = AO.open_table(gdb, "Errors");
                int sum_items = table.RowCount(null);
                ICursor cursor = AO.create_table_cursor_with_query(table, "\"OBJECTID\" = " + Last_OID.ToString());
                IRow row       = cursor.NextRow();
                while (row != null)
                {

                    string GushNum = row.Value[row.Fields.FindField("GushNum")];
                    string ParcelNum = row.Value[row.Fields.FindField("ParcelNum")];
                    string GushSfx = row.Value[row.Fields.FindField("GushSfx")];
                    object ErrDescription = row.Value[row.Fields.FindField("ErrDescription")];

                    string query = "OBJECTID < 0";
                    if (GushNum == "0" && ParcelNum == "0" && ErrDescription != null)
                    {
                        if (ErrDescription.ToString().Contains("OID:"))
                        {
                            //MessageBox.Show(System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value);
                            string oid = System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value;
                            query = "OBJECTID = " + oid;
                        }
                    }
                    else
                    {
                        query = "GUSH_NUM = " + GushNum +
                            " AND PARCEL = " + ParcelNum +
                            " AND GUSH_SUFFIX = " + GushSfx;
                    }

                    IFeatureLayer flayer = AO.getLayerFromMxd(map, "חלקות לעריכה");
                    AO.ZoomToSelection(mxd, flayer, query);
                    List_acc.RemoveAt(List_acc.Count - 1);
                    //MessageBox.Show(get(List_acc));
                    current_OID = Last_OID;
                    row = cursor.NextRow();


                    if (ErrDescription != null)
                    {
                        label3.Text = ErrDescription.ToString();
                        label5.Text = sum_items.ToString() +" / " + List_acc.Count.ToString();
                    }
                    else
                    {
                        label3.Text = "ללא תיאור";
                        label5.Text = "";
                    }

                }
            }

        }

        private void button4_Click(object sender, EventArgs e)
        {
            current_OID = -1;
            Last_OID = -1;
            next_OID = -1;
            counter_items = 0;
            List_acc.Clear();
            IMapDocument mxd = ZoomNextError.ArcMap.Application.Document as IMapDocument;
            IMap map = mxd.get_Map(0);
            string gdb = AO.getLayerPathFromMxd(map, "חלקות לעריכה");



            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            else
            {
                ITable table = AO.open_table(gdb, "Errors");
                int sum_items = table.RowCount(null);
                if (table != null)
                {
                    counter_items++;
                    int counter = 0;
                    ICursor cursor = AO.create_table_cursor_with_query(table, "\"OBJECTID\" > " + current_OID.ToString());
                    IRow row = cursor.NextRow();
                    while (counter < 1 && row != null)
                    {
                        if (counter_items < sum_items)
                        {
                            counter++;
                            current_OID = row.OID;
                            //MessageBox.Show(current_OID.ToString());
                            string GushNum = row.Value[row.Fields.FindField("GushNum")];
                            string ParcelNum = row.Value[row.Fields.FindField("ParcelNum")];
                            string GushSfx = row.Value[row.Fields.FindField("GushSfx")];
                            object ErrDescription = row.Value[row.Fields.FindField("ErrDescription")];

                            string query = "OBJECTID < 0";
                            if (GushNum == "0" && ParcelNum == "0" && ErrDescription != null)
                            {
                                if (ErrDescription.ToString().Contains("OID:"))
                                {
                                    //MessageBox.Show(System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value);
                                    string oid = System.Text.RegularExpressions.Regex.Match(ErrDescription.ToString(), @"\d+").Value;
                                    query = "OBJECTID = " + oid;
                                }
                            }
                            else
                            {
                                query = "GUSH_NUM = " + GushNum +
                                    " AND PARCEL = " + ParcelNum +
                                    " AND GUSH_SUFFIX = " + GushSfx;
                            }

                            IFeatureLayer flayer = AO.getLayerFromMxd(map, "חלקות לעריכה");

                            AO.ZoomToSelection(mxd, flayer, query);
                            List_acc.Add(row.OID);
                            //MessageBox.Show(get(List_acc));
                            row = cursor.NextRow();

                            if (ErrDescription != null)
                            {
                                label3.Text = ErrDescription.ToString();
                                label5.Text = sum_items.ToString() +" / " + List_acc.Count.ToString();
                            }
                            else
                            {
                                label3.Text = "ללא תיאור";
                                label5.Text = "";
                            }

                        }
                        else
                        {
                            current_OID = -1;
                            counter_items = 0;
                        }
                    }
                }
            }
        }
    }
}
