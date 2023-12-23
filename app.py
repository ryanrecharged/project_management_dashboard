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
    
    login_col2.markdown('<span id="button-logout"></span>', unsafe_allow_html=True)
    login_col2.button("Login", key="button_login", 
              on_click=UTILS.validate_login)
    
    # Login Error
    if st.session_state.login_error:
        login_col2.warning(st.session_state.login_error_message)    
    
    d, e, f, g = login_col2.tabs([" ", 'Terms', 'About this app', 'Register'])
    
    
        
# Menu
def menu():
    menu_col1, menu_col2, menu_col3 = st.columns([3,2,3])
    
    menu_col2.subheader("Choose version")
    
    menu_col2.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
    menu_col2.button(f"{st.session_state.report_title} Report", key="button_update", 
              on_click=UTILS.update_session_state, args=("page", "entry"))
    menu_col2.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
    menu_col2.button("Project Manager", key="button_report",
              on_click=UTILS.update_session_state, args=("page", "report"))

# Structure Page
def structure_page():
    st.subheader(f"{st.session_state.report_title} Report")
    st.markdown("***")
    st.caption(st.session_state.project_name)
    line_col, sta_col, spcr_col, opts_col = st.columns([3, 4, 3, 2])
    
    select_tab, update_tab, assign_tab, attach_tab = line_col.tabs(
        ["Select", "Update", "Assign", "Attach"]
        )
    
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
        
        
    # Chat box
    with spcr_col.expander("Communications hub"):
        st.selectbox(
            'To', options=['Lampkin', 'Skelly'], 
            placeholder="[Select recipient]", index=None, 
            label_visibility='collapsed'
            )
        st.selectbox(
            'Medium', options=['SMS'], 
            placeholder="[Select medium]", index=None,
            label_visibility='collapsed'
            )
        
        st.text_area(
            'Contents of Message', placeholder="[contents of message]", 
            label_visibility='collapsed', height=200)
        st.code('Enter history of messages here\nlampkin: [completed stage of "XYSA"]')
    
    # Attach document tab
    STATUS.produce_attach_document(attach_tab)
    
    
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
            sv_disabled = True
        else:
            st.markdown('<span id="button-pending"></span>', unsafe_allow_html=True)
            sv_disabled = False
            
        st.button("Save Changes", disabled=sv_disabled,
            on_click=UTILS.save_filtered_df, args=(struct_df, filter_df,)
            )
        
    with tmline:
        st.altair_chart(
            reports.gantt_chart(filter_df), use_container_width=False
        )
    
    # with tabr2: # Tableau-style
    #    stc.html(reports.tableau_style(filter_df), scrolling=True, height=920)
    
    with admin_tab:
        st.multiselect(
            'Settings categories', 
            options = ['Preferences', 'User access', 'File gateway',
                       'Project settings', 'Records'], # # Create task lists, # Sorting, filtering columns # Customize stages
            placeholder='[select to display]',
            key = 'admin_settings_multiselect')
        
        reports.admin_settings_display(struct_df) 



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

