from otree.api import *
from .models import C, Group, Player
import json
import numpy as np



def initialize_capital_if_needed(player: Player):
    """Initialize capital for a player if not already done for this treatment"""
    treatment_start_round = player.get_treatment_start_round()
    capital_init_key = f'capital_initialized_round_{treatment_start_round}'
    
    if player.participant.vars.get(capital_init_key, False):
        return  # Already initialized
    
    is_market = player.is_market_treatment()
    is_high_capital = player.participant.vars.get('is_high_capital', False)
    

    is_baseline = player.participant.vars.get('is_baseline', True)



    if is_baseline:
        if is_high_capital:
            initial_brown = C.INITIAL_BROWN_HIGH_BASELINE
            initial_green = C.INITIAL_GREEN_HIGH_BASELINE
        else: # Low capital
            initial_brown = C.INITIAL_BROWN_LOW_BASELINE
            initial_green = C.INITIAL_GREEN_LOW_BASELINE
    else: # Control treatment
        if is_high_capital:
            initial_brown = C.INITIAL_BROWN_HIGH_CONTROL
            initial_green = C.INITIAL_GREEN_HIGH_CONTROL
        else: # Low capital
            initial_brown = C.INITIAL_BROWN_LOW_CONTROL
            initial_green = C.INITIAL_GREEN_LOW_CONTROL

    # Set participant vars based on market type
    if is_market:
        player.participant.vars['brown_capital'] = initial_brown / 5
        player.participant.vars['green_capital'] = initial_green / 5
    else: # Social Planner
        player.participant.vars['brown_capital'] = initial_brown
        player.participant.vars['green_capital'] = initial_green

    
    player.participant.vars['temperature'] = C.INITIAL_TEMPERATURE
    player.participant.vars['available_output'] = 0
    player.participant.vars[capital_init_key] = True
    


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1
            
    @staticmethod
    def vars_for_template(player: Player):
        is_market = player.is_market_treatment()
        
        period_in_treatment = player.get_period_in_treatment()
        game_name = player.get_game_name()
        
        graph_data = {}
        
        c_vals = np.linspace(0.1, 20, 100)
        u_vals = np.sqrt(c_vals)
        graph_data['utility'] = {'c': list(c_vals), 'u': list(u_vals)}
        
        k_grid, th_grid = np.meshgrid(np.linspace(0.1, 25, 30), np.linspace(0.1, 15, 30))
        y_grid = C.TFP * (th_grid ** C.UPSILON) * (k_grid ** C.ALPHA)
        e_grid = (C.S * (k_grid ** C.RHO)) / (th_grid ** C.SIGMA) if C.SIGMA > 0 else C.S * (k_grid ** C.RHO)
        graph_data['production'] = {'k': [list(row) for row in k_grid], 'th': [list(row) for row in th_grid], 'y': [list(row) for row in y_grid]}
        graph_data['emissions_surface'] = {'k': [list(row) for row in k_grid], 'th': [list(row) for row in th_grid], 'e': [list(row) for row in e_grid]}
        
        e_vals = np.linspace(0, 5, 100)
        temp_change_vals = C.XI * e_vals
        graph_data['temp_change'] = {'e': list(e_vals), 'dt': list(temp_change_vals)}
        
        t_vals = np.linspace(0, 30, 100)
        omega_vals = 1 / (1 + C.PI_1 * t_vals + C.PI_2 * (t_vals**2))
        graph_data['damage'] = {'t': list(t_vals), 'omega': list(omega_vals)}
        
        if is_market:
            agent_index = player.participant.vars.get('agent_type', 0)
            agent_tfp = C.AGENT_PRODUCTIVITY[agent_index]
        else:
            agent_tfp = C.TFP
        
        constants_for_js = {
            'ETA': C.ETA, 'TFP': agent_tfp, 'UPSILON': C.UPSILON, 'ALPHA': C.ALPHA,
            'S': C.S, 'RHO': C.RHO, 'SIGMA': C.SIGMA, 'XI': C.XI, 'ZETA': C.ZETA,
            'PI_1': C.PI_1, 'PI_2': C.PI_2,
        }
        
        
        
        is_baseline = player.participant.vars.get('is_baseline', True)
        if is_market:
            agent_index = player.participant.vars.get('agent_type', 0)
            payoff_rate = C.AGENT_EXCHANGE_RATES_BASELINE[agent_index] if is_baseline else C.AGENT_EXCHANGE_RATES[agent_index]
        else:
            payoff_rate = C.SP_EXCHANGE_RATE_BASELINE if is_baseline else C.SP_EXCHANGE_RATE_CONTROL

        
        
        return {
            'round_number': player.round_number,  
            'period_in_treatment': period_in_treatment,  
            'game_name': game_name,  
            'is_market_treatment': is_market,
            'is_baseline': player.participant.vars.get('is_baseline', True),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1 if is_market else 0,
            'productivity': player.participant.vars.get('productivity', 1.0) if is_market else C.TFP,
            'graph_data': json.dumps(graph_data),
            'C_js': json.dumps(constants_for_js),
            'initial_temperature': C.INITIAL_TEMPERATURE,
            'payoff_conversion_rate': round(payoff_rate, 2),
            'example_earnings': round(payoff_rate * 4, 2)
        }







class PracticeMarket(Page):
    """Practice round for DM treatment - learn the market mechanism"""
    form_model = 'player'
    form_fields = ['brown_capital_bid_price', 'brown_capital_bid_quantity',
                   'brown_capital_ask_price', 'brown_capital_ask_quantity',
                   'green_capital_bid_price', 'green_capital_bid_quantity',
                   'green_capital_ask_price', 'green_capital_ask_quantity']
    
    @staticmethod
    def is_displayed(player: Player):
        # Only show when entering DM treatment
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        treatment_order = player.participant.vars.get('treatment_order', 'dm_first')
        
        # Show at start of DM treatment
        if treatment_order == 'dm_first':
            return player.round_number == 1
        else:  # sp_first
            return player.round_number == rounds_t1 + 1
    
    @staticmethod
    def vars_for_template(player: Player):
        initialize_capital_if_needed(player)
        
        is_market = player.is_market_treatment()
        group = player.group
        
        if is_market:
            production_output = group.calculate_individual_output(player)
        else:
            production_output = group.calculate_output()
        
       
        player.participant.vars['available_output'] = production_output
        
        brown_k = player.participant.vars.get('brown_capital', 0)
        green_k = player.participant.vars.get('green_capital', 0)
        
        return {
            'brown_capital': round(brown_k, 2),
            'green_capital': round(green_k, 2),
            'type3_capital_display': round(brown_k, 2),  
            'type1_capital_display': round(green_k, 2),  
            'current_output': round(production_output, 2),
            'temperature': round(group.get_temperature(), 2),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1,
            'productivity': player.participant.vars.get('productivity', 1.0),
            'is_baseline': group.is_baseline_treatment(),
        }






