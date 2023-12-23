import streamlit as st

def set_project_name():
    if st.session_state.admin_project_name != "":
        st.session_state.project_name = st.session_state.admin_project_name
    else:
        st.session_state.project_name = "Hudson, NY: HRVA Transmission Line PNO 22.XXXX"
    
def set_report_title():
    print(st.session_state.admin_title_name)
    if st.session_state.admin_title_name != "":
        st.session_state.report_title = st.session_state.admin_title_name
    else:
        st.session_state.report_title = "Structure"
        
        
