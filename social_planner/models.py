from otree.api import *
import random
import math

doc = """Social Planner Economic Experiment - Within-Subjects Design"""

class C(BaseConstants):
    NAME_IN_URL = 'social_planner'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 30
    NUM_PRACTICE_ROUNDS = 2
    
    # Preference parameters
    BETA = 0.93
    ETA = 0.5
    
    # Capital depreciation
    DELTA = 0.10
    GREEN_DELTA = 0.10
    
    # Production function
    TFP = 3.5417
    ALPHA = 0.33
    UPSILON = 0.22
    
    # Emissions
    S = 1.0
    M = 3  
    # this means k_3 produces 3x as much emissions as k_1
    RHO = 1.0
    SIGMA = 0.0
    
    # Climate dynamics
    XI = 0.0035
    ZETA = 0.05
    
    # Damage function (Nordhaus DICE)
    PI_1 = 0.0000
    PI_2 = 0.05

 

    # --- 1. Define Steady State Values for BOTH Treatments ---
    # Control Treatment (with environmental impacts)
    SS_BROWN_CONTROL = 9.2461
    SS_GREEN_CONTROL = 8.8294
    SS_TEMP_CONTROL  = 2.5597

    # Baseline Treatment (NO environmental impacts, PI_1=PI_2=0)
    SS_BROWN_BASELINE = 55.598
    SS_GREEN_BASELINE = 37.066
    SS_TEMP_BASELINE  = 14.27 

    # --- 2. Define Percentage Deviations BELOW Steady State ---
    # High Capital Condition (closer to SS)
    HIGH_DEV_BROWN_PCT = 0.05  # 5% below SS for k3
    HIGH_DEV_GREEN_PCT = 0.10  # 10% below SS for k1

    # Low Capital Condition (further from SS)
    LOW_DEV_BROWN_PCT = 0.40  # 40% below SS for k3
    LOW_DEV_GREEN_PCT = 0.50  # 50% below SS for k1

    # --- 3. Calculate the 8 Initial Capital Scenarios ---

    # CONTROL Treatment Initial Values
    INITIAL_BROWN_HIGH_CONTROL = SS_BROWN_CONTROL * (1 - HIGH_DEV_BROWN_PCT)
    INITIAL_GREEN_HIGH_CONTROL = SS_GREEN_CONTROL * (1 - HIGH_DEV_GREEN_PCT)
    INITIAL_BROWN_LOW_CONTROL  = SS_BROWN_CONTROL * (1 - LOW_DEV_BROWN_PCT)
    INITIAL_GREEN_LOW_CONTROL  = SS_GREEN_CONTROL * (1 - LOW_DEV_GREEN_PCT)

    # BASELINE Treatment Initial Values
    INITIAL_BROWN_HIGH_BASELINE = SS_BROWN_BASELINE * (1 - HIGH_DEV_BROWN_PCT)
    INITIAL_GREEN_HIGH_BASELINE = SS_GREEN_BASELINE * (1 - HIGH_DEV_GREEN_PCT)
    INITIAL_BROWN_LOW_BASELINE  = SS_BROWN_BASELINE * (1 - LOW_DEV_BROWN_PCT)
    INITIAL_GREEN_LOW_BASELINE  = SS_GREEN_BASELINE * (1 - LOW_DEV_GREEN_PCT)

    # --- 4. Define Initial Temperature (Same for all) ---
    INITIAL_TEMPERATURE = 1.5 
   
    # Costs
    GREEN_CAPITAL_COST = 1.00
    
    # Game parameters
    UTILITY_TO_MONEY = 1.0
    MARKET_DURATION = 240
    INSTRUCTIONS_BUFFER_SECONDS = 180
    
    # Heterogeneous agents (DM treatment) - per agent values
    AGENT_PRODUCTIVITY = [2.4, 2.0, 1.6, 1.2, 0.8]
    # For CONTROL treatment
    AGENT_EXCHANGE_RATES = [1.80, 1.95, 2.15, 2.50, 3.00] 
    # For BASELINE treatment
    AGENT_EXCHANGE_RATES_BASELINE = [1.05, 1.15, 1.30, 1.50, 1.80]  
    
    # SP exchange rate for CONTROL treatment
    SP_EXCHANGE_RATE_CONTROL = 0.85
    # SP exchange rate for BASELINE treatment
    SP_EXCHANGE_RATE_BASELINE = 0.65  






