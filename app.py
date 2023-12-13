import app_control as CONTROL
import data as DATA
import status_control as STATUS
import utils as UTILS

import streamlit as st
import pandas as pd
import altair as alt

import reports


print('PAGE RELOAD')

CONTROL.set_page_confige()

hide_st_style = CONTROL.apply_custom_css()
st.markdown(hide_st_style, unsafe_allow_html=True)

CONTROL.initialize_state_variables()
struct_df = UTILS.load_initial_dataframe()

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
    line_col, sta_col, opts_col = st.columns([2, 3, 3])
    
    select_tab, update_tab, assign_tab = line_col.tabs(["Select", "Update", "Assign"])
    
    # TODO: Rename these functions to more descriptive
    STATUS.filter_options(struct_df, select_tab)
    STATUS.structure_function(struct_df, select_tab)
    
    STATUS.work_status(struct_df, update_tab, assign_tab, sta_col)
    UTILS.create_options_column(opts_col, opt_type="Project Manager")

# Report Page
def report_page():
    st.subheader("Project Manager")
    report_col1, report_col2 = st.columns([5,1])
    table, tabr1, tabr3  = report_col1.tabs(
        ["Table", "Timeline", "Admin"]
        )
    
    # FILTER CONFLICTS
    if st.session_state.pm_conflicts_only:
        filter_df = struct_df.loc[struct_df['timeline_conflict'] == True].copy()
    else:
        filter_df = struct_df.copy()
    
    # SORT COLUMNS
    if st.session_state.pm_sort_toggle:
        s_val = st.session_state['pm_sort_by']
        
        filter_df['stage_map'] = filter_df['stage'].map(CONTROL.project_display_names()).map(CONTROL.project_stages('stage_order'))

        m = {
            'Stage' : ['stage_map', 'projected_end_date'],
            'Station' : ['primary_key_line', 'primary_key_sta'],
        }
        filter_df.sort_values(m[s_val], inplace=True)
    
    reports.display_report_column_options(report_col2, filter_df)
    reports.display_report_column_tabs([table, tabr1, tabr3], filter_df)
    
    
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

