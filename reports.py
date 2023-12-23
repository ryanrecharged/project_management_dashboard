import app_control as CONTROL
import utils as UTILS
import user as USER

import altair as alt
import boto3
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
        x=alt.X('yearmonthdate(dates):O', title='', scale=alt.Scale(domain=interval))
    ).properties(
        width=900
    )

    view = base.encode(
        y=alt.Y('structure_name:O', title='', axis=alt.Axis(labels=False))
    ).add_params(
        interval
    ).properties(
        width=900,
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
                required=False
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
    st.caption("Options")
    st.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
    st.button(
        f"{st.session_state.report_title} Report", key="button_update_structure",
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
    
    st.markdown('<span id="button-logout"></span>', unsafe_allow_html=True)
    st.button("Logout", key="button_logout_report", on_click=UTILS.logout)

def admin_settings_display(df):
    c1, c2, c3 = st.columns(3)
    tstmp = pd.Timestamp.now().strftime("%Y-%m-%d.%H%M")
    for each in st.session_state.admin_settings_multiselect:
        print(each)

    
    with c1.expander("Project name and title: :orange[Change headings]"):
        s, t= st.tabs(['Name of Project', 'Report Title'])
        s.text_input(
            label='Name of Project', key="admin_project_name",
            placeholder="Hudson, NY: HRVA Transmission Line PNO 22.XXXX",
            label_visibility='collapsed',
            on_change=USER.set_project_name
            )
        t.text_input(
            label='Report Title', key='admin_title_name',
            placeholder='e.g. "Structure"',
            label_visibility='collapsed',
            on_change=USER.set_report_title
        )
    
    with c1.expander("Color schemes: :orange[General visual styling]"):
        x, y = st.tabs(['Primary', 'Accent'])
        
        x.color_picker(
            'Primary Color', value="#593773", key='admin_accent_color', 
            label_visibility='collapsed'
            )
        y.color_picker(
            'Accent Color', value="#b16ee6", key='admin_bkgd_color', 
            label_visibility='collapsed'
            )
        
    
    with c2.expander("Records and logs: :orange[Access the database]"):
        a, b = st.tabs(['Database', 'Change log'])
        a.download_button(
            "Download database", UTILS.convert_df(df.copy()),
            f"ctm_internal_boonville_{tstmp}.csv", "text/csv"
            )
        b.button("Print log file", key="button_print_log", disabled=True)

    with c3.expander("Workflow: :orange[Establish project structure]"):
        w1, w2 = st.tabs(['Stages', 'Milestones'])
    
        w1.selectbox(
            'Project type', 
            options=['Type 1', 'Type 2'], index=None,
            label_visibility='visible')
        w1.text_area(
            'Set project stages', 
            placeholder="Set project stages; emojis allowed; using notion for duration increments + subcontractor + team",
            label_visibility='collapsed')
        
        w2.radio(
            'Format', 
            options=['Notes + Slider', 'Checklist'],
            )

    with c2.expander("Data uploads"):
        d1, d2 = st.tabs(['File uploader', 'Second tab'])
        with d1.form('file_uploader', clear_on_submit=True, border=False):
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
                df['trav_location'] = f'pm_{ts}.csv'
                UTILS.save_database_changes(df)
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
                df['dxf_location'] = f'pm_{ts}.csv'
                UTILS.save_database_changes(df)
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
                df['structure_location'] = f'pm_{ts}.csv'
                UTILS.save_database_changes(df)
        
            st.checkbox(
                'Assign to all structure reports', 
                value=True, disabled=True
                )
            st.selectbox(
                "Structures to associate", 
                options=['All', 'Single', 'Multi'],
                index=0, label_visibility='collapsed',
                disabled=True)
        
            st.form_submit_button('Upload')


    with c1.expander("App integration: :orange[Connect to third-party apps]"):
        m, n = st.tabs(['Zapier', 'List of Zaps'])
        m.button("Connect Zapier")
        n.text_area("[List Zaps here via API query]")
        
    with c3.expander("Data alignment"):
        x, y, z, aa = st.tabs(["Sort by", "Filter by", "Field view", "Table view"])
        x.text_area("Enter list to sort by")
        y.text_area("Enter list to filter by")
        z.text_area("Enter list for field info")
        aa.text_area("Columns for Admin Table view")
    
    with c2.expander("User management"):
        t, a, b = st.tabs(['Add user', 'Remove user', 'Update user'])
        if t.toggle('Add new user to project'):
            with st.form("new_user_entry", border=False):
                st.text_input(
                    label="Username", placeholder='Username: last_name', 
                    label_visibility='collapsed')
                st.text_input(
                    label='Password', placeholder='Password: [auto-generated]', 
                    label_visibility='collapsed', disabled=True)
                st.text_input(
                    label='Email address', placeholder='Contact: 631.555.1234 or email',
                    label_visibility='collapsed')
                st.checkbox('Make administrator', key='new_user_admin')
                st.form_submit_button("Create user") 

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