def creating_session(subsession):
    """Initialize or reset treatment at the start of each treatment phase"""
    
    config = subsession.session.config
    rounds_t1 = config.get('rounds_treatment_1', 15)
    rounds_t2 = config.get('rounds_treatment_2', 15)
    
    subsession.session.vars['rounds_treatment_1'] = rounds_t1
    subsession.session.vars['rounds_treatment_2'] = rounds_t2
    subsession.session.vars['total_rounds'] = rounds_t1 + rounds_t2
    
    
    # ROUND 1 ONLY: Assign participant-level metadata
    
    if subsession.round_number == 1:
        participants = subsession.session.get_participants()
        
        # Store session-level settings
        for p in participants:
            p.vars['is_baseline'] = config.get('baseline_treatment', True)
            p.vars['treatment_order'] = config.get('treatment_order', 'dm_first')
        
        # Assign capital levels and DM economies
        num_participants = len(participants)
        num_economies = (num_participants + 4) // 5
        
        economy_capital_levels = [True] * (num_economies // 2) + [False] * (num_economies - num_economies // 2)
        random.shuffle(economy_capital_levels)
        
        random.shuffle(participants)
        
        dm_economy_counter = 0
        for i in range(0, len(participants), 5):
            economy_group = participants[i:i+5]
            economy_is_high_capital = economy_capital_levels[dm_economy_counter] if dm_economy_counter < len(economy_capital_levels) else True
            
            for idx, participant in enumerate(economy_group):
                # Capital level assignment
                participant.vars['is_high_capital'] = economy_is_high_capital
                
                # DM economy and agent assignment
                participant.vars['dm_economy_id'] = dm_economy_counter + 1
                agent_index = idx % 5
                participant.vars['agent_type'] = agent_index
                participant.vars['productivity'] = C.AGENT_PRODUCTIVITY[agent_index]
                
                
                participant.vars['exchange_rate'] = C.AGENT_EXCHANGE_RATES[agent_index]
             
                             
            
            dm_economy_counter += 1
    

   
    is_first_treatment = (subsession.round_number <= rounds_t1)
    
    _setup_treatment_grouping(subsession, is_first_treatment)
    
    
  
    if subsession.round_number == 1:
        for player in subsession.get_players():
            
            player.economy_id = player.participant.vars.get('dm_economy_id', 0)
            
            is_high = player.participant.vars.get('is_high_capital', False)
            player.capital_level = 'H' if is_high else 'L'
    
    

def _setup_treatment_grouping(subsession, is_first_treatment):
    """Set up groups WITHOUT initializing capital"""
    
    config = subsession.session.config
    rounds_t1 = subsession.session.vars.get('rounds_treatment_1', 15)
    treatment_order = config.get('treatment_order', 'dm_first')
    
    if is_first_treatment:
        is_market = (treatment_order == 'dm_first')
    else:
        is_market = (treatment_order == 'sp_first')
    
    
    if is_market:
        players = subsession.get_players()
        
        economy_groups = {}
        for player in players:
            dm_eco_id = player.participant.vars.get('dm_economy_id', 1)
            if dm_eco_id not in economy_groups:
                economy_groups[dm_eco_id] = []
            economy_groups[dm_eco_id].append(player)
        
        group_matrix = [economy_groups[eco_id] for eco_id in sorted(economy_groups.keys())]
        subsession.set_group_matrix(group_matrix)
        
        for group in subsession.get_groups():
            for player in group.get_players():
                player.participant.vars['economy_id'] = group.id_in_subsession
    else:
        players = subsession.get_players()
        group_matrix = [[player] for player in players]
        subsession.set_group_matrix(group_matrix)
        
        for player in subsession.get_players():
            player.participant.vars['economy_id'] = player.group.id_in_subsession




class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    def get_brown_capital(self):
        """For DM: sum within group. For SP: just the player's capital"""
        return sum(p.participant.vars.get('brown_capital', 0) for p in self.get_players())
    
    def get_green_capital(self):
        """For DM: sum within group. For SP: just the player's capital"""
        return sum(p.participant.vars.get('green_capital', 0) for p in self.get_players())
    
    def get_temperature(self):
        """Temperature is shared within an economy (group)"""
        return self.get_players()[0].participant.vars.get('temperature', C.INITIAL_TEMPERATURE)
    
    def is_baseline_treatment(self):
        return self.session.config.get('baseline_treatment', True)
    
    
    def calculate_output(self):
        """Calculate aggregate output for the group"""
        brown_capital = self.get_brown_capital()
        green_capital = self.get_green_capital()
        temperature = self.get_temperature()
                
        if self.is_baseline_treatment():
            omega = 1.0
        else:
            omega = 1.0 / (1.0 + C.PI_1 * temperature + C.PI_2 * temperature**2)
                
        output = C.TFP * omega * (green_capital ** C.UPSILON) * (brown_capital ** C.ALPHA)
        
     
        
        return max(output, 0.0)


    
    def calculate_individual_output(self, player):
        """Calculate individual agent's output"""
        brown_capital = player.participant.vars.get('brown_capital', 0)
        green_capital = player.participant.vars.get('green_capital', 0)
        temperature = self.get_temperature()
        productivity = player.participant.vars.get('productivity', 1.0)
                
        if self.is_baseline_treatment():
            omega = 1.0
        else:
            omega = 1.0 / (1.0 + C.PI_1 * temperature + C.PI_2 * temperature**2)
                
        output = productivity * omega * (green_capital ** C.UPSILON) * (brown_capital ** C.ALPHA)
        
        
        return max(output, 0.0)
    
    
    
    
    
    def calculate_emissions(self):
        """Calculate emissions for the economy
        Formula: e_t = s × (Θ_t + m × k_t)
        where Θ_t = k_1 (cleaner capital), k_t = k_3 (dirtier capital), m = 3
        """
        k_3 = self.get_brown_capital()  
        k_1 = self.get_green_capital()
        
        emissions = C.S * (k_1 + C.M * k_3)
        return max(emissions, 0.0)

    
    def process_trade(self, buyer, seller, max_quantity, price, capital_type):
        """Process a trade between two agents in the market"""
        capital_key = f'{capital_type}_capital'
        seller_inventory = seller.participant.vars.get(capital_key, 0)
        buyer_budget = buyer.participant.vars.get('available_output', 0)
        
        if price <= 0:
            return 0
        
        max_affordable_q = buyer_budget / price
        actual_trade_q = min(max_quantity, seller_inventory, max_affordable_q)
        
        if actual_trade_q > 0:
            total_cost = actual_trade_q * price
            seller.participant.vars[capital_key] -= actual_trade_q
            buyer.participant.vars[capital_key] += actual_trade_q
            seller.participant.vars['available_output'] += total_cost
            buyer.participant.vars['available_output'] -= total_cost
            return actual_trade_q
        
        return 0
    
    
    
    def update_end_of_period_state(self):
        """Update temperature for the entire economy at end of period"""
        current_temp = self.get_temperature()
        
        
        total_brown_capital_start = sum(p.capital_brown_start for p in self.get_players())
        total_green_capital_start = sum(p.capital_green_start for p in self.get_players())
        
        emissions = C.S * (total_green_capital_start + C.M * total_brown_capital_start)
        emissions = max(emissions, 0.0)

        # Temperature dynamics
        temp_change = C.XI * emissions - C.ZETA * current_temp
        new_temperature = current_temp + temp_change
        
        for p in self.get_players():
            p.participant.vars['temperature'] = new_temperature
            p.period_emissions = emissions
            p.period_temperature_end = new_temperature






class Player(BasePlayer):
    consumption = models.FloatField(
    min=0.0, 
    label="Consumption"
    )
    brown_investment = models.FloatField(
    min=0.0, 
    label="New investment in \(k_3\): Type-3 capital"
)
    green_investment = models.FloatField(
    min=0.0, 
    label="New investment in \(k_1\): Type-1 capital"
)

    individual_consumption = models.FloatField(
    min=0.0, 
    initial=0.0, 
    label="Consumption"
)
    individual_brown_investment = models.FloatField(
    min=0.0, 
    initial=0.0, 
    label="New investment in \(k_3\): Type-3 capital"
)
    individual_green_investment = models.FloatField(
    min=0.0, 
    initial=0.0, 
    label="New investment in \(k_1\): Type-1 capital"
)
    
    brown_capital_bid_price = models.FloatField(blank=True, min=0)
    brown_capital_bid_quantity = models.FloatField(blank=True, min=0)
    brown_capital_ask_price = models.FloatField(blank=True, min=0)
    brown_capital_ask_quantity = models.FloatField(blank=True, min=0)
    
    green_capital_bid_price = models.FloatField(blank=True, min=0)
    green_capital_bid_quantity = models.FloatField(blank=True, min=0)
    green_capital_ask_price = models.FloatField(blank=True, min=0)
    green_capital_ask_quantity = models.FloatField(blank=True, min=0)
    
    period_utility = models.FloatField(initial=0.0)
    cumulative_utility = models.FloatField(initial=0.0)
    period_output = models.FloatField(initial=0.0)
    period_initial_output = models.FloatField(initial=0.0)
    period_emissions = models.FloatField(initial=0.0)
    period_temperature = models.FloatField(initial=0.0)
    
    period_temperature_end = models.FloatField(initial=0.0)
    
    
    
    period_omega = models.FloatField(initial=1.0)  
    period_tfp = models.FloatField(initial=0.0)  
    period_exchange_rate = models.FloatField(initial=1.0)  
    
    treatment = models.StringField()
    is_high_capital = models.BooleanField()
    is_baseline = models.BooleanField()
    
    economy_id = models.IntegerField(initial=0)  
    capital_level = models.StringField(initial='')
    
    brown_market_results = models.LongStringField(initial='{}')
    green_market_results = models.LongStringField(initial='{}')
    
   
    # For practice round visualization
    practice_brown_market_results = models.LongStringField(initial='{}')
    practice_green_market_results = models.LongStringField(initial='{}')
    
    
    trades_made = models.LongStringField(initial='[]')
    
    # Clean capital tracking fields
    capital_brown_start = models.FloatField(initial=0.0)
    capital_green_start = models.FloatField(initial=0.0)
    capital_brown_end = models.FloatField(initial=0.0)
    capital_green_end = models.FloatField(initial=0.0)
    
    # For DM market tracking  
    capital_brown_pre_trade = models.FloatField(initial=0.0)
    capital_green_pre_trade = models.FloatField(initial=0.0)
    capital_brown_post_trade = models.FloatField(initial=0.0)
    capital_green_post_trade = models.FloatField(initial=0.0)
    
    
    

    # --- Survey Fields ---
    survey_q1_expectation = models.StringField(
        label="Q1) When the 1st Economy (Social Planner) ended, did you expect the economy to last more or less than it did?",
        choices=[
            'I expected the economy to go on for more rounds.',
            'I expected the economy to go on for less rounds.',
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_q1_how_many = models.IntegerField(
        label="How many rounds more or less?",
        min=0,
        blank=True
    )
    survey_q2_expectation = models.StringField(
        label="Q2) When the 2nd Economy (Decentralized Market - with trading) ended, did you expect the economy to last more or less than it did?",
        choices=[
            'I expected the economy to go on for more rounds.',
            'I expected the economy to go on for less rounds.',
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_q2_how_many = models.IntegerField(
        label="How many rounds more or less?",
        min=0,
        blank=True
    )
    survey_q3_thought = models.IntegerField(
        label="Q3) On a scale of 1 to 7, how much thought did you put into the choices you made in the experiment today, where 1 means no thought at all, and 7 indicates a great deal of thought?",
        choices=[
            [1, '1 - no thought at all'],
            [2, '2'],
            [3, '3'],
            [4, '4'],
            [5, '5'],
            [6, '6'],
            [7, '7 - a great deal of thought'],
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_q4_effort = models.IntegerField(
        label="Q4) On a scale of 1 to 7, how much effort did you put into the choices you made in the experiment today, where 1 means no effort at all, and 7 indicates a great deal of effort?",
        choices=[
            [1, '1 - no effort at all'],
            [2, '2'],
            [3, '3'],
            [4, '4'],
            [5, '5'],
            [6, '6'],
            [7, '7 - a great deal of effort'],
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_q5_earnings_effort = models.IntegerField(
        label="Q5) On a scale of 1 to 7, how much do you think your earnings for participating in today’s experiment would have increased if you put a great deal of effort and thought into the choices you made compared to no effort or thought at all, where 1 means your payoffs would have been the same no matter how little or much effort and thought you put into your choices, and 7 means you believe your earnings would have been a lot greater had you put a lot of effort and thought into your decisions?",
        choices=[
            [1, '1 - my earnings would have been the same regardless of effort/thought'],
            [2, '2'],
            [3, '3'],
            [4, '4'],
            [5, '5'],
            [6, '6'],
            [7, '7 - my earnings would have been a lot greater had I put a lot of effort/thought'],
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_q6_strategy = models.LongStringField(
        label="Q6) Did you follow a particular strategy when making the decisions? Did you change this strategy anytime during the experiment? And if so, when and why?",
        blank=True
    )

    # --- Demographics ---
    survey_demo_gender = models.StringField(
        label="1) With what gender do you identify most with?",
        choices=[
            'Male',
            'Female',
            'Non-binary',
            'Other',
            'Prefer not to answer'
        ],
        widget=widgets.RadioSelect,
        blank=True
    )
    survey_demo_birth_country = models.StringField(
        label="2) What is your country of birth?",
        blank=True
    )
    survey_demo_degree = models.StringField(
        label="4) What degree/program are you currently enrolled in at university? (i.e., degree and major, undergrad, postgrad, masters...)",
        blank=True
    )
    survey_demo_year = models.StringField(
        label="5) In what year of your degree are you currently?",
        choices=[
            'First',
            'Second',
            'Third',
            'Fourth',
            'Fifth or more'
        ],
        widget=widgets.RadioSelect,
        blank=True
    )

    
    
    
    def is_market_treatment(self):
        """
        Dynamically determine if current round is a market treatment.
        """
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        treatment_order = self.participant.vars.get('treatment_order', 'dm_first')
        
        # First treatment (rounds 1 to rounds_t1)
        if self.round_number <= rounds_t1:
            is_market = (treatment_order == 'dm_first')
        # Second treatment (rounds rounds_t1+1 onwards)
        else:
            is_market = (treatment_order == 'sp_first')
        
        return is_market
    
    def get_period_in_treatment(self):
        """Get the period number within the current treatment (1-indexed)"""
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        if self.round_number <= rounds_t1:
            return self.round_number  
        else:
            return self.round_number - rounds_t1  
    
    def get_treatment_start_round(self):
        """Get the round number where current treatment started"""
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        if self.round_number <= rounds_t1:
            return 1  
        else:
            return rounds_t1 + 1 
    
    def get_game_name(self):
        """Get 'Game 1' or 'Game 2' based on which treatment we're in"""
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        return "Game 1" if self.round_number <= rounds_t1 else "Game 2"
    
    
    


    def calculate_utility(self, consumption_amount):
        """
        Calculate utility in DOLLAR UNITS.
        Formula: u($) = ExchangeRate × sqrt(consumption)
        
        For SP: ExchangeRate = 1.0 (Control) or 0.65 (Baseline)
        For DM: ExchangeRate varies by agent
        """
        if consumption_amount <= 0:
            return 0.0
        
        is_market = self.is_market_treatment()
        is_baseline = self.participant.vars.get('is_baseline', True)
        
        # Get exchange rate based on treatment and agent type
        if is_market:
            # DM treatment: use agent-specific exchange rate (treatment-dependent)
            agent_type = self.participant.vars.get('agent_type', 0)
            if is_baseline:
                exchange_rate = C.AGENT_EXCHANGE_RATES_BASELINE[agent_type]
            else:
                exchange_rate = C.AGENT_EXCHANGE_RATES[agent_type]
        else:
            # SP treatment: use treatment-dependent exchange rate
            if is_baseline:
                exchange_rate = C.SP_EXCHANGE_RATE_BASELINE
            else:
                exchange_rate = C.SP_EXCHANGE_RATE_CONTROL
        

        utility_dollars = exchange_rate * math.sqrt(consumption_amount)
        
        
        return utility_dollars
    
    
    
    
    
    
    def process_individual_decisions(self):
        is_market = self.is_market_treatment()
        
        # Store period info
        self.period_temperature = self.participant.vars.get('temp_pre_decision', 0)
        self.period_initial_output = self.participant.vars.get('output_before_trading', 0)
        self.period_output = self.participant.vars.get('output_pre_decision', 0)
        
        # Calculate utility
        if is_market:
            self.period_utility = self.calculate_utility(self.individual_consumption)
            current_brown = self.capital_brown_start  
            current_green = self.capital_green_start  
        else:
            self.period_utility = self.calculate_utility(self.consumption)
            current_brown = self.capital_brown_start  
            current_green = self.capital_green_start  
        
        
        
        # Depreciation (applied to PRE-TRADE capital)
        depreciated_brown = (1 - C.DELTA) * current_brown
        depreciated_green = (1 - C.GREEN_DELTA) * current_green

        
        # For DM: add trading changes (POST-TRADE - PRE-TRADE)
        if is_market:
            post_trade_brown = self.capital_brown_post_trade
            post_trade_green = self.capital_green_post_trade
            trading_change_brown = post_trade_brown - current_brown
            trading_change_green = post_trade_green - current_green
        else:
            trading_change_brown = 0
            trading_change_green = 0
        
        # Investments
        brown_inv = self.individual_brown_investment if is_market else self.brown_investment
        green_inv = self.individual_green_investment if is_market else self.green_investment
        
        # New capital: k(t+1) = k(t)×(1-δ) + Δk(trading) + i(t)
        new_brown = depreciated_brown + trading_change_brown + brown_inv
        new_green = depreciated_green + trading_change_green + green_inv
        
        
     
        self.capital_brown_end = max(new_brown, 0)
        self.capital_green_end = max(new_green, 0)
        
  
        self.participant.vars['brown_capital'] = max(new_brown, 0)
        self.participant.vars['green_capital'] = max(new_green, 0)
        
        # Cumulative utility
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        treatment_start_round = self.get_treatment_start_round()
        periods_in_treatment = self.get_period_in_treatment()
        
        if self.round_number == treatment_start_round:
            self.cumulative_utility = self.period_utility  
        else:
            prev_player = self.in_round(self.round_number - 1)
            self.cumulative_utility = prev_player.cumulative_utility + self.period_utility  
        
    
    
    
    

    def get_final_payment(self):
        """
        Calculate total payment from BOTH treatment phases.
        Since utility is already in dollars, just sum and add show-up fee.
        """
        rounds_t1 = self.session.vars.get('rounds_treatment_1', 15)
        rounds_t2 = self.session.vars.get('rounds_treatment_2', 15)
        
        # Get cumulative utilities (already in dollars) from both treatments
        first_treatment_utility = self.in_round(rounds_t1).cumulative_utility
        second_treatment_utility = self.in_round(rounds_t1 + rounds_t2).cumulative_utility
        
        # Total performance payment (utilities are already in dollars)
        performance_payment = first_treatment_utility + second_treatment_utility
        
        # Add show-up fee
        show_up_fee = self.session.config.get('participation_fee', 10.00)
        total_payment = performance_payment + show_up_fee
        
        
        return total_payment