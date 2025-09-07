from poke_env.battle import AbstractBattle
from poke_env.player import Player
from typing import Dict

# -----------------------------
# TEAM
# -----------------------------
team = """
Palkia @ Choice Specs
Ability: Pressure
Tera Type: Dragon
EVs: 252 SpA / 4 HP / 252 Spe
Timid Nature
- Hydro Pump
- Draco Meteor
- Thunder
- Fire Blast

Ting-Lu @ Leftovers  
Ability: Vessel of Ruin  
Tera Type: Water  
EVs: 252 HP / 4 Atk / 252 SpD  
Careful Nature  
- Spikes  
- Stealth Rock  
- Ruination  
- Whirlwind

Deoxys-Speed @ Focus Sash
Ability: Pressure
Tera Type: Ghost
EVs: 248 HP / 8 SpA / 252 Spe
Timid Nature
IVs: 0 Atk
- Thunder Wave
- Spikes
- Taunt
- Psycho Boost

Ho-Oh @ Heavy-Duty Boots
Ability: Regenerator
Tera Type: Flying
EVs: 248 HP / 252 Atk / 8 Spe
Adamant Nature
- Brave Bird
- Sacred Fire
- Earthquake
- Recover

Kingambit @ Dread Plate
Ability: Supreme Overlord
Tera Type: Dark
EVs: 56 HP / 252 Atk / 200 Spe
Adamant Nature
- Swords Dance
- Kowtow Cleave
- Iron Head
- Sucker Punch

Regieleki @ Choice Scarf
Ability: Transistor
Tera Type: Electric
EVs: 4 HP / 252 SpA / 252 Spe
Timid Nature
- Thunderbolt
- Volt Switch
- Hyper Beam
- Electro Ball
"""

