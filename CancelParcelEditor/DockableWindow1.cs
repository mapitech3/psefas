using System;
using System.Linq;
using System.IO;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using ESRI.ArcGIS.ArcMapUI;
using AO = ArcObjectsTools.ArcObjects;
using System.Windows.Forms;
using ESRI.ArcGIS.Geodatabase;
using ESRI.ArcGIS.DataSourcesGDB;
using ESRI.ArcGIS.Geoprocessor;
using ESRI.ArcGIS.Geoprocessing;
using ESRI.ArcGIS.DataManagementTools;
using ESRI.ArcGIS.Geometry;
using ESRI.ArcGIS.AnalysisTools;
using ESRI.ArcGIS.Carto;
namespace CancelParcelEditor10_5
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


        private void insert_Click(object sender, EventArgs e)
        {
            IMapDocument mxd = CancelParcelEditor10_5.ArcMap.Application.Document as IMapDocument;
            IMap map = mxd.get_Map(0);
            string gdb = AO.getLayerPathFromMxd(map, "חלקות לעריכה");
            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            else
            {
                ITable table = AO.open_table(gdb, "CANCEL_PARCEL_EDIT");
                if (table != null)
                {
                    if (!String.IsNullOrEmpty(f_gush_num.Text) &&
                        !String.IsNullOrEmpty(f_parcel_num.Text) &&
                        !String.IsNullOrEmpty(t_gush_num.Text) &&
                        !String.IsNullOrEmpty(t_parcel_num.Text) &&
                        !String.IsNullOrEmpty(f_gush_suffix.Text) &&
                        !String.IsNullOrEmpty(t_gush_suffix.Text)
                        )
                    {
                        if (String.IsNullOrEmpty(f_parcel_num_e.Text) && String.IsNullOrEmpty(t_parcel_num_e.Text))
                        {
                            IRow row = table.CreateRow();
                            row.Value[row.Fields.FindField("F_GUSH_NUM")] = Convert.ToInt32(f_gush_num.Text);
                            row.Value[row.Fields.FindField("F_PARCEL_NUM")] = Convert.ToInt32(f_parcel_num.Text);
                            row.Value[row.Fields.FindField("T_GUSH_NUM")] = Convert.ToInt32(t_gush_num.Text);
                            row.Value[row.Fields.FindField("T_PARCEL_NUM")] = Convert.ToInt32(t_parcel_num.Text);
                            row.Value[row.Fields.FindField("F_GUSH_SUFFIX")] = Convert.ToInt32(f_gush_suffix.Text);
                            row.Value[row.Fields.FindField("T_GUSH_SUFFIX")] = Convert.ToInt32(t_gush_suffix.Text);
                            row.Store();
                            MessageBox.Show("רשומה נוספה");
                        }
                        else
                        {
                            if (!String.IsNullOrEmpty(f_parcel_num_e.Text) && String.IsNullOrEmpty(t_parcel_num_e.Text))
                            {
                                int f_parcel_end = Convert.ToInt32(f_parcel_num_e.Text);
                                int f_parcel_start = Convert.ToInt32(f_parcel_num.Text);
                                while (f_parcel_start <= f_parcel_end)
                                {
                                    IRow row = table.CreateRow();
                                    row.Value[row.Fields.FindField("F_GUSH_NUM")] = Convert.ToInt32(f_gush_num.Text);
                                    row.Value[row.Fields.FindField("F_PARCEL_NUM")] = f_parcel_start;
                                    row.Value[row.Fields.FindField("T_GUSH_NUM")] = Convert.ToInt32(t_gush_num.Text);
                                    row.Value[row.Fields.FindField("T_PARCEL_NUM")] = Convert.ToInt32(t_parcel_num.Text);
                                    row.Value[row.Fields.FindField("F_GUSH_SUFFIX")] = Convert.ToInt32(f_gush_suffix.Text);
                                    row.Value[row.Fields.FindField("T_GUSH_SUFFIX")] = Convert.ToInt32(t_gush_suffix.Text);
                                    row.Store();
                                    f_parcel_start++;
                                }
                                MessageBox.Show("רשומות נוספו (איחוד)");
                            }
                            if (String.IsNullOrEmpty(f_parcel_num_e.Text) && !String.IsNullOrEmpty(t_parcel_num_e.Text))
                            {
                                int t_parcel_end = Convert.ToInt32(t_parcel_num_e.Text);
                                int t_parcel_start = Convert.ToInt32(t_parcel_num.Text);
                                while (t_parcel_start <= t_parcel_end)
                                {
                                    IRow row = table.CreateRow();
                                    row.Value[row.Fields.FindField("F_GUSH_NUM")] = Convert.ToInt32(f_gush_num.Text);
                                    row.Value[row.Fields.FindField("F_PARCEL_NUM")] = Convert.ToInt32(f_parcel_num.Text);
                                    row.Value[row.Fields.FindField("T_GUSH_NUM")] = Convert.ToInt32(t_gush_num.Text);
                                    row.Value[row.Fields.FindField("T_PARCEL_NUM")] = t_parcel_start;
                                    row.Value[row.Fields.FindField("F_GUSH_SUFFIX")] = Convert.ToInt32(f_gush_suffix.Text);
                                    row.Value[row.Fields.FindField("T_GUSH_SUFFIX")] = Convert.ToInt32(t_gush_suffix.Text);
                                    row.Store();
                                    t_parcel_start++;
                                }
                                MessageBox.Show("רשומות נוספו (חלוקה)");
                            }
                        }
                    }
                    else
                    {
                        MessageBox.Show("נא למלא את כל השדות");
                    }

                }
                else
                {
                    MessageBox.Show("טבלת CANCEL_PARCEL_EDIT אינה קיימת ב gdb");
                }
            }
        }

        private void f_gush_num_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 7)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }
        }

        private void f_parcel_num_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }

        }

        private void t_gush_num_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 7)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }

        }

        private void t_parcel_num_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }

        }

        private void talar_number_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 5)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }

        }

        private void f_gush_suffix_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }


        }

        private void t_gush_suffix_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                // same as testing for decimal above, we can check the text for digits
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }
        }

        private void cancel_Click(object sender, EventArgs e)
        {

            IMapDocument mxd = CancelParcelEditor10_5.ArcMap.Application.Document as IMapDocument;
            IMap map = mxd.get_Map(0);
            string gdb = AO.getLayerPathFromMxd(map, "חלקות לעריכה");
            if (String.IsNullOrEmpty(gdb))
            {
                MessageBox.Show("שכבת חלקות לעריכה אינה קיימת במפה");
            }
            else
            {
                ITable table = AO.open_table(gdb, "CANCEL_PARCEL_EDIT");
                if (table != null)
                {
                    if (!String.IsNullOrEmpty(f_gush_num.Text) &&
                        !String.IsNullOrEmpty(f_parcel_num.Text) &&
                        !String.IsNullOrEmpty(t_gush_num.Text) &&
                        !String.IsNullOrEmpty(t_parcel_num.Text) &&
                        !String.IsNullOrEmpty(f_gush_suffix.Text) &&
                        !String.IsNullOrEmpty(t_gush_suffix.Text))
                    {

                        if (String.IsNullOrEmpty(f_parcel_num_e.Text) && String.IsNullOrEmpty(t_parcel_num_e.Text))
                        {
                            ICursor cursor = AO.create_table_cursor(table);
                            IRow row = cursor.NextRow();
                            bool deleted = false;
                            while (row != null)
                            {
                                if (!(row.Value[row.Fields.FindField("F_GUSH_NUM")] == null) &&
                                        !(row.Value[row.Fields.FindField("F_PARCEL_NUM")] == null) &&
                                        !(row.Value[row.Fields.FindField("T_GUSH_NUM")] == null) &&
                                        !(row.Value[row.Fields.FindField("T_PARCEL_NUM")] == null))
                                {
                                    if (
                                    row.Value[row.Fields.FindField("F_GUSH_NUM")] == Convert.ToInt32(f_gush_num.Text) &&
                                    row.Value[row.Fields.FindField("F_PARCEL_NUM")] == Convert.ToInt32(f_parcel_num.Text) &&
                                    row.Value[row.Fields.FindField("T_GUSH_NUM")] == Convert.ToInt32(t_gush_num.Text) &&
                                    row.Value[row.Fields.FindField("T_PARCEL_NUM")] == Convert.ToInt32(t_parcel_num.Text)
                                        )
                                    {
                                        row.Delete();
                                        MessageBox.Show("רשומה נמחקה");
                                        deleted = true;

                                    }
                                    row = cursor.NextRow();
                                }
                            }
                            if (deleted == false)
                            {
                                MessageBox.Show("לא נמצאה רשומה למחיקה");
                            }
                        }
                        else
                        {
                            if (!String.IsNullOrEmpty(f_parcel_num_e.Text) && String.IsNullOrEmpty(t_parcel_num_e.Text))
                            {
                                int f_parcel_end = Convert.ToInt32(f_parcel_num_e.Text);
                                int f_parcel_start = Convert.ToInt32(f_parcel_num.Text);
                                List<object> parcel_num_in = new List<object>();
                                while (f_parcel_start <= f_parcel_end)
                                {
                                    parcel_num_in.Add(f_parcel_start.ToString());
                                    f_parcel_start++;
                                }
                                string query = "T_PARCEL_NUM =" + t_parcel_num.Text + " AND F_PARCEL_NUM IN (" + AO.ListToString(parcel_num_in) + ")";
                                ICursor cursor = AO.create_table_cursor_with_query(table, query);
                                IRow row = cursor.NextRow();
                                bool deleted = false;
                                while (row != null)
                                {
                                    row.Delete();
                                    row = cursor.NextRow();
                                    deleted = true;
                                }
                                if (deleted == false)
                                {
                                    MessageBox.Show("לא נמצאה רשומה למחיקה");
                                }
                            }
                            if (String.IsNullOrEmpty(f_parcel_num_e.Text) && !String.IsNullOrEmpty(t_parcel_num_e.Text))
                            {
                                int t_parcel_end = Convert.ToInt32(t_parcel_num_e.Text);
                                int t_parcel_start = Convert.ToInt32(t_parcel_num.Text);
                                List<object> parcel_num_in = new List<object>();
                                while (t_parcel_start <= t_parcel_end)
                                {
                                    parcel_num_in.Add(t_parcel_start.ToString());
                                    t_parcel_start++;
                                }
                                string query = "F_PARCEL_NUM =" + f_parcel_num.Text + " AND T_PARCEL_NUM IN (" + AO.ListToString(parcel_num_in) + ")";
                                ICursor cursor = AO.create_table_cursor_with_query(table, query);
                                IRow row = cursor.NextRow();
                                bool deleted = false;
                                while (row != null)
                                {
                                    row.Delete();
                                    row = cursor.NextRow();
                                    deleted = true;
                                }
                                if (deleted == false)
                                {
                                    MessageBox.Show("לא נמצאה רשומה למחיקה");
                                }

                            }
                        }

                    }
                    else
                    {
                        MessageBox.Show("נא למלא את כל השדות");
                    }

                }
                else
                {
                    MessageBox.Show("טבלת CANCEL_PARCEL_EDIT אינה קיימת ב gdb");
                }
            }
        }


        private void buttonZoom_Click(object sender, EventArgs e)
        {
            if (!String.IsNullOrEmpty(t_gush_num.Text) &&
    !String.IsNullOrEmpty(t_parcel_num.Text))
            {
                IMapDocument mxd = CancelParcelEditor10_5.ArcMap.Application.Document as IMapDocument;
                IMap map = mxd.get_Map(0);
                IFeatureLayer flayer = AO.getLayerFromMxd(map, "חלקות להכנסה");

                string query = "GUSHNUM = " + Convert.ToInt32(t_gush_num.Text).ToString() +
                            " AND PARCEL_FINAL = " + Convert.ToInt32(t_parcel_num.Text).ToString();

                AO.ZoomToSelection(mxd, flayer, query);

            }

        }

        private void f_parcel_num_e_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                // same as testing for decimal above, we can check the text for digits
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }
        }

        private void t_parcel_num_e_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 3)
            {
                // same as testing for decimal above, we can check the text for digits
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }

        }

        private void textBox10_KeyPress(object sender, KeyPressEventArgs e)
        {
            if ((sender as TextBox).Text.Count(Char.IsDigit) < 4)
            {
                // same as testing for decimal above, we can check the text for digits
                if ((e.KeyChar < '0' || e.KeyChar > '9') && (e.KeyChar != '\b'))
                {
                    e.Handled = true;
                }
                else
                {
                    e.Handled = false;
                }
            }
            else
            {
                if (e.KeyChar == (char)8)
                {
                    e.Handled = false;
                }
                else
                {
                    e.Handled = true;
                }
            }
        }
    }
}