class PracticeMarketWait(WaitPage):
    """Wait for all agents to submit practice orders"""
    body_text = "Waiting for other participants to complete the practice round..."

    @staticmethod
    def is_displayed(player: Player):
        return PracticeMarket.is_displayed(player)






    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()

        for capital_type in ['brown', 'green']:
            for p in players:
                p.participant.vars[f'practice_{capital_type}_trades'] = []

            bids_raw = [{'player': p, 'price': p.field_maybe_none(f'{capital_type}_capital_bid_price'), 'quantity': p.field_maybe_none(f'{capital_type}_capital_bid_quantity')} for p in players]
            asks_raw = [{'player': p, 'price': p.field_maybe_none(f'{capital_type}_capital_ask_price'), 'quantity': p.field_maybe_none(f'{capital_type}_capital_ask_quantity')} for p in players]

            bids = [b for b in bids_raw if b['price'] is not None and b['quantity'] is not None and b['price'] > 0 and b['quantity'] > 0]
            asks = [a for a in asks_raw if a['price'] is not None and a['quantity'] is not None and a['price'] > 0 and a['quantity'] > 0]

            results = {'avg_price': 0, 'total_volume': 0}

            if not bids or not asks:
                for p in players:
                    setattr(p, f'practice_{capital_type}_market_results', json.dumps(results))
                continue

            bids.sort(key=lambda x: x['price'], reverse=True)
            asks.sort(key=lambda x: x['price'])

            if bids[0]['price'] < asks[0]['price']:
                for p in players:
                    setattr(p, f'practice_{capital_type}_market_results', json.dumps(results))
                continue

          
            potential_prices = sorted(list(set([b['price'] for b in bids] + [a['price'] for a in asks])))
            
            max_volume = -1  
            clearing_price = 0

            for price in potential_prices:
                q_demand = sum(b['quantity'] for b in bids if b['price'] >= price)
                q_supply = sum(a['quantity'] for a in asks if a['price'] <= price)
                traded_volume = min(q_demand, q_supply)

                if traded_volume > max_volume:
                    max_volume = traded_volume
                    clearing_price = price
                elif traded_volume == max_volume and max_volume >= 0: 
                    clearing_price = (clearing_price + price) / 2.0
            
            equilibrium_price = clearing_price if max_volume > 0 else 0
           

            if equilibrium_price == 0:
                results = {'avg_price': 0, 'total_volume': 0}
                for p in players:
                    setattr(p, f'practice_{capital_type}_market_results', json.dumps(results))
                continue

           
            eligible_buyers = [b for b in bids if b['price'] >= equilibrium_price]
            eligible_sellers = [a for a in asks if a['price'] <= equilibrium_price]

            total_volume = 0
            iterations = 0
            max_iterations = 100

            while eligible_buyers and eligible_sellers and iterations < max_iterations:
                iterations += 1
                buyer = eligible_buyers[0]
                seller = eligible_sellers[0]

                if buyer['player'] == seller['player']:
                    if len(eligible_sellers) > 1:
                        eligible_sellers.pop(0)
                        continue
                    else:
                        break

                trade_qty = min(buyer['quantity'], seller['quantity'])
                
                if trade_qty > 0:
                    total_volume += trade_qty
                    trade_info = {'quantity': trade_qty, 'price': equilibrium_price, 'capital_type': capital_type}

                   
                    buyer['player'].participant.vars[f'practice_{capital_type}_trades'].append({**trade_info, 'type': 'buy'})
                    seller['player'].participant.vars[f'practice_{capital_type}_trades'].append({**trade_info, 'type': 'sell'})

                    buyer['quantity'] -= trade_qty
                    seller['quantity'] -= trade_qty

                if buyer['quantity'] < 0.001:
                    eligible_buyers.pop(0)
                if seller['quantity'] < 0.001:
                    eligible_sellers.pop(0)
            

            results = {'avg_price': equilibrium_price, 'total_volume': total_volume}
            for p in players:
                setattr(p, f'practice_{capital_type}_market_results', json.dumps(results))
                
                




class PracticeResults(Page):
    """Show supply/demand curves with player's position highlighted"""

    @staticmethod
    def is_displayed(player: Player):
        return PracticeMarket.is_displayed(player)


    @staticmethod
    def vars_for_template(player: Player):
        players = player.group.get_players()
        
        practice_brown_results = json.loads(getattr(player, 'practice_brown_market_results', '{}'))
        practice_green_results = json.loads(getattr(player, 'practice_green_market_results', '{}'))

        def build_market_data_for_graph(capital_type, equilibrium_price):
            bids = []
            asks = []
            for p in players:
                bid_price = p.field_maybe_none(f'{capital_type}_capital_bid_price')
                bid_qty = p.field_maybe_none(f'{capital_type}_capital_bid_quantity')
                ask_price = p.field_maybe_none(f'{capital_type}_capital_ask_price')
                ask_qty = p.field_maybe_none(f'{capital_type}_capital_ask_quantity')
                if bid_price and bid_qty and bid_price > 0 and bid_qty > 0:
                    bids.append({'price': bid_price, 'quantity': bid_qty, 'is_player': p == player})
                if ask_price and ask_qty and ask_price > 0 and ask_qty > 0:
                    asks.append({'price': ask_price, 'quantity': ask_qty, 'is_player': p == player})
            bids.sort(key=lambda x: x['price'], reverse=True)
            asks.sort(key=lambda x: x['price'])
            return {
                'demand': bids,
                'supply': asks,
                'equilibrium': equilibrium_price
            }

        brown_data = build_market_data_for_graph('brown', practice_brown_results.get('avg_price', 0))
        green_data = build_market_data_for_graph('green', practice_green_results.get('avg_price', 0))

        
        # Calculate simulated trades for the current player from participant.vars
        brown_trades = player.participant.vars.get('practice_brown_trades', [])
        green_trades = player.participant.vars.get('practice_green_trades', [])

        brown_bought = sum(t['quantity'] for t in brown_trades if t.get('type') == 'buy')
        brown_sold = sum(t['quantity'] for t in brown_trades if t.get('type') == 'sell')

        green_bought = sum(t['quantity'] for t in green_trades if t.get('type') == 'buy')
        green_sold = sum(t['quantity'] for t in green_trades if t.get('type') == 'sell')
     

        return {
            'brown_market_data': brown_data,
            'green_market_data': green_data,
            'brown_price': round(brown_data['equilibrium'], 2),
            'green_price': round(green_data['equilibrium'], 2),
            'player_brown_bid': player.field_maybe_none('brown_capital_bid_price') or 0,
            'player_brown_ask': player.field_maybe_none('brown_capital_ask_price') or 0,
            'player_green_bid': player.field_maybe_none('green_capital_bid_price') or 0,
            'player_green_ask': player.field_maybe_none('green_capital_ask_price') or 0,
            'brown_bought': round(brown_bought, 2),
            'brown_sold': round(brown_sold, 2),
            'green_bought': round(green_bought, 2),
            'green_sold': round(green_sold, 2),
        }





