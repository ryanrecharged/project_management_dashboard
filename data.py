import pandas as pd

struct_df = pd.DataFrame({
    'primary_key_line': [12, 12, 12, 'AR'],
    'primary_key_sta': [217, 218, 219, '12-220'],
    'second_key_line': [11, 11, 11, 11],
    'second_key_sta': [151, 152, 153, 0],
    'stage' : ['', '', '', ''], # brush clearing, stakeout, timber clearing, construction, survey offsets, drilling, line crew, live wire, monitoring, as-built
    'projected_end_date' : ['', '', '', ''], # of current stage
    'pad_type' : ['', '', '', ''], # Type 1, Min Impact, Matting, Mixed Type with Matting
    'difficulty_rating' : ['', '', '', ''], #
    'subcontractor' : ['', '', '', ''], # CT Male, Supreme, Tri State, 3 Phase
    'foreman_notes' : ['', '', '', ''], # Enable notes in structure page, automatically toggle b/w foreman and field crew depending on user
    'field_notes' : ['', '', '', ''], #
    'next_phase_start_date' : ['', '', '', ''], #
    'next_phase_end_date' : ['', '', '', ''], #
})
