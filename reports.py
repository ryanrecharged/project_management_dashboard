
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
    
    chart = alt.Chart(dframe).transform_fold(
        ['projected_end_date', 'next_phase_start_date', 'next_phase_end_date'],
        as_=['column', 'dates']
        ).mark_bar().encode(
        x='yearmonthdate(dates):O',
        y='structure_name:O',
        color=alt.Color('stage:N'),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).properties(
        title='',
    ).add_params(
        selection
    )
    
    return chart
    
def tableau_style(dframe: pd.DataFrame) -> str:

    return pyg.walk(dframe, env='streamlit', spec="config.json", return_html=True, use_preview=True)

def table_display(df: pd.DataFrame, stage_opts: list) -> st.data_editor:
    
    return st.data_editor(
        df, column_order=(
            'primary_key_line', 'primary_key_sta', 'stage', 
            'projected_end_date', 'next_phase_start_date',
            'next_phase_end_date', 'ctm_notes'),
        column_config={
            "primary_key_line": st.column_config.NumberColumn(
                "Line", required=True
                ),
            "primary_key_sta": st.column_config.NumberColumn(
                "Station", required=True
                ),
            "stage": st.column_config.SelectboxColumn(
                "Stage", options=stage_opts,
                width='medium', required=True
                ),
            
            "projected_end_date": st.column_config.DateColumn(
                "Projected Completion",
                min_value=date(2023, 1, 1),
                max_value=date(2023, 12, 12),
                format="DD.MM.YYYY",
                step=1,
                ),
            "next_phase_start_date": st.column_config.DateColumn(
                "Next Phase Start",
                min_value=date(2023, 1, 1),
                max_value=date(2023, 12, 12),
                format="DD.MM.YYYY",
                step=1,
                ),
            "next_phase_end_date": st.column_config.DateColumn(
                "Next Phase End",
                min_value=date(2023, 1, 1),
                max_value=date(2023, 12, 12),
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

def display_report_column_options(st_column_containter, df):
    st_column_containter.caption("Options")
    st_column_containter.button("Structure Report", key="button_update_structure", 
                    on_click=UTILS.update_session_state, args=("page", "entry"))
    
    st_column_containter.checkbox('Only display conflicts', key='pm_conflicts_only')
    
    sort_tog = st_column_containter.toggle(
        'Sort by...', key='pm_sort_toggle')
    if sort_tog:
        st_column_containter.radio('label', key="pm_sort_by",
            options=['Stage', 'Station', 'Next Start'],
            label_visibility='collapsed')
        
    filt_tog = st_column_containter.toggle(
        'Filter by...', key='pm_fliter_toggle', disabled=True)
    if filt_tog:
        st_column_containter.radio('Filter by...', options=['Stage', 'Subcontractor', 'Crew'],
                          label_visibility='collapsed')
        st_column_containter.selectbox('Filter by Stage', 
            options=[v['display_name'] for (k,v) in CONTROL.project_stages().items()],
            label_visibility="collapsed")
    
    st_column_containter.button("Logout", key="button_logout_report", on_click=UTILS.logout)

def display_report_column_tabs(tabs_list, df):
    
    with tabs_list[1]: # Gantt chart
        st.altair_chart(gantt_chart(df), use_container_width=True)
        
    # with tabs_list[2]: # Tableau-style
    #     stc.html(tableau_style(df), scrolling=True, height=920)
        
    with tabs_list[0]: # Table
        opts = [v['display_name'] for (k,v) in CONTROL.project_stages().items()]
        edf = table_display(df, opts)
        st.button("Save Changes", on_click=UTILS.save_edited_df, args=(edf,))
    
    with tabs_list[2]: # Admin
        buttons, days_per = st.columns(2)
        tstmp = pd.Timestamp.now().strftime("%Y-%m-%d.%H%M")
        
        # Column 1

        buttons.download_button("Download CSV", UTILS.convert_df(df),
                           f"ctm_internal_boonville_{tstmp}.csv",
                           "text/csv")
        buttons.button("Print transaction log", key="button_print_log", disabled=True)
        buttons.button("Add user", key="button_add_user", disabled=True) 