class TreatmentTransition(Page):
    """Show between treatments to inform participants"""
        
    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        return player.round_number == rounds_t1 + 1
        
    # In class TreatmentTransition(Page):

    @staticmethod
    def vars_for_template(player: Player):
        treatment_order = player.participant.vars['treatment_order']
        first_was_dm = (treatment_order == 'dm_first')
        

        going_to_dm = not first_was_dm # True if the NEXT treatment is DM
 

        # Calculate payment from first treatment
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        first_treatment_player = player.in_round(rounds_t1)
        first_utility = first_treatment_player.cumulative_utility
        

        first_payment = first_utility
        
        # Prepare variables for the UPCOMING (second) treatment
        is_high_capital = player.participant.vars.get('is_high_capital', False)
        is_baseline = player.participant.vars.get('is_baseline', True)
        
        
        

        if going_to_dm:
            # Transitioning to Decentralized Market
            agent_index = player.participant.vars.get('agent_type', 0)
            new_productivity = C.AGENT_PRODUCTIVITY[agent_index]
            new_payoff_rate = C.AGENT_EXCHANGE_RATES_BASELINE[agent_index] if is_baseline else C.AGENT_EXCHANGE_RATES[agent_index]

            # Select initial capital based on baseline/control AND high/low for DM
            if is_baseline:
                if is_high_capital:
                    new_brown_k_total = C.INITIAL_BROWN_HIGH_BASELINE
                    new_green_k_total = C.INITIAL_GREEN_HIGH_BASELINE
                else: # Low capital
                    new_brown_k_total = C.INITIAL_BROWN_LOW_BASELINE
                    new_green_k_total = C.INITIAL_GREEN_LOW_BASELINE
            else: # Control
                if is_high_capital:
                    new_brown_k_total = C.INITIAL_BROWN_HIGH_CONTROL
                    new_green_k_total = C.INITIAL_GREEN_HIGH_CONTROL
                else: # Low capital
                    new_brown_k_total = C.INITIAL_BROWN_LOW_CONTROL
                    new_green_k_total = C.INITIAL_GREEN_LOW_CONTROL
            
    
            new_brown_k = new_brown_k_total / 5
            new_green_k = new_green_k_total / 5

        else:
            # Transitioning to Social Planner
            new_productivity = C.TFP
            new_payoff_rate = C.SP_EXCHANGE_RATE_BASELINE if is_baseline else C.SP_EXCHANGE_RATE_CONTROL

            # Select initial capital based on baseline/control AND high/low for SP
            if is_baseline:
                if is_high_capital:
                    new_brown_k = C.INITIAL_BROWN_HIGH_BASELINE
                    new_green_k = C.INITIAL_GREEN_HIGH_BASELINE
                else: # Low capital
                    new_brown_k = C.INITIAL_BROWN_LOW_BASELINE
                    new_green_k = C.INITIAL_GREEN_LOW_BASELINE
            else: # Control
                if is_high_capital:
                    new_brown_k = C.INITIAL_BROWN_HIGH_CONTROL
                    new_green_k = C.INITIAL_GREEN_HIGH_CONTROL
                else: # Low capital
                    new_brown_k = C.INITIAL_BROWN_LOW_CONTROL
                    new_green_k = C.INITIAL_GREEN_LOW_CONTROL
       
        
        
        
        
        return {
            'first_treatment': 'Decentralized Market' if first_was_dm else 'Social Planner',
            'second_treatment': 'Social Planner' if first_was_dm else 'Decentralized Market',
            'first_utility': round(first_utility, 2),
            'first_payment': round(first_payment, 2),
            'is_baseline': player.participant.vars.get('is_baseline', True),
            'is_high_capital': is_high_capital,
            'new_productivity': round(new_productivity, 4),
            'new_payoff_rate': round(new_payoff_rate, 2),
            'new_brown_capital': round(new_brown_k, 2),
            'new_green_capital': round(new_green_k, 2),
            'new_type3_capital_display': round(new_brown_k, 2),  
            'new_type1_capital_display': round(new_green_k, 2),  
            'initial_temperature': C.INITIAL_TEMPERATURE,
        }


class InstructionsBuffer(Page):
    """
    Buffer page shown to participants transitioning from SP to DM.
    Forces 3-minute wait to ensure all participants can sync before DM starts.
    """
    
    @staticmethod
    def is_displayed(player: Player):
        # Only show at start of second treatment (after SP phase)
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        treatment_order = player.participant.vars.get('treatment_order', 'dm_first')
        
        # Show only when transitioning from SP to DM (i.e., sp_first order at round rounds_t1+1)
        return (player.round_number == rounds_t1 + 1 and treatment_order == 'sp_first')
    
    @staticmethod
    def vars_for_template(player: Player):
        # Show DM instructions with agent-specific info
        graph_data = {}
        
        c_vals = np.linspace(0.1, 20, 100)
        u_vals = np.sqrt(c_vals)
        graph_data['utility'] = {'c': list(c_vals), 'u': list(u_vals)}
        
        k_grid, th_grid = np.meshgrid(np.linspace(0.1, 25, 30), np.linspace(0.1, 15, 30))
        y_grid = C.TFP * (th_grid ** C.UPSILON) * (k_grid ** C.ALPHA)
        e_grid = (C.S * (k_grid ** C.RHO)) / (th_grid ** C.SIGMA) if C.SIGMA > 0 else C.S * (k_grid ** C.RHO)
        graph_data['production'] = {'k': [list(row) for row in k_grid], 'th': [list(row) for row in th_grid], 'y': [list(row) for row in y_grid]}
        graph_data['emissions_surface'] = {'k': [list(row) for row in k_grid], 'th': [list(row) for row in th_grid], 'e': [list(row) for row in e_grid]}
        
        e_vals = np.linspace(0, 5, 100)
        temp_change_vals = C.XI * e_vals
        graph_data['temp_change'] = {'e': list(e_vals), 'dt': list(temp_change_vals)}
        
        t_vals = np.linspace(0, 30, 100)
        omega_vals = 1 / (1 + C.PI_1 * t_vals + C.PI_2 * (t_vals**2))
        graph_data['damage'] = {'t': list(t_vals), 'omega': list(omega_vals)}
        
        constants_for_js = {
            'ETA': C.ETA, 'TFP': C.TFP, 'UPSILON': C.UPSILON, 'ALPHA': C.ALPHA,
            'S': C.S, 'RHO': C.RHO, 'SIGMA': C.SIGMA, 'XI': C.XI, 'ZETA': C.ZETA,
            'PI_1': C.PI_1, 'PI_2': C.PI_2,
        }
        
        return {
            'is_market_treatment': True,  
            'is_baseline': player.participant.vars.get('is_baseline', True),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1,
            'productivity': player.participant.vars.get('productivity', 1.0),
            'graph_data': json.dumps(graph_data),
            'C_js': json.dumps(constants_for_js),
            'min_wait_seconds': C.INSTRUCTIONS_BUFFER_SECONDS,
            'dm_economy_id': player.participant.vars.get('dm_economy_id', 1),
            'payoff_conversion_rate': round(
                C.AGENT_EXCHANGE_RATES_BASELINE[player.participant.vars.get('agent_type', 0)] if player.participant.vars.get('is_baseline', True) 
                else C.AGENT_EXCHANGE_RATES[player.participant.vars.get('agent_type', 0)], 2)
        }


class BufferWaitPage(WaitPage):
    """Wait for all participants to finish reading DM instructions"""
    body_text = "Waiting for all participants to finish reading the instructions..."
    
    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        treatment_order = player.participant.vars.get('treatment_order', 'dm_first')
        return (player.round_number == rounds_t1 + 1 and treatment_order == 'sp_first')
    
    
    

