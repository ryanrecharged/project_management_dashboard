import app_control as CONTROL
import pandas as pd

import re
import streamlit as st
from datetime import datetime, timedelta

def apply_emojis(text):
    try:
        return CONTROL.project_stages()[text.lower()]['display_name']
    except:
        return text

def apply_structure_name(line_no, station_no):
    return f"{line_no}-{station_no}"

def apply_subcontractor(text):
    try:
        return CONTROL.project_stages()[text.lower()]['subcontractor']
    except:
        return text

def apply_team(text):
    try:
        return CONTROL.project_stages()[text.lower()]['team']
    except:
        return text

def apply_timeline_conflicts(end_date, next_start):
    if end_date >= next_start:
        return True
    else:
        return False

def callback_sessions(modified_state, value):
    st.session_state[modified_state] = st.session_state[value]
    return True

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def create_list_of_possible_filters(df: pd.DataFrame):
    print('PRINTING TIMELINE CONFLICTS')
    x = [*df.timeline_conflict.unique()]
    print(x)
    print(sorted(x, reverse=True))
    v = {
        "Sub: " : {"opts": [*df.subcontractor.unique()],
                   "column": "subcontractor"},
        "Crew: " : {"opts": [*df.assigned_crew.unique()],
                    "column": "assigned_crew"},
        "Conflicts: " : {"opts": sorted([*df.timeline_conflict.unique()], reverse=True),
                         "column": "timeline_conflict"}
        }
    return v

def create_options_column(st_container, opt_type="Project Manager"):
    st_container.caption("Options")
    
    if opt_type == "Project Manager":
        st_container.button("Project Manager", 
                            key="button_project_mgr", 
                            on_click=update_session_state, 
                            args=("page", "report")
                            )
    elif opt_type == "Structure Report":
        pass
    st_container.button("Logout", 
                        key="button_logout_structure", on_click=logout
                        )
        
def compose_filter_options(v: dict) -> list:
    filter_options = []
    for _ in v:
        for each in v[_]['opts']:
            if not pd.isna(each):
                filter_options.append(f'{_}{each}')
                    
    return filter_options

def _format_term(term):
    if term == "True":
        term = True
    elif term == "False":
        term = False
    return term

def _multiselect_loop(df: pd.DataFrame, mask=None) -> pd.DataFrame:
    for _ in st.session_state.multiselect_structure_filter:
        key = _[:_.find(":")+2]
        term = _[_.find(":")+2:]
        col = create_list_of_possible_filters(df)[key]['column']
        
        term = _format_term(term)
        condition = (df[col] == term)
        
        if mask is None:
            df.loc[condition, 'selected_filter'] = True
            mask = condition
        else:
            df['selected_filter'] = False
            df.loc[mask & condition, 'selected_filter'] = True
            
            if len(df.loc[mask & condition, 'selected_filter']) == 0:
                mask = mask | condition
            else:
                mask = mask & condition
                
            df['selected_filter'] = mask
            
    return df

def filter_dataframe_by_multiselect(df: pd.DataFrame) -> pd.DataFrame:
    
    if len(st.session_state.multiselect_structure_filter) == 0:
        df['selected_filter'] = True
    
    else:
        df['selected_filter'] = False
        df = _multiselect_loop(df)       
            
    save_edited_df(df, save_edits=False)    

def filter_dataframe_by_select_station(df: pd.DataFrame) -> pd.DataFrame:
    line = st.session_state.select_line
    station = st.session_state.select_station
    
    return df.loc[(df.primary_key_line == line) & (df.primary_key_sta == station)]

def logout():
    update_session_state("logged_in", False)
    update_session_state("page", "login")
    update_session_state("login_error", False)
    update_session_state("login_error_message", "")

def consolidate_duplicates(df):
    # Match primary key line-sta to secondary key line-sta and VV
    df.apply(lambda row: apply_matching_function(row['internal_id']))
    
    # with delete true/false column in hand,
    # df = df.[where True].drop()

    # Specify the values you want to compare
    value1 = 'A'
    value2 = 'D'

    # Specify the columns you want to exclude from the comparison
    exclude_columns = ['structure_name', 'primary_key_line', 'primary_key_sta',
                       'second_key_line', 'second_key_sta']

    # Get the columns you want to compare
    compare_columns = [col for col in df.columns if col not in exclude_columns]

    # Filter the DataFrame to get the rows with the specified values in 'col1'
    row1 = df[df['col1'] == value1]
    row2 = df[df['col1'] == value2]

    # Compare the values in the filtered rows
    are_equal = (row1[compare_columns].values == row2[compare_columns].values).all()
    if are_equal:
        pass # tag row2 for deletion --> establish tempory column
    
    # Drop all rows with deletion == True

    return df

