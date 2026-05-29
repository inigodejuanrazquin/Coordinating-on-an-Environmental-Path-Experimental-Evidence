from os import environ

SESSION_CONFIGS = [
    # ========== BASELINE TREATMENTS (No Environmental Effects) ==========
    
    # SP First - Baseline
    {
        'name': 'baseline_sp_first_5p',
        'display_name': 'Baseline: SP→DM (5 participants - Testing)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 5,
        'baseline_treatment': True,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    {
        'name': 'baseline_sp_first_10p',
        'display_name': 'Baseline: SP→DM (10 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 10,
        'baseline_treatment': True,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    {
        'name': 'baseline_sp_first_20p',
        'display_name': 'Baseline: SP→DM (20 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 20,
        'baseline_treatment': True,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    
    # DM First - Baseline
    {
        'name': 'baseline_dm_first_5p',
        'display_name': 'Baseline: DM→SP (5 participants - Testing)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 5,
        'baseline_treatment': True,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
    {
        'name': 'baseline_dm_first_10p',
        'display_name': 'Baseline: DM→SP (10 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 10,
        'baseline_treatment': True,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
    {
        'name': 'baseline_dm_first_20p',
        'display_name': 'Baseline: DM→SP (20 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 20,
        'baseline_treatment': True,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
    
    # ========== CONTROL TREATMENTS (With Environmental Effects) ==========
    
    # SP First - Control
    {
        'name': 'control_sp_first_5p',
        'display_name': 'Control: SP→DM (5 participants - Testing)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 5,
        'baseline_treatment': False,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    {
        'name': 'control_sp_first_10p',
        'display_name': 'Control: SP→DM (10 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 10,
        'baseline_treatment': False,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    {
        'name': 'control_sp_first_20p',
        'display_name': 'Control: SP→DM (20 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 20,
        'baseline_treatment': False,
        'treatment_order': 'sp_first',
        'rounds_treatment_1': 15,  # SP rounds
        'rounds_treatment_2': 15,  # DM rounds
    },
    
    # DM First - Control
    {
        'name': 'control_dm_first_5p',
        'display_name': 'Control: DM→SP (5 participants - Testing)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 5,
        'baseline_treatment': False,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
    {
        'name': 'control_dm_first_10p',
        'display_name': 'Control: DM→SP (10 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 10,
        'baseline_treatment': False,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
    {
        'name': 'control_dm_first_20p',
        'display_name': 'Control: DM→SP (20 participants)',
        'app_sequence': ['social_planner'],
        'num_demo_participants': 20,
        'baseline_treatment': False,
        'treatment_order': 'dm_first',
        'rounds_treatment_1': 15,  # DM rounds
        'rounds_treatment_2': 15,  # SP rounds
    },
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=10.00,
    doc="",
)

PARTICIPANT_FIELDS = ['economy_id', 'dm_economy_id', 'agent_type']  # Track DM assignments from start
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'AUD'
USE_POINTS = False
DEBUG = False  # ← ADD THIS LINE

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """
<h3>Social Planner Economic Experiment - Within-Subjects Design</h3>

<div style="margin: 20px 0; padding: 20px; background: #e8f5e9; border-left: 4px solid #4caf50;">
    <h4>⚙️ How to Configure Round Numbers:</h4>
    <p><strong>IMPORTANT:</strong> You can customize the number of rounds for each treatment!</p>
    <ol>
        <li>When creating a session, click <strong>"Configure session"</strong></li>
        <li>Edit these parameters:
            <ul>
                <li><strong>rounds_treatment_1:</strong> Number of rounds for the FIRST treatment (default: 15)</li>
                <li><strong>rounds_treatment_2:</strong> Number of rounds for the SECOND treatment (default: 15)</li>
            </ul>
        </li>
        <li>Examples:
            <ul>
                <li>12 & 18 rounds → Set rounds_treatment_1=12, rounds_treatment_2=18</li>
                <li>10 & 20 rounds → Set rounds_treatment_1=10, rounds_treatment_2=20</li>
            </ul>
        </li>
    </ol>
    <p><em>Note: For "SP→DM" sessions, treatment 1 = SP and treatment 2 = DM. For "DM→SP" sessions, treatment 1 = DM and treatment 2 = SP.</em></p>
</div>

<h4>📊 Session Options:</h4>

<div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #2196f3;">
    <h5>🧪 Testing Options (Small Groups):</h5>
    <ul>
        <li><strong>5 participants:</strong> Test one complete DM economy (5 agents)</li>
    </ul>
</div>

<div style="margin: 20px 0; padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800;">
    <h5>🔬 Experiment Options:</h5>
    <ul>
        <li><strong>10 participants:</strong> 
            <ul>
                <li>SP treatment: 10 separate individual economies</li>
                <li>DM treatment: 2 economies of 5 agents each</li>
            </ul>
        </li>
        <li><strong>20 participants:</strong>
            <ul>
                <li>SP treatment: 20 separate individual economies</li>
                <li>DM treatment: 4 economies of 5 agents each</li>
            </ul>
        </li>
    </ul>
</div>

<p><strong>Note:</strong> Each participant experiences BOTH treatments. For SP→DM orders, participants will see an instructions buffer page (3-minute minimum) before entering the DM phase together.</p>
"""


# Room configuration for fixed participant links
ROOMS = [
    dict(
        name='experiment_room',
        display_name='Social Planner Experiment Room',
        participant_label_file='_rooms/participant_labels.txt',
    ),
]


SECRET_KEY = '9867293834'
INSTALLED_APPS = ['otree']