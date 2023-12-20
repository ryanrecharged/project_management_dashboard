import boto3
import app_control as CONTROL
import status_control as STATUS
import utils as UTILS

import streamlit as st
import pandas as pd

import reports
import user


print('PAGE RELOAD')

CONTROL.set_page_confige()

hide_st_style = CONTROL.apply_custom_css()
st.markdown(hide_st_style, unsafe_allow_html=True)
floating_container = CONTROL.apply_custom_floating_container()
st.markdown(floating_container, unsafe_allow_html=True)
button_style = CONTROL.apply_custom_button_styling()
st.markdown(button_style, unsafe_allow_html=True)

CONTROL.initialize_state_variables()

try:
    struct_df = UTILS.load_initial_dataframe()
except:
    st.session_state.page = 'refresh'
    
# No internet
def no_internet():
    st.warning("Need network connection to access database")
    st.error("Connect to internet and refresh page")

# Login
def login():
    login_col1, login_col2, login_col3 = st.columns([3,2,3])
    login_col2.subheader("Login Page")
    
    # Login Form
    login_col2.text_input("Username", 
        key="login_form_username_key", 
        on_change=UTILS.callback_sessions, 
        args=('login_form_username', 'login_form_username_key'))
    
    login_col2.text_input("Password", 
        key="login_form_pass_key", type="password",
        on_change=UTILS.callback_sessions, 
        args=('login_form_pass', 'login_form_pass_key'))
    
    login_col2.button("Login", key="button_login", 
              on_click=UTILS.validate_login)
    
    # Login Error
    if st.session_state.login_error:
        login_col2.warning(st.session_state.login_error_message)
        
# Menu
def menu():
    menu_col1, menu_col2, menu_col3 = st.columns([3,2,3])
    
    menu_col2.subheader("Choose version")
    
    menu_col2.button("Structure Report", key="button_update", 
              on_click=UTILS.update_session_state, args=("page", "entry"))
    menu_col2.button("Project Manager", key="button_report",
              on_click=UTILS.update_session_state, args=("page", "report"))

# Structure Page
def structure_page():
    st.subheader("Structure Report")
    st.markdown("***")
    st.caption(st.session_state.project_name)
    line_col, sta_col, spcr_col, opts_col = st.columns([3, 4, 3, 2])
    
    select_tab, update_tab, assign_tab = line_col.tabs(["Select", "Update", "Assign"])
    
    STATUS.produce_structure_filter(struct_df, select_tab)
    STATUS.produce_structure_selection(struct_df, select_tab)
    
    # Structure Status section
    s_s = UTILS.filter_dataframe_by_select_station(struct_df)
    STATUS.produce_status_info_column(sta_col, s_s)
    STATUS.produce_status_notes(sta_col, s_s)
    STATUS.produce_status_assignment(sta_col, s_s)
    STATUS.produce_file_hub(sta_col, s_s)
    
    # Structure Modification section
    line = st.session_state.select_line
    station = st.session_state.select_station
    if update_tab.toggle(
        f"Update: **{line}-{station}**", key="toggle_update_status"
        ):
        STATUS.produce_update_form(s_s, update_tab, struct_df)
    if assign_tab.toggle(
        f"Assign: **{line}-{station}**", key="toggle_assign_status"
        ):
        STATUS.produce_assignment_form(s_s, assign_tab, struct_df)
    
    # Global options section
    STATUS.create_options_column(opts_col)

