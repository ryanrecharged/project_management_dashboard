import app_control as CONTROL
import utils as UTILS

import pandas as pd
import streamlit as st


def produce_status_info_column(col, station_frame):
    col.caption(
        "Info", 
        help="Lookahead Date refers to subsequent stage expected start date"
        )
    
    if station_frame.timeline_conflict.values[0]:
        col.error("Timeline conflict detected")    
              
def produce_assignment_form(df_row, update_col, df):
     
    i = df_row.index[0]
    with st.form(key='assignment_form'):
        crew_opts = [""]
        cc_dict = CONTROL.crew_chiefs()
        sub = df_row['subcontractor'].values[0]
        crew_opts.extend([k for (k,v) in cc_dict.items() if cc_dict[k]['subcontractor'] == sub])
        
        update_col.text_input(
            "Foreman notes", key="work_assign_notes", value="",
            placeholder="enter notes for field crew here",
            on_change=_insert_spreadsheet_change, args=(df, i, "work_assign_notes"))
        update_col.selectbox(
            "Assign to crew", key="work_assign_crew", 
            options=crew_opts, 
            on_change=_insert_spreadsheet_change, args=(df, i, "work_assign_crew"))
        update_col.date_input(
            "Projected completion date", key="work_assign_completion_date", 
            value=None, format="YYYY-MM-DD",
            on_change=_insert_spreadsheet_change, args=(df, i, "work_assign_completion_date"))

def produce_update_form(df_row, update_col, df):
    
    i = df_row.index[0]
    with st.form(key='work_status_form'):
        update_col.text_input(
            "Field Notes", key="work_status_field_notes", value="",
            placeholder="enter notes for project manager here",
            on_change=_insert_spreadsheet_change, args=(df, i, "work_status_field_notes"))
        update_col.slider(
            "Completion Pct", key="complete_slider", 
            min_value=0, max_value=100, value=0, step=25,
            format="%.0f%%",
            on_change=_insert_spreadsheet_change, args=(df, i, "complete_slider"))
        
        if st.session_state.complete_slider == 100:
            update_col.checkbox(
                "Applies to all structures in work area", 
                value=False, disabled=True)
            update_col.button(
                "Mark as complete", key="button_complete", 
                on_click=_work_complete, args=(df, i))

def _insert_spreadsheet_change(df: pd.DataFrame, i: int, state_key: str) -> None:
    d = {
        "work_assign_notes" : "foreman_notes",
        "work_assign_crew" : "assigned_crew",
        "work_assign_completion_date" : "projected_end_date",
        "work_status_field_notes" : "field_notes",
        "complete_slider" : "phase_completion_pct"
        }
    
    df.at[i, d[state_key]] = st.session_state[state_key]
    UTILS.save_database_changes(df)
     
def _work_complete(df: pd.DataFrame, i: int):
    
    df.at[i, "field_notes"] = ""
    df.at[i, "foreman_notes"] = ""
    df.at[i, "assigned_crew"] = ""
    df.at[i, "projected_end_date"] = df.at[i, "next_phase_end_date"]
    df.at[i, "next_phase_start_date"] = df.at[i, "next_phase_end_date"]
    df.at[i, "phase_completion_pct"] = 0
    
    ps = CONTROL.project_stages()
    stg = UTILS.remove_emojis(df.at[i, "stage"].lower())
    nxt_stage = ps[stg]['next']
    df.at[i, "stage"] = nxt_stage.capitalize()
    df.at[i, "subcontractor"] = ps[f'{nxt_stage}']['subcontractor']
    
    st.session_state.toggle_update_status = False
    st.session_state.toggle_assign_status = False
    
    UTILS.save_database_changes(df)

def produce_status_notes(col, df):
    f_n = df.iloc[0].field_notes
    r_n = df.iloc[0].foreman_notes
    m_n = df.iloc[0].ctm_notes
    crew = df.iloc[0].assigned_crew
    
    if f_n != " " and not pd.isna(f_n):
        if not pd.isna(crew):
            col.info(f"**{crew} says**: {f_n}")
        else:
            col.info(f"**Notes from the field**: {f_n}")

    if not pd.isna(r_n) and r_n != " ":
        col.success(f"**Boudreau says**: {r_n}")
    elif not pd.isna(m_n) and m_n != " ":
        col.success(f"**CTM says**: {m_n}")

