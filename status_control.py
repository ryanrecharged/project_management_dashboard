import app_control as CONTROL
import utils as UTILS

import pandas as pd
import streamlit as st


def work_status(df, tab1, tab2, placeholder_col):
    s = UTILS.filter_dataframe_by_select_station(df)
    placeholder_col.caption(
        "Info", 
        help="Lookahead Date refers to expected subsequent stage start date"
        )

    if s.timeline_conflict.values[0]:
        placeholder_col.error("Timeline conflict detected")
    
    _work_notes(s, placeholder_col)
    _work_status_text(s, placeholder_col)
    _work_status_toggles(tab1, tab2)
    
    if st.session_state.toggle_update_status:
        _form_work_status(s, tab1, df)
    if st.session_state.toggle_assign_status:
        _form_work_assigment(s, tab2, df)
              
def _form_work_assigment(df_row, update_col, df):
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

def _form_work_status(df_row, update_col, df):
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

def _work_notes(df, detail_col):
    if df.iloc[0].field_notes != " " and not pd.isna(df.iloc[0].field_notes):
        if not pd.isna(df.iloc[0].assigned_crew):
            detail_col.info(f"**{df.iloc[0].assigned_crew} says**: {df.iloc[0].field_notes}")
        else:
            detail_col.info(f"**Notes from the field**: {df.iloc[0].field_notes}")
    print("STATUS REPORT")
    print(df)
    print(df['foreman_notes'])
    if not pd.isna(df.iloc[0].foreman_notes) and df.iloc[0].foreman_notes != " ":
        detail_col.success(f"**Boudreau says**: {df.iloc[0].foreman_notes}")
    elif not pd.isna(df.iloc[0].ctm_notes) and df.iloc[0].ctm_notes != " ":
        detail_col.success(f"**CTM says**: {df.iloc[0].ctm_notes}")

def work_schedule(df):
    st.write("existing schedule printed here")
    st.toggle("Update schedule", key="toggle_update_schedule", value=False)
    
    if st.session_state.toggle_update_schedule:
        _work_schedule_form()
        
def _work_status_text(df_row, detail_col):
    v = {
        df_row.iloc[0].structure_name : f"{df_row.iloc[0].stage} ({df_row.iloc[0].subcontractor})",
        "Pad Type" : df_row.iloc[0].pad_type,
        "Assigned" : df_row.iloc[0].assigned_crew,
        "Completion Pct" : f'{df_row.iloc[0].phase_completion_pct/100:.0%}',
        "Lookahead Date" : f'{df_row.iloc[0].next_phase_start_date: %Y-%m-%d}',
        }
    
    for _ in v:
        if not pd.isna(v[_]):
            detail_col.markdown(f"**{_}:** {v[_]}")

def _work_status_toggles(tab1, tab2):
    line = st.session_state.select_line
    station = st.session_state.select_station

    tab1.toggle(f"Update: **{line}-{station}**", key="toggle_update_status", value=False)
    tab2.toggle(f"Assign: **{line}-{station}**", key="toggle_assign_status", value=False)   

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

def structure_function(df, st_container):
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
    
def filter_options(df, st_container):
    v = UTILS.create_list_of_possible_filters(df)
    filter_options = UTILS.compose_filter_options(v)
    
    st_container.multiselect("Filter options", options=filter_options, 
        key="multiselect_structure_filter", placeholder="filtering options",
        label_visibility="collapsed",
        on_change=UTILS.filter_dataframe_by_multiselect, args=(df,))
    