# -----------------------------
# EXPERT SYSTEM AGENT
# -----------------------------
class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        
        # Expert System Components
        self.knowledge_base = PokemonKnowledge()
        self.damage_calculator = DamageCalculator()
        self.expert_rules = EnhancedExpertRules()
        
        # Decision tracking for learning/evaluation
        self.decision_history = []
        self.battle_count = 0

    def teampreview(self, _):
        return "/team 123456"

    def choose_move(self, battle: AbstractBattle):
        self.battle_count += 1
        battle_state = self._assess_battle_state(battle)
        strategy = self._determine_strategy(battle_state)
        action = self._select_action(battle, strategy)
        self._log_decision(battle_state, strategy, action)
        return action

    # -----------------------------
    # PHASE 1: BATTLE ASSESSMENT
    # -----------------------------
    def _assess_battle_state(self, battle: AbstractBattle) -> Dict:
        state = {
            "turn": battle.turn,
            "my_active": battle.active_pokemon,
            "opp_active": battle.opponent_active_pokemon,
            "my_team_status": self._get_team_status(battle.team),
            "field_conditions": {
                "weather": getattr(battle, 'weather', None),
                "my_side": getattr(battle, 'side_conditions', {}),
                "opp_side": getattr(battle, 'opponent_side_conditions', {})
            },
            "threat_level": "unknown"
        }
        
        # Assess threat level
        if state["my_active"] and state["opp_active"]:
            my_hp_frac = state["my_active"].current_hp_fraction
            if my_hp_frac < 0.25:
                state["threat_level"] = "critical"
            elif my_hp_frac < 0.5:
                state["threat_level"] = "high"
            else:
                state["threat_level"] = "low"
        return state

    def _get_team_status(self, team: Dict) -> Dict:
        status = {"alive_count": 0, "healthy_count": 0, "available_switches": []}
        for name, pokemon in team.items():
            if not pokemon.fainted:
                status["alive_count"] += 1
                if pokemon.current_hp_fraction > 0.5:
                    status["healthy_count"] += 1
                if not pokemon.active:
                    status["available_switches"].append(name)
        return status

    # -----------------------------
    # PHASE 2: STRATEGIC PLANNING
    # -----------------------------
    def _determine_strategy(self, battle_state: Dict) -> str:
        threat_level = battle_state["threat_level"]
        alive_count = battle_state["my_team_status"]["alive_count"]
        
        # Strategic rules based on battle state
        if threat_level == "critical":
            if len(battle_state["my_team_status"]["available_switches"]) > 0:
                return "emergency_switch"
            else:
                return "desperate_attack"
        elif alive_count <= 2:
            return "endgame_careful"
        elif battle_state["turn"] <= 3:
            return "early_game_setup"
        else:
            return "mid_game_aggressive"

    # -----------------------------
    # PHASE 3: ACTION SELECTION
    # -----------------------------
    def _select_action(self, battle: AbstractBattle, strategy: str):
        # Check optimal switch
        best_switch = EnhancedExpertRules.get_best_switch(battle)
        if best_switch and strategy in ["emergency_switch", "endgame_careful"]:
            return self.create_order(battle.team[best_switch])

        # Evaluate moves
        if battle.active_pokemon and hasattr(battle, 'available_moves') and battle.available_moves:
            move_evaluations = []
            for move in battle.available_moves:
                priority, reasoning = EnhancedExpertRules.evaluate_move_priority_advanced(battle, move.id)
                move_evaluations.append((move, priority, reasoning))
                
            # Sort by priority and select best move
            if move_evaluations:
                move_evaluations.sort(key=lambda x: x[1], reverse=True)
                best_move, _, _ = move_evaluations[0]
                return self.create_order(best_move)

        # Fallback: random move if expert system fails
        return self.choose_random_move(battle)

    # -----------------------------
    # LOGGING DECISIONS
    # -----------------------------
    def _log_decision(self, battle_state: Dict, strategy: str, action):
        decision_record = {
            "battle_count": self.battle_count,
            "turn": battle_state["turn"],
            "threat_level": battle_state["threat_level"],
            "strategy": strategy,
            "action_type": type(action).__name__,
            "my_hp": battle_state["my_active"].current_hp_fraction if battle_state["my_active"] else 0,
            "opp_hp": battle_state["opp_active"].current_hp_fraction if battle_state["opp_active"] else 0
        }
        
        # Keep history manageable
        self.decision_history.append(decision_record)
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]

    def get_performance_metrics(self) -> Dict:
        if not self.decision_history:
            return {"error": "No decision history"}
        total_decisions = len(self.decision_history)
        strategy_counts = {}
        threat_response = {"critical": 0, "high": 0, "low": 0}
        for decision in self.decision_history:
            strategy = decision["strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            threat_response[decision["threat_level"]] += 1
        return {
            "total_decisions": total_decisions,
            "battles_played": self.battle_count,
            "strategy_distribution": strategy_counts,
            "threat_response_distribution": threat_response,
            "avg_decisions_per_battle": total_decisions / max(1, self.battle_count)
        }


# -----------------------------
# PHASE 1 KNOWLEDGE BASE
# PHASE 2 ADVANCED COMPETITIVE METAGAME KNOWLEDGE (some deprecated now after PHASE 3)
# -----------------------------
class PokemonKnowledge:
    # Type effectiveness chart (attacking type -> defending type -> multiplier)
    TYPE_CHART = {
        "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
        "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
        "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
        "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
        "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
        "ice": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
        "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
        "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2},
        "ground": {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
        "flying": {"electric": 0.5, "grass": 2, "ice": 0.5, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
        "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
        "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5},
        "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
        "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
        "dragon": {"dragon": 2, "steel": 0.5, "fairy": 0},
        "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
        "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
        "fairy": {"fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5},
    }

class DamageCalculator:
    @staticmethod
    def estimate_damage(attacker, defender, move):
        # Simplified: effectiveness × power
        eff = 1.0
        if move.type in PokemonKnowledge.TYPE_CHART and defender.type_1:
            eff *= PokemonKnowledge.TYPE_CHART[move.type].get(defender.type_1, 1)
        if move.type in PokemonKnowledge.TYPE_CHART and defender.type_2:
            eff *= PokemonKnowledge.TYPE_CHART[move.type].get(defender.type_2, 1)
        return move.base_power * eff

# -----------------------------
# PHASE 3 EXPERT RULES
# -----------------------------
class EnhancedExpertRules:
    @staticmethod
    def evaluate_move_priority_advanced(battle, move_id):
        # Returns priority score and reasoning
        move = next((m for m in battle.available_moves if m.id == move_id), None)
        if not move:
            return 0, "Move not found"
        priority = move.base_power
        reasoning = f"Base power {move.base_power}"
        # Increase priority vs known Uber threats
        if battle.opponent_active_pokemon and battle.opponent_active_pokemon.species:
            species_name = battle.opponent_active_pokemon.species.lower().replace(" ", "-")
            threats = [
                "deoxys-speed",
                "kingambit",
                "zacian-crowned",
                "arceus-fairy",
                "eternatus",
                "koraidon",
            ]
        if species_name in threats:
            priority *= 1.5
            reasoning += " | Meta threat bonus applied"
        # Increase priority if it can finish opponent
        damage_est = DamageCalculator.estimate_damage(battle.active_pokemon, battle.opponent_active_pokemon, move)
        if damage_est >= battle.opponent_active_pokemon.current_hp:
            priority *= 2
            reasoning += " | KO potential"
        return priority, reasoning

    @staticmethod
    def get_best_switch(battle):
        # Return optimal switch name if any
        for mon_name, mon in battle.team.items():
            if not mon.fainted and mon != battle.active_pokemon:
                # Simple type advantage heuristic
                if any(move.type in ["fire", "electric", "ground", "dragon"] for move in mon.moves.values()):
                    return mon_name
        return None