class ProductionPhase(Page):
    @staticmethod
    def vars_for_template(player: Player):
        initialize_capital_if_needed(player)
        
        is_market = player.is_market_treatment()
        group = player.group
      
    
        
          
       

        current_brown_k = player.participant.vars.get('brown_capital', 0)
        current_green_k = player.participant.vars.get('green_capital', 0)
        current_temp = group.get_temperature()
        
        

        if is_market:
            production_output = group.calculate_individual_output(player)
        else:
            production_output = group.calculate_output()
        
        
        
        
        player.participant.vars['available_output'] = production_output
        player.participant.vars['output_before_trading'] = production_output
        
        

        temperature = current_temp
        if group.is_baseline_treatment():
            omega = 1.0
        else:
            omega = 1.0 / (1.0 + C.PI_1 * temperature + C.PI_2 * temperature**2)
        
        if is_market:
            tfp = player.participant.vars.get('productivity', 1.0)
            agent_type = player.participant.vars.get('agent_type', 0)
            exr = C.AGENT_EXCHANGE_RATES_BASELINE[agent_type] if group.is_baseline_treatment() else C.AGENT_EXCHANGE_RATES[agent_type]
        else:
            tfp = C.TFP
            exr = C.SP_EXCHANGE_RATE_BASELINE if group.is_baseline_treatment() else C.SP_EXCHANGE_RATE_CONTROL
        
        player.period_omega = omega
        player.period_tfp = tfp
        player.period_exchange_rate = exr
        

        
        
        
        # Get treatment-relative period and range
        period_in_treatment = player.get_period_in_treatment()
        treatment_start_round = player.get_treatment_start_round()
        
        # Build historical data - ONLY from current treatment
        historical_data = []
        # Loop through ALL rounds completed *in this treatment* UP TO AND INCLUDING the current round
        for r in range(treatment_start_round, player.round_number + 1):
            p_in_r = player.in_round(r)
            period_num = r - treatment_start_round + 1
            is_current_round = (r == player.round_number)

            # --- Determine capital values ---
            if is_current_round:
                # Current round: Production just happened
                brown_k_pre = current_brown_k
                brown_k_post = current_brown_k
                green_k_pre = current_green_k
                green_k_post = current_green_k
                output_initial, output_adjusted = production_output, None
            else:
                # Past rounds: Fetch stored data
                if is_market:
                    brown_k_pre, brown_k_post = p_in_r.capital_brown_pre_trade, p_in_r.capital_brown_post_trade
                    green_k_pre, green_k_post = p_in_r.capital_green_pre_trade, p_in_r.capital_green_post_trade
                else:
                    brown_k_pre, brown_k_post = p_in_r.capital_brown_pre_trade, p_in_r.capital_brown_pre_trade
                    green_k_pre, green_k_post = p_in_r.capital_green_pre_trade, p_in_r.capital_green_pre_trade
                output_initial = p_in_r.period_initial_output
                output_adjusted = p_in_r.period_output

            # --- Determine START temperature for round 'r' ---
            if r == treatment_start_round:
                period_temp_start = C.INITIAL_TEMPERATURE
            else:
                # For subsequent rounds 'r', use the END temperature from round 'r-1'
                
                prev_p_in_r = player.in_round(r - 1)
                period_temp_start = prev_p_in_r.period_temperature_end # T_r = T_{r-1}_end

            # --- Fetch consumption and utility for past rounds ---
            cons = None if is_current_round else (p_in_r.individual_consumption if is_market else p_in_r.consumption)
            utility = None if is_current_round else p_in_r.period_utility

            # --- Append data for round 'r' ---
            historical_data.append({
                'period': period_num,
                'brown_capital_pre': brown_k_pre,
                'brown_capital_post': brown_k_post,
                'green_capital_pre': green_k_pre,
                'green_capital_post': green_k_post,
                'temperature': period_temp_start, 
                'consumption': cons,
                'utility': utility,
                'output_initial': output_initial,
                'output_adjusted': output_adjusted 
            })

        
        
        prev_results = {}
        if period_in_treatment > 1:
            prev_player = player.in_round(player.round_number - 1)
            if is_market:
                prev_results['consumption'] = round(prev_player.individual_consumption, 2)
                prev_results['brown_investment'] = round(prev_player.individual_brown_investment, 2)
                prev_results['green_investment'] = round(prev_player.individual_green_investment, 2)
            else:
                prev_results['consumption'] = round(prev_player.consumption, 2)
                prev_results['brown_investment'] = round(prev_player.brown_investment, 2)
                prev_results['green_investment'] = round(prev_player.green_investment, 2)
            prev_results['period_utility'] = round(prev_player.period_utility, 2)
            prev_results['cumulative_utility'] = round(prev_player.cumulative_utility, 2)
        
        return {
            'round_number': player.round_number,  
            'period_number': period_in_treatment,  
            'previous_period_number': period_in_treatment - 1,
            'game_name': player.get_game_name(),
            'is_market': is_market, 
            'is_baseline': group.is_baseline_treatment(),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1,
            'brown_capital': round(current_brown_k, 2), 
            'green_capital': round(current_green_k, 2),
            'type3_capital_display': round(current_brown_k, 2),  
            'type1_capital_display': round(current_green_k, 2), 
            'temperature': round(current_temp, 2),
            'individual_output': round(production_output, 2),
            'total_output': round(group.calculate_output(), 2),
            'current_emissions': round(group.calculate_emissions(), 2),
            'historical_data': json.dumps(historical_data), 
            'prev_results': prev_results
        }
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):    
        pass  






class MarketWaitPage(WaitPage):
    body_text = "Waiting for other agents to proceed to the market..."
        
    @staticmethod
    def is_displayed(player: Player):
        return player.is_market_treatment()

