import streamlit as st

def set_project_name():
    print(st.session_state.admin_project_name)
    if st.session_state.admin_project_name != "":
        st.session_state.project_name = st.session_state.admin_project_name
    else:
        st.session_state.project_name = "Boonville, NY: National Grid SmartPath Connect PNO 22.XXXX"