# Report Page
def report_page():
    
    # Establish page structure
    st.subheader("Project Manager")
    st.markdown("***")
    st.caption(st.session_state.project_name)
    report_col, options_col = st.columns([5,1])
    table, tmline, admin_tab  = report_col.tabs(["Table", "Timeline", "Admin"])
    
    # Filter conflicts
    filter_df = reports.filter_only_conflicts(struct_df)
    
    # Sort dataframe
    filter_df = reports.sort_dataframe_per_selection(filter_df)
    
    # Filter by selection
    filter_df = reports.filter_dataframe_per_selection(filter_df)
    
    crew_opts = [_ for _ in CONTROL.crew_chiefs().keys()]
    
    with options_col:    
        # Create option lists for controls
        outage_opts = struct_df['outage_no'].unique()
        str_opts = filter_df['structure_name'].unique()
        
        # Generate "options" column
        reports.display_options_frame(crew_opts, outage_opts, str_opts, struct_df)
        
    with table:
        stage_opts = [v['display_name'] for (k,v) in CONTROL.project_stages().items()]
        reports.table_display(filter_df, stage_opts, crew_opts)
        
        er = st.session_state.table_editor['edited_rows']
        ar = st.session_state.table_editor['added_rows']
        dr = st.session_state.table_editor['deleted_rows']
        
        if len(er) + len(ar) + len(dr) == 0:
            pass
        else:
            st.markdown('<span id="button-pending"></span>', unsafe_allow_html=True)
            
        st.button("Save Changes", 
            on_click=UTILS.save_filtered_df, args=(struct_df, filter_df,)
            )
        
    with tmline:
        st.altair_chart(
            reports.gantt_chart(filter_df), use_container_width=False
        )
    
    # with tabr2: # Tableau-style
    #    stc.html(reports.tableau_style(filter_df), scrolling=True, height=920)
    
    with admin_tab:
        tstmp = pd.Timestamp.now().strftime("%Y-%m-%d.%H%M")
        with st.expander("User settings: :orange[Change project name and add users]"):
            ex_col1, ex_col2 = st.columns(2)
            ex_col1.text_input(
                label='Name of Project', key="admin_project_name",
                placeholder="Boonville, NY: National Grid SmartPath Connect PNO 22.XXXX",
                on_change=user.set_project_name
                )
            
            if ex_col2.toggle('Add new user to project'):
                with ex_col2.form("new_user_entry", border=False):
                    st.text_input(
                        label="Username", placeholder='Username: last_name', 
                        label_visibility='collapsed')
                    st.text_input(
                        label='Password', placeholder='Password: [auto-generated]', 
                        label_visibility='collapsed', disabled=True)
                    st.text_input(
                        label='Email address', placeholder='Contact: 631.555.1234',
                        label_visibility='collapsed')
                    st.checkbox('Make user Administrator', key='new_user_admin')
                    st.form_submit_button("Submit") 
        
        with st.expander("Records and logs: :orange[Obtain digital access to the database]"):
            st.download_button(
                "Download database", UTILS.convert_df(struct_df.copy()),
                f"ctm_internal_boonville_{tstmp}.csv", "text/csv"
                )
            st.button("Print log file", key="button_print_log", disabled=True)
            
            
        with st.expander("File repository: :orange[Upload files for synchronous field work]"):
            
            with st.form('file_uploader', clear_on_submit=True, border=False):
                col1, col2 = st.columns(2)
                with col1:
                    hubs = st.file_uploader('STRUCTURE HUBS', type='csv')
                    dxf = st.file_uploader('DXF FILES', type='dxf')
                    trav = st.file_uploader('CONTROL POINTS', type='csv')
                    if trav is not None:
                        s3 = boto3.client(
                            service_name="s3",
                            region_name=st.secrets.AWS_S3_REGION,
                            aws_access_key_id=st.secrets.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=st.secrets.AWS_SECRET_ACCESS_KEY,
                        )
                        
                        ts = pd.Timestamp.now().strftime("%Y%m%d.%H%M")
                        name = f"{st.secrets.AWS_TRAV_KEY}{ts}.csv"
                        s3.upload_fileobj(trav, st.secrets.AWS_BUCKET, name)
                        struct_df['trav_location'] = f'pm_{ts}.csv'
                        UTILS.save_database_changes(struct_df)
                    if dxf is not None:
                        s3 = boto3.client(
                            service_name="s3",
                            region_name=st.secrets.AWS_S3_REGION,
                            aws_access_key_id=st.secrets.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=st.secrets.AWS_SECRET_ACCESS_KEY,
                        )
                        
                        ts = pd.Timestamp.now().strftime("%Y%m%d.%H%M")
                        name = f"{st.secrets.AWS_DXF_KEY}{ts}.csv"
                        s3.upload_fileobj(dxf, st.secrets.AWS_BUCKET, name)
                        struct_df['dxf_location'] = f'pm_{ts}.csv'
                        UTILS.save_database_changes(struct_df)
                    if hubs is not None:
                        s3 = boto3.client(
                            service_name="s3",
                            region_name=st.secrets.AWS_S3_REGION,
                            aws_access_key_id=st.secrets.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=st.secrets.AWS_SECRET_ACCESS_KEY,
                        )
                        
                        ts = pd.Timestamp.now().strftime("%Y%m%d.%H%M")
                        name = f"{st.secrets.AWS_STR_KEY}{ts}.csv"
                        s3.upload_fileobj(hubs, st.secrets.AWS_BUCKET, name)
                        struct_df['structure_location'] = f'pm_{ts}.csv'
                        UTILS.save_database_changes(struct_df)
                
                with col2:
                    col2.checkbox(
                        'Assign to all structure reports', 
                        value=True, disabled=True
                        )
                    col2.selectbox(
                        "Structures to associate", 
                        options=['All', 'Single', 'Multi'],
                        index=0, label_visibility='collapsed',
                        disabled=True)
            
                st.form_submit_button('Upload')


# Main Logic for Navigation
UTILS.validate_login()

if st.session_state.page == "login":
    login()
elif st.session_state.page == "selection":
    menu()
elif st.session_state.page == "entry":
    structure_page()
elif st.session_state.page == "report":
    report_page()
elif st.session_state.page == "refresh":
    no_internet()