class CombinedCapitalMarket(Page):
    form_model = 'player'
    form_fields = ['brown_capital_bid_price', 'brown_capital_bid_quantity', 'brown_capital_ask_price', 'brown_capital_ask_quantity',
                   'green_capital_bid_price', 'green_capital_bid_quantity', 'green_capital_ask_price', 'green_capital_ask_quantity']
    timeout_seconds = 240
        
    @staticmethod
    def is_displayed(player: Player):
        return player.is_market_treatment()
        
    @staticmethod
    def vars_for_template(player: Player):
        is_market = player.is_market_treatment()
        group = player.group
        
        current_output = player.participant.vars.get('available_output', 0)
        temperature = group.get_temperature()
        
        player.participant.vars['temp_pre_decision'] = temperature
        player.participant.vars['output_pre_decision'] = current_output
                
        period_in_treatment = player.get_period_in_treatment()
        treatment_start_round = player.get_treatment_start_round()
               
        historical_data = []
        for r in range(treatment_start_round, player.round_number + 1):
            p_in_r = player.in_round(r)
            period_num = r - treatment_start_round + 1
            is_current_round = (r == player.round_number)
            
            if is_current_round:
                brown_k_pre = player.participant.vars.get('pre_market_brown_k', player.participant.vars.get('brown_capital', 0))
                green_k_pre = player.participant.vars.get('pre_market_green_k', player.participant.vars.get('green_capital', 0))
                brown_k_post = player.participant.vars.get('brown_capital', 0)
                green_k_post = player.participant.vars.get('green_capital', 0)
                temp = temperature
                output_initial = player.participant.vars.get('output_before_trading', current_output)
                trading_delta = current_output - output_initial
            else:
                brown_k_pre, green_k_pre = p_in_r.capital_brown_pre_trade, p_in_r.capital_green_pre_trade
                brown_k_post, green_k_post = p_in_r.capital_brown_post_trade, p_in_r.capital_green_post_trade
                temp = p_in_r.period_temperature
                output_initial = p_in_r.period_initial_output
                trading_delta = p_in_r.period_output - p_in_r.period_initial_output
                
                
                
            
            cons = None if is_current_round else (p_in_r.individual_consumption if is_market else p_in_r.consumption)
            utility = None if is_current_round else p_in_r.period_utility
            historical_data.append({
                'period': period_num, 
                'brown_k_pre': brown_k_pre, 
                'brown_k_post': brown_k_post, 
                'green_k_pre': green_k_pre, 
                'green_k_post': green_k_post, 
                'temperature': temp,
                'consumption': cons, 
                'utility': utility, 
                'output_initial': output_initial, 
                'trading_delta': trading_delta
            })
        
        return {
    'round_number': player.round_number,
    'period_number': period_in_treatment,
    'game_name': player.get_game_name(),
    'is_market': is_market, 
    'is_baseline': group.is_baseline_treatment(),
    'current_output': round(current_output, 2),  
    'brown_capital': round(player.participant.vars.get('brown_capital', 0), 2),
    'green_capital': round(player.participant.vars.get('green_capital', 0), 2),
    'type3_capital_display': round(player.participant.vars.get('brown_capital', 0), 2),  
    'type1_capital_display': round(player.participant.vars.get('green_capital', 0), 2),  
    'temperature': round(temperature, 2),  
    'green_capital_cost': C.GREEN_CAPITAL_COST,
    'agent_type': player.participant.vars.get('agent_type', 0) + 1 if is_market else 0,
    'historical_data': json.dumps(historical_data),
    'brown_depreciation_pct': round(C.DELTA * 100, 1), 
    'brown_survival_pct': round((1 - C.DELTA) * 100, 1), 
    'brown_survival_rate': round(1 - C.DELTA, 2),
    'green_depreciation_pct': round(C.GREEN_DELTA * 100, 1), 
    'green_survival_pct': round((1 - C.GREEN_DELTA) * 100, 1), 
    'green_survival_rate': round(1 - C.GREEN_DELTA, 2),
    'productivity': player.participant.vars.get('productivity', 1.0) if is_market else C.TFP
}


   
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        """Store pre-market values before entering wait page"""
        player.participant.vars['pre_market_brown_k'] = player.participant.vars.get('brown_capital', 0)
        player.participant.vars['pre_market_green_k'] = player.participant.vars.get('green_capital', 0)
        player.participant.vars['pre_market_output'] = player.participant.vars.get('available_output', 0)
        





class AfterMarketWait(WaitPage):
    body_text = "The capital markets are now closed. Clearing trades..."
        
    @staticmethod
    def is_displayed(player: Player):
        return player.is_market_treatment()
        
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()

        for capital_type in ['brown', 'green']:
            for p in players:
                p.participant.vars[f'{capital_type}_market_trades'] = []

            bids_raw = [{'player': p, 'price': p.field_maybe_none(f'{capital_type}_capital_bid_price'), 'quantity': p.field_maybe_none(f'{capital_type}_capital_bid_quantity')} for p in players]
            asks_raw = [{'player': p, 'price': p.field_maybe_none(f'{capital_type}_capital_ask_price'), 'quantity': p.field_maybe_none(f'{capital_type}_capital_ask_quantity')} for p in players]

            bids = [b for b in bids_raw if b['price'] is not None and b['quantity'] is not None and b['price'] > 0 and b['quantity'] > 0]
            asks = [a for a in asks_raw if a['price'] is not None and a['quantity'] is not None and a['price'] > 0 and a['quantity'] > 0]

            results = {'avg_price': 0, 'total_volume': 0}

            if not bids or not asks:
                for p in players:
                    setattr(p, f'{capital_type}_market_results', json.dumps(results))
                continue

            bids.sort(key=lambda x: x['price'], reverse=True)
            asks.sort(key=lambda x: x['price'])

            if bids[0]['price'] < asks[0]['price']:
                for p in players:
                    setattr(p, f'{capital_type}_market_results', json.dumps(results))
                continue
            
            potential_prices = sorted(list(set([b['price'] for b in bids] + [a['price'] for a in asks])))
            
            max_volume = -1 
            clearing_price = 0

            for price in potential_prices:
                q_demand = sum(b['quantity'] for b in bids if b['price'] >= price)
                q_supply = sum(a['quantity'] for a in asks if a['price'] <= price)
                traded_volume = min(q_demand, q_supply)

                if traded_volume > max_volume:
                    max_volume = traded_volume
                    clearing_price = price
                elif traded_volume == max_volume and max_volume >= 0:
                    clearing_price = (clearing_price + price) / 2.0
            
            equilibrium_price = clearing_price if max_volume > 0 else 0           

            if equilibrium_price == 0:
                results = {'avg_price': 0, 'total_volume': 0}
                for p in players:
                    setattr(p, f'{capital_type}_market_results', json.dumps(results))
                continue

            
            eligible_buyers = [b for b in bids if b['price'] >= equilibrium_price]
            eligible_sellers = [a for a in asks if a['price'] <= equilibrium_price]

            total_volume = 0
            iterations = 0
            max_iterations = 100

            while eligible_buyers and eligible_sellers and iterations < max_iterations:
                iterations += 1
                buyer = eligible_buyers[0]
                seller = eligible_sellers[0]

                if buyer['player'] == seller['player']:
                    if len(eligible_sellers) > 1:
                        eligible_sellers.pop(0)
                        continue
                    else:
                        break

                trade_qty = min(buyer['quantity'], seller['quantity'])
                
                if trade_qty > 0:
                    
                    actual_trade_q = group.process_trade(buyer['player'], seller['player'], trade_qty, equilibrium_price, capital_type)
                    

                    if actual_trade_q > 0:
                        total_volume += actual_trade_q
                        trade_info = {'quantity': actual_trade_q, 'price': equilibrium_price, 'capital_type': capital_type}

                        buyer['player'].participant.vars[f'{capital_type}_market_trades'].append({**trade_info, 'type': 'buy'})
                        seller['player'].participant.vars[f'{capital_type}_market_trades'].append({**trade_info, 'type': 'sell'})

                        buyer['quantity'] -= actual_trade_q
                        seller['quantity'] -= actual_trade_q
                    else:
                        
                        eligible_buyers.pop(0) 

                if buyer['quantity'] < 0.001:
                    eligible_buyers.pop(0)
                if seller['quantity'] < 0.001:
                    eligible_sellers.pop(0)
            

            results = {'avg_price': equilibrium_price, 'total_volume': total_volume}
            for p in players:
                setattr(p, f'{capital_type}_market_results', json.dumps(results))
        
        for p in players:
            all_trades_for_player = p.participant.vars.get('brown_market_trades', []) + p.participant.vars.get('green_market_trades', [])
            p.trades_made = json.dumps(all_trades_for_player)
            
            

class MarketResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.is_market_treatment()
        
    @staticmethod
    def vars_for_template(player: Player):
        brown_results = json.loads(player.brown_market_results)
        green_results = json.loads(player.green_market_results)
        brown_trades = player.participant.vars.get('brown_market_trades', [])
        green_trades = player.participant.vars.get('green_market_trades', [])
                
        brown_bought = sum(t['quantity'] for t in brown_trades if t.get('type') == 'buy')
        brown_sold = sum(t['quantity'] for t in brown_trades if t.get('type') == 'sell')
        green_bought = sum(t['quantity'] for t in green_trades if t.get('type') == 'buy')
        green_sold = sum(t['quantity'] for t in green_trades if t.get('type') == 'sell')
                
        return {
            'round_number': player.round_number,
            'period_number': player.get_period_in_treatment(),  
            'is_market': True,
            'is_baseline': player.group.is_baseline_treatment(),
            'current_output': round(player.participant.vars.get('available_output', 0), 2),
            'brown_capital': round(player.participant.vars.get('brown_capital', 0), 2),
            'green_capital': round(player.participant.vars.get('green_capital', 0), 2),
            'temperature': round(player.group.get_temperature(), 2),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1,
            'brown_avg_price': round(brown_results.get('avg_price', 0), 2),
            'brown_total_volume': round(brown_results.get('total_volume', 0), 2),
            'brown_bought': round(brown_bought, 2),
            'brown_sold': round(brown_sold, 2),
            'green_avg_price': round(green_results.get('avg_price', 0), 2),
            'green_total_volume': round(green_results.get('total_volume', 0), 2),
            'green_bought': round(green_bought, 2),
            'green_sold': round(green_sold, 2),
            'pre_brown_k': round(player.participant.vars.get('pre_market_brown_k', 0), 2),
            'post_brown_k': round(player.participant.vars.get('brown_capital', 0), 2),
            'pre_green_k': round(player.participant.vars.get('pre_market_green_k', 0), 2),
            'post_green_k': round(player.participant.vars.get('green_capital', 0), 2),
            'pre_output': round(player.participant.vars.get('pre_market_output', 0), 2),
            'post_output': round(player.participant.vars.get('available_output', 0), 2),
            'change_output': round(player.participant.vars.get('available_output', 0) - player.participant.vars.get('pre_market_output', 0), 2),
        }
    
    
    
    

class PeriodDecision(Page):
    form_model = 'player'
    
    @staticmethod
    def get_form_fields(player: Player):
        return ['individual_consumption', 'individual_brown_investment', 'individual_green_investment'] if player.is_market_treatment() else ['consumption', 'brown_investment', 'green_investment']
    
    
    
    

    @staticmethod
    def vars_for_template(player: Player):
        initialize_capital_if_needed(player)
        is_market = player.is_market_treatment()
        group = player.group
        current_brown_k = player.participant.vars.get('brown_capital', 0) 
        current_green_k = player.participant.vars.get('green_capital', 0) 
        current_temp = group.get_temperature() 
        if is_market:
            player.capital_brown_start = player.participant.vars.get('pre_market_brown_k', current_brown_k)
            player.capital_green_start = player.participant.vars.get('pre_market_green_k', current_green_k)
        else:
            player.capital_brown_start = current_brown_k
            player.capital_green_start = current_green_k
        production_output = player.participant.vars.get('available_output', 0) 
        
        initial_output_this_period = player.participant.vars.get('output_before_trading', production_output) 
        if 'temp_pre_decision' not in player.participant.vars:
            player.participant.vars['temp_pre_decision'] = current_temp
        if 'output_pre_decision' not in player.participant.vars:
            player.participant.vars['output_pre_decision'] = production_output
        period_in_treatment = player.get_period_in_treatment()
        treatment_start_round = player.get_treatment_start_round()
        

        
        historical_data = []
        for r in range(treatment_start_round, player.round_number + 1):
            p_in_r = player.in_round(r)
            period_num = r - treatment_start_round + 1
            is_current_round = (r == player.round_number)

            
            if is_current_round:
                if is_market:
                    brown_k_pre = player.participant.vars.get('pre_market_brown_k', current_brown_k)
                    green_k_pre = player.participant.vars.get('pre_market_green_k', current_green_k)
                    brown_k_post = current_brown_k
                    green_k_post = current_green_k
                else:
                    brown_k_pre, brown_k_post = current_brown_k, current_brown_k
                    green_k_pre, green_k_post = current_green_k, current_green_k
                
                output_for_graph = initial_output_this_period
            else: 
                if is_market:
                    brown_k_pre, brown_k_post = p_in_r.capital_brown_pre_trade, p_in_r.capital_brown_post_trade
                    green_k_pre, green_k_post = p_in_r.capital_green_pre_trade, p_in_r.capital_green_post_trade
                else:
                    brown_k_pre, brown_k_post = p_in_r.capital_brown_pre_trade, p_in_r.capital_brown_pre_trade
                    green_k_pre, green_k_post = p_in_r.capital_green_pre_trade, p_in_r.capital_green_pre_trade
                
                output_for_graph = p_in_r.period_initial_output 

            
            if r == treatment_start_round:
                period_temp_start = C.INITIAL_TEMPERATURE
            else:
                prev_p_in_r = player.in_round(r - 1)
                period_temp_start = prev_p_in_r.period_temperature_end

            
            cons = None if is_current_round else (p_in_r.individual_consumption if is_market else p_in_r.consumption)
            utility = None if is_current_round else p_in_r.period_utility

            
            historical_data.append({
                'period': period_num,
                'brown_capital_pre': brown_k_pre,
                'brown_capital_post': brown_k_post,
                'green_capital_pre': green_k_pre,
                'green_capital_post': green_k_post,
                'temperature': period_temp_start,
                'consumption': cons,
                'utility': utility,
                'output_initial': output_for_graph, 
            })

        
        return {
            'round_number': player.round_number,
            'period_number': period_in_treatment,
            'game_name': player.get_game_name(),
            'is_market': is_market,
            'is_baseline': group.is_baseline_treatment(),
            'current_output': round(production_output, 2),
            'brown_capital': round(current_brown_k, 2),
            'green_capital': round(current_green_k, 2),
            'type3_capital_display': round(current_brown_k, 2),
            'type1_capital_display': round(current_green_k, 2),
            'temperature': round(current_temp, 2),
            'green_capital_cost': C.GREEN_CAPITAL_COST,
            'type1_capital_display_cost': C.GREEN_CAPITAL_COST,
            'agent_type': player.participant.vars.get('agent_type', 0) + 1 if is_market else 0,
            'historical_data': json.dumps(historical_data),
            'brown_depreciation_pct': round(C.DELTA * 100, 1),
            'brown_survival_pct': round((1 - C.DELTA) * 100, 1),
            'brown_survival_rate': round(1 - C.DELTA, 2),
            'green_depreciation_pct': round(C.GREEN_DELTA * 100, 1),
            'green_survival_pct': round((1 - C.GREEN_DELTA) * 100, 1),
            'green_survival_rate': round(1 - C.GREEN_DELTA, 2),
            'productivity': player.participant.vars.get('productivity', 1.0) if is_market else C.TFP
        }
    
    
    
    
    
    
    @staticmethod
    def error_message(player: Player, values):
        available_output = player.participant.vars.get('available_output', 0)
        if player.is_market_treatment():
            c, i_b, i_g = values['individual_consumption'], values['individual_brown_investment'], values['individual_green_investment']
        else:
            c, i_b, i_g = values['consumption'], values['brown_investment'], values['green_investment']
        
        if any(v is None for v in [c, i_b, i_g]): return "Please fill in all decision fields."
        if any(v < 0 for v in [c, i_b, i_g]): return "All allocations must be non-negative."
        
        total_allocation = c + i_b + (C.GREEN_CAPITAL_COST * i_g)
        if abs(total_allocation - available_output) > 0.01:
            return f"Your total allocation ({total_allocation:.2f}) must exactly equal your available output ({available_output:.2f})."
    
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        
        if player.is_market_treatment():
            
            player.capital_brown_pre_trade = player.participant.vars.get('pre_market_brown_k', 0)
            player.capital_green_pre_trade = player.participant.vars.get('pre_market_green_k', 0)
            
            
            player.capital_brown_post_trade = player.participant.vars.get('brown_capital', 0)
            player.capital_green_post_trade = player.participant.vars.get('green_capital', 0)
        else:
            
            player.capital_brown_pre_trade = player.capital_brown_start
            player.capital_brown_post_trade = player.capital_brown_start
            player.capital_green_pre_trade = player.capital_green_start
            player.capital_green_post_trade = player.capital_green_start
        

        player.process_individual_decisions()

        
        if not player.is_market_treatment():
            player.group.update_end_of_period_state()




