import app_control as CONTROL
import utils as UTILS

import altair as alt
import pandas as pd
import pygwalker as pyg
import streamlit as st
import streamlit.components.v1 as stc


from datetime import date

def gantt_chart(dframe: pd.DataFrame) -> alt.Chart:
    selection = alt.selection_point(fields=['stage'], bind='legend')
    interval = alt.selection_interval(encodings=['x'])
    
    color = alt.condition(selection,
        alt.Color('stage:N', scale=alt.Scale(
            domain=[k for k in CONTROL.project_display_names()],
            range=['#4CBB17', '#03396c', '#c6c6c6', '#c6c6c6', '#c6c6c6', 
                   '#3137fd', '#c6c6c6', '#c6c6c6', '#fff600', '#005b96', 
                   '#2c75ff'],
            )),
        alt.value('lightgrey'))
    
    base = alt.Chart(dframe).transform_fold(
        ['projected_end_date', 'next_phase_start_date', 'next_phase_end_date'],
        as_=['column', 'dates']
        ).mark_bar().encode(
        alt.X('yearmonthdate(dates):O', title=''),
        alt.Y('structure_name:O', title='', 
              sort=alt.EncodingSortField(field="index", order='ascending')),
        color=color,
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.2))
    ).properties(
        title='',
    ).add_params(
        selection
    )

    chart = base.encode(
        x=alt.X('yearmonthdate(dates):O', title='', scale=alt.Scale(domain=interval.ref()))
    ).properties()

    view = base.encode(
        y=alt.Y('structure_name:O', title='', axis=alt.Axis(labels=False))
    ).add_selection(
        interval
    ).properties(
        height=50,
    )
    
    rules = alt.Chart(pd.DataFrame({
        'Date': [pd.Timestamp('2023-12-17'), pd.Timestamp('2023-12-29')],
        'color': ['red', 'orange']
    })).mark_rule().encode(
        x='yearmonthdate(Date):O',
        color=alt.Color('color:N', scale=None)
    )

    return view & chart
    
def tableau_style(dframe: pd.DataFrame) -> str:

    return pyg.walk(dframe, env='streamlit', spec="config.json", return_html=True, use_preview=True)

def table_display(df: pd.DataFrame, stage_opts: list, crew_opts: list) -> st.data_editor:       
    return st.data_editor(
        df, column_order=(
            'primary_key_line', 'primary_key_sta', 'stage', 
            'projected_end_date', 'phase_completion_pct', 'assigned_crew', 
            'next_phase_start_date', 'ctm_notes'),
        column_config={
            "primary_key_line": st.column_config.NumberColumn(
                "Line", required=True
                ),
            "primary_key_sta": st.column_config.NumberColumn(
                "Station", required=True
                ),
            "stage": st.column_config.SelectboxColumn(
                "Stage", options=stage_opts,
                required=True
                ),
            
            "projected_end_date": st.column_config.DateColumn(
                "Completion Date",
                min_value=date(2023, 1, 1),
                max_value=date(2024, 12, 31),
                format="DD.MM.YYYY",
                step=1,
                ),
            "phase_completion_pct": st.column_config.SelectboxColumn(
                "%", options=[0, 25, 50, 75],
                required=True
                ),
            "assigned_crew": st.column_config.SelectboxColumn(
                "Crew", options=crew_opts,
                width='small', required=False
                ),
            
            "next_phase_start_date": st.column_config.DateColumn(
                "Next Phase Start",
                min_value=date(2023, 1, 1),
                max_value=date(2024, 12, 31),
                format="DD.MM.YYYY",
                step=1,
                ),
            "ctm_notes": st.column_config.TextColumn(
                "Project Notes", width='large'
                ),
        },           
        use_container_width=False, width=1200,
        num_rows="dynamic", height=500, key="table_editor",
        )

def display_options_frame(crew_opts, outage_opts, str_opts, df):    
    # Enable floating menu
    # st.markdown('<div class="floating">', unsafe_allow_html=True)
    
    st.caption("Options")
    # st.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
    st.button(
        "Structure Report", key="button_update_structure",
        on_click=UTILS.update_session_state, args=("page", "entry")
        )    
    st.checkbox(
        'Only display conflicts', key='pm_conflicts_only'
        )
    if st.toggle('Sort by...', key='pm_sort_toggle'):
        _display_sort_options()
    
    if st.toggle('Filter by...', key='pm_filter_toggle'):
        _display_filter_options(crew_opts, outage_opts)
        
    with st.expander("Assign Structure"):
        _display_assignment_expansion(crew_opts, str_opts, df)
        
    st.button("Logout", key="button_logout_report", on_click=UTILS.logout)
        
    # Close floating container
    st.markdown('</div>', unsafe_allow_html=True)

def _display_sort_options():
    st.radio(
        'label', key="pm_sort_by", options=['Stage', 'Station'],
        label_visibility='collapsed'
        )

def _display_filter_options(crew_opts, outage_opts):        
    
    f_s = st.session_state.chart_filter_selection
    
    st.radio(
        'Filter by...', options=['Crew', 'Outage No.'],
        key="chart_filter_selection", label_visibility='collapsed'
        )
    st.selectbox(
        'Filter choices', key="chart_filter_choice",
        options=crew_opts if f_s.lower() == "crew" else outage_opts,
        index=None, placeholder="Select choice",
        label_visibility="collapsed"
        )

def _display_assignment_expansion(crew_opts, str_opts, df):
    with st.form("assign_form", clear_on_submit=True, border=False):
        st.selectbox(
            "Structure", options=str_opts, index=None, 
            key = "form_set_structure",
            label_visibility="collapsed", placeholder="Choose structure"
            )
        st.selectbox(
            "Field crew", options=crew_opts, index=None, 
            key = "form_set_crew",
            label_visibility="collapsed", placeholder="Select team"
            )
        st.text_input(
            "Notes to field crew", placeholder="Provide instructions", 
            key = "form_set_notes",
            label_visibility="collapsed"
            )
        
        st.form_submit_button(
            "Assign", on_click=UTILS.save_crew_assignment, args=(df,)
            )
           
def filter_only_conflicts(df):
    if st.session_state.pm_conflicts_only:
        return df.loc[df['timeline_conflict'] == True].copy()
    else:
        return df.copy()
    
def sort_dataframe_per_selection(df):
    if st.session_state.pm_sort_toggle:
        s_val = st.session_state['pm_sort_by']
        
        df['stage_map'] = df['stage'].map(CONTROL.project_display_names()).map(CONTROL.project_stages('stage_order'))

        m = {
            'Stage' : ['stage_map', 'projected_end_date'],
            'Station' : ['primary_key_line', 'primary_key_sta'],
        }
        df.sort_values(m[s_val], inplace=True)
        
    return df

def filter_dataframe_per_selection(df):
    if st.session_state.pm_filter_toggle:
        filter_type = st.session_state.chart_filter_selection
        filter_choice = st.session_state.chart_filter_choice
        if filter_type.lower() == 'crew':
            if filter_choice == None or filter_choice == "":
                return df
            else:
                return df.loc[df['assigned_crew'] == filter_choice]
        else:
            if filter_choice == None or filter_choice == "":
                return df
            else:
                return df.loc[df['outage_no'] == filter_choice]
    return df