def work_schedule(df):
    st.write("existing schedule printed here")
    st.toggle("Update schedule", key="toggle_update_schedule", value=False)
    
    if st.session_state.toggle_update_schedule:
        _work_schedule_form()
        
def produce_status_assignment(col, df):
    stage = df.iloc[0].stage
    contractor = df.iloc[0].subcontractor
    
    v = {
        df.iloc[0].structure_name : f"{stage} ({contractor})",
        "Pad Type" : df.iloc[0].pad_type,
        "Assigned" : df.iloc[0].assigned_crew,
        "Completion Pct" : f'{df.iloc[0].phase_completion_pct/100:.0%}',
        "Lookahead Date" : f'{df.iloc[0].next_phase_start_date: %Y-%m-%d}',
        }
    
    for _ in v:
        if not pd.isna(v[_]):
            col.markdown(f"**{_}:** {v[_]}")

def produce_file_hub(st_container, df):
    if st_container.toggle("Access work files"):
        
        aws_url = st.secrets.AWS_LONG_FORM
        trav_link = f"trav/{df.iloc[0].trav_location}"
        dxf_link = f"dxf/{df.iloc[0].dxf_location}"
        str_link = f"str/{df.iloc[0].structure_location}"
        
        st_container.caption(f'ctm/{trav_link}')
        st_container.link_button("Traverse CSV", url=f'{aws_url}{trav_link}')
        
        st_container.caption(f'ctm/{dxf_link}')
        st_container.link_button("Boonville DXF", url=f'{aws_url}{dxf_link}')
        
        st_container.caption(f'ctm/{str_link}')
        st_container.link_button("Structures CSV", url=f'{aws_url}{str_link}')
        
def create_options_column(st_container):
    # Enable floating menu
    st_container.markdown('<div class="floating">', unsafe_allow_html=True)
    
    st_container.caption("Options")
    
    st_container.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
    st_container.button(
        "Project Manager", key="button_project_mgr",
        on_click=UTILS.update_session_state, args=("page", "report")
        )

    st_container.button(
        "Logout", key="button_logout_structure", on_click=UTILS.logout
        )
    
    # Close floating container
    st.markdown('</div>', unsafe_allow_html=True)

def _work_schedule_form():
    with st.form(key='schedule_form'):
        # Various Input Types
        text_input = st.text_input("Text Input")
        date_input = st.date_input("Date Input")
        slider_input = st.slider("Slider Input", min_value=0, max_value=100, value=50)
        
        submit_button = st.form_submit_button(label='Submit')
        if submit_button:
            st.success("Entry Submitted!")
            # Process the input data as needed

def produce_structure_selection(df, st_container):
    # Select Line
    filt_df = df.loc[df.selected_filter == True]
    line_keys = [*filt_df.primary_key_line.unique()]
    st_container.selectbox(
        "line no.", key="select_line", 
        options=sorted([i for i in line_keys if i != 0])
        )
    line = st.session_state.select_line
    
    # Select Station
    station_keys = [
        *df.loc[(df.primary_key_line == line) & 
                       (df.selected_filter == True)].primary_key_sta
        ]
      
    st_container.selectbox("station no.", key="select_station", 
        options=sorted([i for i in station_keys if i != 0]),
        on_change=UTILS.reset_session_state) 
    
def produce_structure_filter(df, st_container):
    v = UTILS.create_list_of_possible_filters(df)
    filter_options = UTILS.compose_filter_options(v)
    
    st_container.multiselect("Filter options", options=filter_options, 
        key="multiselect_structure_filter", placeholder="filtering options",
        label_visibility="collapsed",
        on_change=UTILS.filter_dataframe_by_multiselect, args=(df,))
    