class EndOfPeriodWaitPage(WaitPage):
    body_text = "Waiting for other participants to submit their decisions..."
    
    @staticmethod
    def is_displayed(player: Player):
        return player.is_market_treatment()  # Only for DM
    
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.update_end_of_period_state()








class PeriodResults(Page):
    timeout_seconds = 60
    
    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        rounds_t2 = player.session.vars.get('rounds_treatment_2', 15)
        total_rounds = rounds_t1 + rounds_t2
        
        is_end_of_first_treatment = (player.round_number == rounds_t1)
        is_end_of_experiment = (player.round_number == total_rounds)
        
        return not (is_end_of_first_treatment or is_end_of_experiment)
    
    
    
    
    

    @staticmethod
    def vars_for_template(player: Player):
        is_market = player.is_market_treatment()
        group = player.group

 
        is_baseline = player.participant.vars.get('is_baseline', True)
        if is_market:
            agent_index = player.participant.vars.get('agent_type', 0)
            payoff_rate = C.AGENT_EXCHANGE_RATES_BASELINE[agent_index] if is_baseline else C.AGENT_EXCHANGE_RATES[agent_index]
        else:
            payoff_rate = C.SP_EXCHANGE_RATE_BASELINE if is_baseline else C.SP_EXCHANGE_RATE_CONTROL

        period_payoff = player.period_utility # Utility already in dollarsss

        if is_market:
            consumption = player.individual_consumption
            brown_investment = player.individual_brown_investment
            green_investment = player.individual_green_investment
        else:
            consumption = player.consumption
            brown_investment = player.brown_investment
            green_investment = player.green_investment

        # values for the START of the NEXT period (t+1)
        new_brown_capital = player.participant.vars.get('brown_capital', 0)
        new_green_capital = player.participant.vars.get('green_capital', 0)
        # temperature calculated at the END of period t, i.e., T_{t+1}
        new_temperature = player.participant.vars.get('temperature', 0)

        damage_factor = 1.0
        if not group.is_baseline_treatment():
            # Calculate damage factor based on NEXT period's temperature
            damage_factor = 1.0 / (1.0 + C.PI_1 * new_temperature + C.PI_2 * new_temperature**2)

        period_in_treatment = player.get_period_in_treatment()
        next_period_in_treatment = period_in_treatment + 1
        treatment_start_round = player.get_treatment_start_round()

       
        historical_data = []
        for r in range(treatment_start_round, player.round_number + 1):
            p_in_r = player.in_round(r)
            period_num = r - treatment_start_round + 1

            
            if is_market:
                brown_k_pre = p_in_r.capital_brown_pre_trade
                brown_k_post = p_in_r.capital_brown_post_trade
                green_k_pre = p_in_r.capital_green_pre_trade
                green_k_post = p_in_r.capital_green_post_trade
            else: # SP treatment
                brown_k_pre = p_in_r.capital_brown_pre_trade
                brown_k_post = p_in_r.capital_brown_pre_trade
                green_k_pre = p_in_r.capital_green_pre_trade
                green_k_post = p_in_r.capital_green_pre_trade

           
            output_initial = p_in_r.period_initial_output

           
            if r == treatment_start_round:
                period_temp_start = C.INITIAL_TEMPERATURE
            else:
                prev_p_in_r = player.in_round(r - 1)
                period_temp_start = prev_p_in_r.period_temperature_end 

            # --- Append data for this past round 'r' ---
            historical_data.append({
                'period': period_num,
                'brown_capital_pre': brown_k_pre,
                'brown_capital_post': brown_k_post,
                'green_capital_pre': green_k_pre,
                'green_capital_post': green_k_post,
                'temperature': period_temp_start, # Temp at START of round r (T_r)
                'consumption': p_in_r.individual_consumption if is_market else p_in_r.consumption,
                'utility': p_in_r.period_utility,
                'output_initial': output_initial,
            })

        # --- Add next period preview data point (t+1) ---
        historical_data.append({
            'period': period_in_treatment + 1,
            'brown_capital_pre': new_brown_capital, # K_{t+1}
            'brown_capital_post': new_brown_capital,
            'green_capital_pre': new_green_capital, # K_{t+1}
            'green_capital_post': new_green_capital,
            'temperature': new_temperature, # Temp for start of next period (T_{t+1})
            'consumption': None,
            'utility': None,
            'output_initial': None,
        })


        return {
            'round_number': player.round_number,
            'period_number': period_in_treatment,
            'next_period_number': next_period_in_treatment,
            'next_round': player.round_number + 1,
            'is_market': is_market,
            'is_baseline': group.is_baseline_treatment(),
            'agent_type': player.participant.vars.get('agent_type', 0) + 1 if is_market else 0,
            'consumption': round(consumption, 2),
            'brown_investment': round(brown_investment, 2),
            'green_investment': round(green_investment, 2),
            'green_cost': round(C.GREEN_CAPITAL_COST * green_investment, 2),
            'period_utility': round(player.period_utility, 2), # Utility in dollars
            'period_output': round(player.period_output, 2), # Post-trade output for DM
            'period_emissions': round(player.period_emissions, 2),
            'new_brown_capital': round(new_brown_capital, 2),
            'new_green_capital': round(new_green_capital, 2),
            'new_type3_capital_display': round(new_brown_capital, 2),
            'new_type1_capital_display': round(new_green_capital, 2),
            'new_temperature': round(new_temperature, 2), # T_{t+1}
            'damage_factor': round(damage_factor, 3), # Ω_{t+1}
            'historical_data': json.dumps(historical_data),
            'payoff_conversion_rate': round(payoff_rate, 2),
            'period_payoff': round(period_payoff, 2), # Same as period_utility now
            'exchange_rate': round(payoff_rate, 2),
        }