def apply_matching_function(data_id):
    pass

def load_initial_dataframe():
    # Load data
    df = pd.read_csv(CONTROL.app_locations()['project_data'])
    df = df.drop(columns=["Unnamed: 0"])
    df['internal_id'] = df.index + 5001
    
    # Expand data to isolate 'primary_keys' only
    df2 = df.copy()
    df2.rename(columns={
        'primary_key_line': 'second_key_line', 
        'primary_key_sta' : 'second_key_sta',
        'second_key_line': 'primary_key_line',
        'second_key_sta' : 'primary_key_sta'
        }, inplace=True
        )
    
    # Refresh structure names to match new primary_keys
    df2['structure_name'] = df2.apply(
        lambda row: apply_structure_name(
            row['primary_key_line'], 
            row['primary_key_sta']), axis=1)
    
    # Do not append duplicates
    duplicates = df2['structure_name'].isin(df['structure_name'])
    uniques = df2[~duplicates]
    df = pd.concat([df, uniques], ignore_index=True)
        
    # App display formatting
    df.primary_key_line.fillna(0, inplace=True)
    df.primary_key_sta.fillna(0, inplace=True)
    df.second_key_line.fillna(0, inplace=True)
    df.second_key_sta.fillna(0, inplace=True)
    df.next_phase_start_date.fillna(pd.Timestamp('2023-12-31'), inplace=True)
    df.stage.fillna('Planning', inplace=True)
    df.phase_completion_pct.fillna(0, inplace=True)
    df.subcontractor.fillna("Burns McDonnell", inplace=True)

    # Set column types
    df['projected_end_date'] = pd.to_datetime(df['projected_end_date'], format='mixed')
    df = df.astype({'primary_key_line' : 'uint16', 'primary_key_sta' : 'uint16',
                    'second_key_line': 'uint16', 'second_key_sta': 'uint16',
                    'next_phase_start_date': 'datetime64[ns]',
                    'next_phase_end_date': 'datetime64[ns]',
                    'stage': 'string', 'ctm_notes': 'string'})
    
    # Apply emoji formatting for app display
    df['stage'] = df['stage'].apply(remove_emojis)
    df['stage'] = df['stage'].apply(apply_emojis)
    
    return df

def remove_emojis(text):
    if pd.isna(text):
        text = ""
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emoj, '', text).strip()

def reset_session_state():
    st.session_state.toggle_update_status = False
    st.session_state.toggle_assign_status = False
    st.session_state.field_notes = ""
    st.session_state.foreman_notes = ""

def save_edited_df(df, save_edits=True):
    df['stage'] = df['stage'].apply(remove_emojis)
    df['subcontractor'] = df['stage'].apply(apply_subcontractor)
    df['team'] = df['stage'].apply(apply_team)
    df['timeline_conflict'] = df.apply(
        lambda row: apply_timeline_conflicts(
            pd.Timestamp(row['projected_end_date']), 
            pd.Timestamp(row['next_phase_start_date'])), axis=1)
    df['structure_name'] = df.apply(
        lambda row: apply_structure_name(
            row['primary_key_line'], 
            row['primary_key_sta']), axis=1)
    
    if save_edits:
        for _ in st.session_state.table_editor['edited_rows']:
            df.at[_, 'field_notes'] = ""
            df.at[_, 'foreman_notes'] = ""
            df.at[_, 'assigned_crew'] = ""
            df.at[_, 'phase_completion_pct'] = 0
        df['selected_filter'] = True
        
    #TODO: Consolidate multiple lines here if all but index, structure_name match
    #df = consolidate_duplicates(df)
        
    df.to_csv(CONTROL.app_locations()['project_data'])
    print("~~~~~~~saved~~~~~~~~~")

def today_plus(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

def update_session_state(key, value):
    if key not in st.session_state:
        st.session_state[key] = value
    else:
        st.session_state[key] = value

def validate_login():
    if not st.session_state.logged_in:
        username = st.session_state['login_form_username_key']
        password = st.session_state['login_form_pass_key']

        # Add logic to validate username and password
        # Using hardcoded "admin" for demo purposes
        if username == "admin" and password == "admin":
            update_session_state("logged_in", True)
            update_session_state("page", "selection")
            update_session_state("login_error", False)
            update_session_state("login_error_message", "")
        else:
            update_session_state("logged_in", False)
            update_session_state("page", "login")
            update_session_state("login_error", True)
            update_session_state("login_error_message", "Invalid user/password")
        
        # Reset the login error message if username or password is empty  
        if username == "" or password == "":
            update_session_state("login_error", False)
            update_session_state("login_error_message", "")
        