class TreatmentSummary(Page):
    """Summary page at the end of first treatment"""
        
    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        return player.round_number == rounds_t1
        
    @staticmethod
    def vars_for_template(player: Player):
        is_market = player.is_market_treatment()
        treatment_order = player.participant.vars['treatment_order']
        first_treatment_name = 'Decentralized Market' if (treatment_order == 'dm_first') else 'Social Planner'
         
        
        
        is_baseline = player.participant.vars.get('is_baseline', True)
        if is_market:
            agent_index = player.participant.vars.get('agent_type', 0)
            payoff_rate = C.AGENT_EXCHANGE_RATES_BASELINE[agent_index] if is_baseline else C.AGENT_EXCHANGE_RATES[agent_index]
        else:
            payoff_rate = C.SP_EXCHANGE_RATE_BASELINE if is_baseline else C.SP_EXCHANGE_RATE_CONTROL

        
        
        # Collect data from all rounds in first treatment
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        round_data = []
        for r in range(1, rounds_t1 + 1):
            p = player.in_round(r)
            
            period_payoff = p.period_utility
            
            round_data.append({
                'round': r,
                'consumption': round(p.individual_consumption if is_market else p.consumption, 2),
                'brown_investment': round(p.individual_brown_investment if is_market else p.brown_investment, 2),
                'green_investment': round(p.individual_green_investment if is_market else p.green_investment, 2),
                'output': round(p.period_output, 2),
                'emissions': round(p.period_emissions, 2),
                'period_utility': round(p.period_utility, 2),
                
                'period_payoff': round(period_payoff, 2), 
                
                'cumulative_utility': round(p.cumulative_utility, 2)
            })
                
        total_utility = player.cumulative_utility
        payment_from_first = total_utility
                
        return {
            'treatment_name': first_treatment_name,
            'total_rounds': rounds_t1,
            'total_utility': round(total_utility, 2),
            'payment_from_treatment': round(payment_from_first, 2),
            'round_data': round_data,
            'is_market': is_market,
            'is_baseline': player.group.is_baseline_treatment(),
            'final_brown_capital': round(player.participant.vars.get('brown_capital', 0), 2),
            'final_green_capital': round(player.participant.vars.get('green_capital', 0), 2),
            'final_type3_capital_display': round(player.participant.vars.get('brown_capital', 0), 2),  
            'final_type1_capital_display': round(player.participant.vars.get('green_capital', 0), 2),  
            'final_temperature': round(player.group.get_temperature(), 2)
        }

class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        rounds_t2 = player.session.vars.get('rounds_treatment_2', 15)
        total_rounds = rounds_t1 + rounds_t2
        
        
        return player.round_number == total_rounds
        


    @staticmethod
    def vars_for_template(player: Player):
        treatment_order = player.participant.vars['treatment_order']
        first_was_dm = (treatment_order == 'dm_first')

        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        rounds_t2 = player.session.vars.get('rounds_treatment_2', 15)
        total_rounds = rounds_t1 + rounds_t2


        # First treatment data
        first_treatment_rounds = []
        cumulative_payoff_1 = 0.0  
        for r in range(1, rounds_t1 + 1):
            p = player.in_round(r)
            is_market_round = first_was_dm
            period_payoff = p.period_utility
            cumulative_payoff_1 += period_payoff  
            first_treatment_rounds.append({
                'round': r,
                'consumption': round(p.individual_consumption if is_market_round else p.consumption, 2),
                'output': round(p.period_output, 2),
                'period_utility': round(p.period_utility, 2),
                'period_payoff': round(period_payoff, 2),
                'cumulative_payoff': round(cumulative_payoff_1, 2), 
                'cumulative_utility': round(p.cumulative_utility, 2)
            })

        # Second treatment data
        second_treatment_rounds = []
        cumulative_payoff_2 = 0.0  
        for r in range(rounds_t1 + 1, total_rounds + 1):
            p = player.in_round(r)
            is_market_round = not first_was_dm
            period_payoff = p.period_utility
            cumulative_payoff_2 += period_payoff 
            second_treatment_rounds.append({
                'round': r - rounds_t1,
                'consumption': round(p.individual_consumption if is_market_round else p.consumption, 2),
                'output': round(p.period_output, 2),
                'period_utility': round(p.period_utility, 2),
                'period_payoff': round(period_payoff, 2),
                'cumulative_payoff': round(cumulative_payoff_2, 2), 
                'cumulative_utility': round(p.cumulative_utility - player.in_round(rounds_t1).cumulative_utility, 2)
            })

        # Final payment calculations
        first_utility = player.in_round(rounds_t1).cumulative_utility
        second_utility_total = player.in_round(total_rounds).cumulative_utility
        second_utility_only = player.in_round(total_rounds).cumulative_utility 

        payment1 = first_utility
        payment2 = second_utility_only
        performance_payment = payment1 + payment2
        total_payment = performance_payment + 10

        return {
            'first_treatment': 'Decentralized Market' if first_was_dm else 'Social Planner',
            'second_treatment': 'Social Planner' if first_was_dm else 'Decentralized Market',
            'first_payment': round(payment1, 2),
            'second_payment': round(payment2, 2),
            'performance_payment': round(performance_payment, 2),
            'total_payment': round(total_payment, 2),
            'first_utility': round(first_utility, 2),
            'second_utility': round(second_utility_only, 2),
            'total_utility': round(first_utility + second_utility_only, 2),
            'first_treatment_rounds': first_treatment_rounds,
            'second_treatment_rounds': second_treatment_rounds,
            'is_baseline': player.participant.vars.get('is_baseline', True),
            'is_high_capital': player.participant.vars.get('is_high_capital', False),
            'rounds_t1': rounds_t1,
            'rounds_t2': rounds_t2,
            'second_treatment_start': rounds_t1 + 1,
            'total_rounds': total_rounds,
        }




class Survey(Page):
    form_model = 'player'
    form_fields = [
        'survey_q1_expectation', 'survey_q1_how_many',
        'survey_q2_expectation', 'survey_q2_how_many',
        'survey_q3_thought',
        'survey_q4_effort',
        'survey_q5_earnings_effort',
        'survey_q6_strategy',
        'survey_demo_gender',
        'survey_demo_birth_country',
        'survey_demo_degree',
        'survey_demo_year',
    ]

    @staticmethod
    def is_displayed(player: Player):
        rounds_t1 = player.session.vars.get('rounds_treatment_1', 15)
        rounds_t2 = player.session.vars.get('rounds_treatment_2', 15)
        total_rounds = rounds_t1 + rounds_t2
        
        # Display on the very last round
        return player.round_number == total_rounds

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'participant_number': player.participant.code
        }






page_sequence = [
    Instructions,
    TreatmentTransition,
    InstructionsBuffer,  
    BufferWaitPage,
    PracticeMarket,  
    PracticeMarketWait,  
    PracticeResults,  
    ProductionPhase,
    MarketWaitPage,
    CombinedCapitalMarket,
    AfterMarketWait,
    MarketResults,
    PeriodDecision,
    EndOfPeriodWaitPage,
    PeriodResults,
    TreatmentSummary,
    Survey,              
    FinalResults,
]