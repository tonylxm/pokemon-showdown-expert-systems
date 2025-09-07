from poke_env.battle import AbstractBattle
from poke_env.player import Player
from typing import Dict, List, Tuple, Optional
from enum import Enum

team = """
Deoxys-Speed @ Focus Sash
Ability: Pressure
EVs: 252 HP / 4 SpA / 252 Spe
Timid Nature
- Spikes
- Thunder Wave
- Taunt
- Psycho Boost

Kingambit @ Dread Plate  
Ability: Supreme Overlord
EVs: 252 Atk / 4 HP / 252 Spe
Adamant Nature
- Swords Dance
- Kowtow Cleave
- Iron Head
- Sucker Punch

Arceus-Fairy @ Pixie Plate
Ability: Multitype
EVs: 252 HP / 252 SpA / 4 Spe
Modest Nature
- Calm Mind
- Judgment
- Recover
- Taunt

Eternatus @ Choice Specs
Ability: Pressure
EVs: 252 SpA / 4 HP / 252 Spe
Modest Nature
- Dynamax Cannon
- Sludge Bomb
- Fire Blast
- Meteor Beam

Koraidon @ Life Orb
Ability: Orichalcum Pulse
EVs: 252 Atk / 4 HP / 252 Spe
Jolly Nature
- Scale Shot
- Close Combat
- Flame Charge
- U-turn

Ho-Oh @ Heavy-Duty Boots
Ability: Pressure
EVs: 248 HP / 252 Atk / 8 Spe
Adamant Nature
- Brave Bird
- Sacred Fire
- Earthquake
- Recover  
"""


class CustomAgent(Player):   
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)
        
        # Expert System Components
        self.knowledge_base = PokemonKnowledge()
        self.damage_calculator = DamageCalculator()
        self.expert_rules = ExpertRules()
        
        # Decision tracking for learning/evaluation
        self.decision_history = []
        self.battle_count = 0
    
    def teampreview(self, _):
        return "/team 123456"
    
    def choose_move(self, battle: AbstractBattle):
        """
        Expert System Decision Making Process
        Implements hierarchical planning: Task -> Global -> Local -> Reactive
        """
        self.battle_count += 1
        
        # Phase 1: Assess Battle State (Perception)
        battle_state = self._assess_battle_state(battle)
        
        # Phase 2: Strategic Planning (Task Planning)
        strategy = self._determine_strategy(battle_state)
        
        # Phase 3: Action Selection (Local Planning)
        action = self._select_action(battle, strategy)
        
        # Phase 4: Log Decision (Learning Component)
        self._log_decision(battle_state, strategy, action)
        
        return action
    
    def _assess_battle_state(self, battle: AbstractBattle) -> Dict:
        """Assess current battle state for expert system"""
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
        """Get team status summary"""
        status = {
            "alive_count": 0,
            "healthy_count": 0,
            "available_switches": []
        }
        
        for name, pokemon in team.items():
            if not pokemon.fainted:
                status["alive_count"] += 1
                if pokemon.current_hp_fraction > 0.5:
                    status["healthy_count"] += 1
                if not pokemon.active:
                    status["available_switches"].append(name)
                    
        return status
    
    def _determine_strategy(self, battle_state: Dict) -> str:
        """High-level strategy determination"""
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
    
    def _select_action(self, battle: AbstractBattle, strategy: str):
        """Select specific action based on strategy"""
        
        # Rule 1: Check if switching is necessary/beneficial
        should_switch, _, target_pokemon = self.expert_rules.should_switch(battle)
        
        if should_switch and strategy in ["emergency_switch", "endgame_careful"]:
            if target_pokemon and target_pokemon in battle.team:
                return self.create_order(battle.team[target_pokemon])
        
        # Rule 2: Select best move using advanced strategy (Phase 2)
        if battle.active_pokemon and hasattr(battle, 'available_moves') and battle.available_moves:
            move_evaluations = []
            
            for move in battle.available_moves:
                priority, _ = EnhancedExpertRules.evaluate_move_priority_advanced(battle, move.id)
                move_evaluations.append((move, priority))
            
            # Sort by priority and select best move
            if move_evaluations:
                move_evaluations.sort(key=lambda x: x[1], reverse=True)
                best_move, _ = move_evaluations[0]
                return self.create_order(best_move)
        
        # Fallback: random move if expert system fails
        return self.choose_random_move(battle)
    
    def _log_decision(self, battle_state: Dict, strategy: str, action):
        """Log decisions for analysis and learning"""
        decision_record = {
            "battle_count": self.battle_count,
            "turn": battle_state["turn"],
            "threat_level": battle_state["threat_level"],
            "strategy": strategy,
            "action_type": type(action).__name__,
            "my_hp": battle_state["my_active"].current_hp_fraction if battle_state["my_active"] else 0,
            "opp_hp": battle_state["opp_active"].current_hp_fraction if battle_state["opp_active"] else 0
        }
        
        self.decision_history.append(decision_record)
        
        # Keep history manageable
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for evaluation"""
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

# PHASE 1
# Expert System Knowledge Base
class PokemonKnowledge:
    """Frame-Based System for Pokémon knowledge representation"""
    
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
        "fairy": {"fire": 0.5, "fighting": 2, "poison": 0.5, "dragon": 2, "dark": 2, "steel": 0.5}
    }
    
    @staticmethod
    def get_type_effectiveness(attacking_type: str, defending_types: List[str]) -> float:
        """Calculate type effectiveness multiplier"""
        if attacking_type not in PokemonKnowledge.TYPE_CHART:
            return 1.0
            
        effectiveness = 1.0
        for defending_type in defending_types:
            if defending_type in PokemonKnowledge.TYPE_CHART[attacking_type]:
                effectiveness *= PokemonKnowledge.TYPE_CHART[attacking_type][defending_type]
        
        return effectiveness
    
    @staticmethod
    def categorize_effectiveness(multiplier: float) -> str:
        """Categorize effectiveness for expert rules"""
        if multiplier >= 2.0:
            return "super_effective"
        elif multiplier > 1.0:
            return "effective" 
        elif multiplier == 1.0:
            return "neutral"
        elif multiplier > 0.0:
            return "not_very_effective"
        else:
            return "no_effect"

class DamageCalculator:
    """Model-Based Reasoning System for damage calculations"""
    
    @staticmethod
    def calculate_damage(attacker_stats: Dict, defender_stats: Dict, move_power: int, 
                        type_effectiveness: float, is_physical: bool = True) -> Tuple[int, int]:
        """
        Calculate damage range using Pokémon damage formula
        Returns (min_damage, max_damage) tuple
        """
        if move_power == 0 or type_effectiveness == 0:
            return (0, 0)
            
        # Simplified damage calculation (Gen 9 formula)
        level = 50  # Standard competitive level
        
        if is_physical:
            attack = attacker_stats.get('attack', 100)
            defense = defender_stats.get('defense', 100)
        else:
            attack = attacker_stats.get('spa', 100)  # Special Attack
            defense = defender_stats.get('spd', 100)  # Special Defense
            
        # Base damage calculation
        base_damage = ((2 * level / 5 + 2) * move_power * attack / defense / 50 + 2)
        
        # Apply type effectiveness
        base_damage *= type_effectiveness
        
        # Apply random factor (85% to 100%)
        min_damage = int(base_damage * 0.85)
        max_damage = int(base_damage * 1.00)
        
        return (min_damage, max_damage)
    
    @staticmethod
    def damage_percentage(damage: int, max_hp: int) -> float:
        """Calculate damage as percentage of max HP"""
        if max_hp == 0:
            return 0.0
        return min(100.0, (damage / max_hp) * 100)

class ExpertRules:
    """Rule-Based System for battle decisions"""
    
    class RulePriority(Enum):
        CRITICAL = 100
        HIGH = 75
        MEDIUM = 50
        LOW = 25
    
    @staticmethod
    def evaluate_move_priority(battle: AbstractBattle, move_name: str) -> Tuple[float, str]:
        """
        Evaluate move priority based on expert rules
        Returns (priority_score, reasoning)
        """
        if not battle.active_pokemon or not battle.opponent_active_pokemon:
            return (0.0, "No active Pokémon")
            
        my_pokemon = battle.active_pokemon
        opp_pokemon = battle.opponent_active_pokemon
        
        # Get move from available moves
        move = None
        if hasattr(my_pokemon, 'moves') and my_pokemon.moves:
            for available_move in my_pokemon.moves.values():
                if available_move.id == move_name.replace(' ', '').lower():
                    move = available_move
                    break
        
        if not move:
            return (0.0, "Move not found")
            
        priority_score = ExpertRules.RulePriority.MEDIUM.value
        reasoning_parts = []
        
        # Rule 1: Type Advantage (High Priority)
        if move.type:
            opp_types = [t.name if hasattr(t, 'name') else str(t) for t in opp_pokemon.types]
            effectiveness = PokemonKnowledge.get_type_effectiveness(move.type.name, opp_types)
            
            if effectiveness >= 2.0:
                priority_score += ExpertRules.RulePriority.HIGH.value
                reasoning_parts.append("Super effective")
            elif effectiveness <= 0.5:
                priority_score -= ExpertRules.RulePriority.MEDIUM.value  
                reasoning_parts.append("Not very effective")
        
        # Rule 2: OHKO Potential (Critical Priority)
        if move.base_power and move.base_power > 0:
            # Use default stats if actual stats not available
            default_stats = {"attack": 100, "spa": 100, "defense": 100, "spd": 100, "hp": 100}
            
            my_stats = default_stats.copy()
            if hasattr(my_pokemon, 'stats') and my_pokemon.stats:
                my_stats.update({k: v for k, v in my_pokemon.stats.items() if v is not None})
            
            opp_stats = default_stats.copy()  
            if hasattr(opp_pokemon, 'stats') and opp_pokemon.stats:
                opp_stats.update({k: v for k, v in opp_pokemon.stats.items() if v is not None})
            
            is_physical = hasattr(move, 'damage_class') and move.damage_class and move.damage_class.name == "physical"
            min_damage, max_damage = DamageCalculator.calculate_damage(
                my_stats, opp_stats, move.base_power, effectiveness, is_physical
            )
            
            # Estimate opponent's current HP
            opp_max_hp = opp_stats.get("hp", 100)
            opp_current_hp = opp_pokemon.current_hp_fraction * opp_max_hp
            
            if max_damage >= opp_current_hp:
                priority_score += ExpertRules.RulePriority.CRITICAL.value
                reasoning_parts.append("Potential OHKO")
            elif min_damage >= opp_current_hp * 0.8:
                priority_score += ExpertRules.RulePriority.HIGH.value
                reasoning_parts.append("High damage potential")
        
        # Rule 3: Status Moves (Context Dependent)
        if move.base_power == 0:  # Status move
            if my_pokemon.current_hp_fraction < 0.3:
                priority_score -= ExpertRules.RulePriority.MEDIUM.value
                reasoning_parts.append("Low HP - avoid status")
            elif "heal" in move.id or "recover" in move.id:
                priority_score += ExpertRules.RulePriority.HIGH.value
                reasoning_parts.append("Healing move")
        
        # Rule 4: PP Conservation
        if hasattr(move, 'current_pp') and move.current_pp is not None and move.current_pp <= 1:
            priority_score -= ExpertRules.RulePriority.LOW.value
            reasoning_parts.append("Low PP")
            
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard move"
        return (priority_score, reasoning)
    
    @staticmethod
    def should_switch(battle: AbstractBattle) -> Tuple[bool, str, Optional[str]]:
        """
        Determine if switching is advisable
        Returns (should_switch, reasoning, recommended_pokemon)
        """
        if not battle.active_pokemon or not battle.opponent_active_pokemon:
            return (False, "No battle state", None)
            
        my_pokemon = battle.active_pokemon
        opp_pokemon = battle.opponent_active_pokemon
        
        # Rule 1: Low HP and taking super effective damage
        if my_pokemon.current_hp_fraction < 0.25:
            # Check if opponent has super effective moves
            opp_types = [t.name if hasattr(t, 'name') else str(t) for t in opp_pokemon.types]
            my_types = [t.name if hasattr(t, 'name') else str(t) for t in my_pokemon.types]
            
            # Simplified check - assume opponent might have STAB moves
            for opp_type in opp_types:
                effectiveness = PokemonKnowledge.get_type_effectiveness(opp_type, my_types)
                if effectiveness >= 2.0:
                    # Look for a resist
                    for pokemon_name, pokemon in battle.team.items():
                        if pokemon != my_pokemon and not pokemon.fainted:
                            pokemon_types = [t.name if hasattr(t, 'name') else str(t) for t in pokemon.types]
                            resist_effectiveness = PokemonKnowledge.get_type_effectiveness(opp_type, pokemon_types)
                            if resist_effectiveness <= 0.5:
                                return (True, f"Switch to resist {opp_type}", pokemon_name)
        
        # Rule 2: Bad matchup
        # Check if current Pokémon is weak to opponent's likely types
        my_types = [t.name if hasattr(t, 'name') else str(t) for t in my_pokemon.types]
        opp_types = [t.name if hasattr(t, 'name') else str(t) for t in opp_pokemon.types]
        
        threat_level = 0
        for opp_type in opp_types:
            effectiveness = PokemonKnowledge.get_type_effectiveness(opp_type, my_types)
            if effectiveness >= 2.0:
                threat_level += 2
            elif effectiveness > 1.0:
                threat_level += 1
                
        if threat_level >= 2 and my_pokemon.current_hp_fraction > 0.8:
            # Look for better matchup
            for pokemon_name, pokemon in battle.team.items():
                if pokemon != my_pokemon and not pokemon.fainted:
                    pokemon_types = [t.name if hasattr(t, 'name') else str(t) for t in pokemon.types]
                    counter_score = 0
                    for opp_type in opp_types:
                        resist_eff = PokemonKnowledge.get_type_effectiveness(opp_type, pokemon_types)
                        if resist_eff <= 0.5:
                            counter_score += 2
                        elif resist_eff < 1.0:
                            counter_score += 1
                    
                    if counter_score >= 2:
                        return (True, f"Better matchup available", pokemon_name)
        
        return (False, "Stay in", None)

# PHASE 2
"""
Advanced Expert System Features - Phase 2
Key improvements to beat classmates and reach #1
"""

class MetaGameKnowledge:
    """Advanced competitive knowledge beyond basic type charts"""
    
    # Common Uber sets and their counters
    COMMON_SETS = {
        "arceus": {
            "likely_moves": ["judgment", "recover", "calmmind", "taunt"],
            "counters": ["kingambit", "yveltal", "zacian"],
            "threat_level": "setup_sweeper"
        },
        "zacian-crowned": {
            "likely_moves": ["behemothblade", "playrough", "swordsdance", "closeombat"],
            "counters": ["necrozma-dusk-mane", "ho-oh", "skarmory"],
            "threat_level": "physical_sweeper"
        },
        "calyrex-shadow": {
            "likely_moves": ["astralbarrage", "nastyplot", "substitute", "psyshock"],
            "counters": ["yveltal", "kingambit", "blissey"],
            "threat_level": "special_sweeper"
        },
        "eternatus": {
            "likely_moves": ["dynamaxcannon", "sludgebomb", "meteorbeam", "agility"],
            "counters": ["ho-oh", "necrozma-dusk-mane", "blissey"],
            "threat_level": "special_wall_breaker"
        }
    }
    
    # Hazard stacking priorities
    HAZARD_PRIORITY = {
        "spikes": 3.0,  # Most important in Ubers
        "stealthrock": 2.0,
        "toxicspikes": 1.0
    }
    
    # Speed tiers (crucial for Ubers)
    SPEED_TIERS = {
        "deoxys-speed": 504,  # Fastest
        "mewtwo": 438,
        "calyrex-shadow": 416,
        "zacian-crowned": 361,
        "arceus": 339
    }

class AdvancedBattleStrategy:
    """Enhanced strategic decision making"""
    
    @staticmethod
    def evaluate_setup_opportunity(battle: AbstractBattle) -> Tuple[float, str]:
        """Identify setup sweeping opportunities"""
        if not battle.active_pokemon or not battle.opponent_active_pokemon:
            return (0.0, "No battle state")
        
        my_pokemon = battle.active_pokemon
        opp_pokemon = battle.opponent_active_pokemon
        
        setup_score = 0.0
        reasoning = []
        
        # Check if we have setup moves
        setup_moves = ["swordsdance", "calmmind", "nastyplot", "agility"]
        has_setup = any(move.id in setup_moves for move in my_pokemon.moves.values())
        
        if not has_setup:
            return (0.0, "No setup moves available")
        
        # Opponent is passive/walls
        opp_name = opp_pokemon.species.lower()
        if any(wall in opp_name for wall in ["blissey", "toxapex", "skarmory"]):
            setup_score += 2.0
            reasoning.append("Passive opponent")
        
        # Opponent is weakened
        if opp_pokemon.current_hp_fraction < 0.4:
            setup_score += 1.5
            reasoning.append("Weakened opponent")
        
        # We're healthy
        if my_pokemon.current_hp_fraction > 0.8:
            setup_score += 1.0
            reasoning.append("Healthy setup")
        
        # Late game advantage
        alive_count = sum(1 for p in battle.team.values() if not p.fainted)
        opp_alive = sum(1 for p in battle.opponent_team.values() if not p.fainted)
        if alive_count >= opp_alive:
            setup_score += 1.0
            reasoning.append("Numbers advantage")
        
        return (setup_score, "; ".join(reasoning))
    
    @staticmethod
    def evaluate_hazard_priority(battle: AbstractBattle) -> Tuple[float, str]:
        """Evaluate setting up entry hazards"""
        if not battle.active_pokemon:
            return (0.0, "No active pokemon")
        
        my_pokemon = battle.active_pokemon
        hazard_score = 0.0
        reasoning = []
        
        # Check for hazard moves
        hazard_moves = {
            "spikes": 3.0,
            "stealthrock": 2.0,
            "toxicspikes": 1.0
        }
        
        available_hazards = []
        for move in my_pokemon.moves.values():
            if move.id in hazard_moves:
                available_hazards.append((move.id, hazard_moves[move.id]))
        
        if not available_hazards:
            return (0.0, "No hazard moves")
        
        # Early game bonus
        if battle.turn <= 2:
            hazard_score += 2.0
            reasoning.append("Early game setup")
        
        # Check if hazards already up
        my_side = getattr(battle, 'side_conditions', {})
        for hazard_name, priority in available_hazards:
            if hazard_name not in my_side:  # Hazard not set
                hazard_score += priority
                reasoning.append(f"Need {hazard_name}")
        
        # Opponent has multiple Pokemon
        opp_alive = sum(1 for p in battle.opponent_team.values() if not p.fainted) if hasattr(battle, 'opponent_team') else 6
        if opp_alive >= 4:
            hazard_score += 1.5
            reasoning.append("Multiple targets")
        
        return (hazard_score, "; ".join(reasoning))
    
    @staticmethod
    def predict_opponent_move(battle: AbstractBattle) -> Dict[str, float]:
        """Predict opponent's most likely move"""
        if not battle.opponent_active_pokemon:
            return {}
        
        opp_pokemon = battle.opponent_active_pokemon
        opp_name = opp_pokemon.species.lower()
        
        # Use meta knowledge
        if opp_name in MetaGameKnowledge.COMMON_SETS:
            common_set = MetaGameKnowledge.COMMON_SETS[opp_name]
            predictions = {}
            
            # Higher probability for likely moves
            for move in common_set["likely_moves"]:
                predictions[move] = 0.7
            
            # Adjust based on situation
            if opp_pokemon.current_hp_fraction < 0.3:
                # Likely to attack or switch
                predictions["switch"] = 0.6
                for move in predictions:
                    if "recover" in move or "roost" in move:
                        predictions[move] = 0.8
            
            return predictions
        
        # Default predictions for unknown Pokemon
        return {
            "attack": 0.6,
            "switch": 0.3,
            "status": 0.1
        }

class WinConditionAnalyzer:
    """Determine and execute win conditions"""
    
    @staticmethod
    def analyze_win_conditions(battle: AbstractBattle) -> List[Tuple[str, float, str]]:
        """Identify possible win conditions and their viability"""
        win_conditions = []
        
        # Setup sweep condition
        for pokemon_name, pokemon in battle.team.items():
            if pokemon.fainted:
                continue
                
            setup_moves = ["swordsdance", "calmmind", "nastyplot", "agility"]
            has_setup = any(move.id in setup_moves for move in pokemon.moves.values())
            
            if has_setup and pokemon.current_hp_fraction > 0.6:
                viability = 0.7 if pokemon.active else 0.5
                win_conditions.append(("setup_sweep", viability, f"Setup with {pokemon_name}"))
        
        # Hazard stacking + residual damage
        hazard_setters = []
        for pokemon_name, pokemon in battle.team.items():
            if not pokemon.fainted:
                hazard_moves = ["spikes", "stealthrock", "toxicspikes"]
                if any(move.id in hazard_moves for move in pokemon.moves.values()):
                    hazard_setters.append(pokemon_name)
        
        if len(hazard_setters) >= 1:
            win_conditions.append(("hazard_stack", 0.6, f"Hazard stack with {hazard_setters}"))
        
        # Revenge killing
        fast_attackers = []
        for pokemon_name, pokemon in battle.team.items():
            if not pokemon.fainted and hasattr(pokemon, 'base_stats'):
                if pokemon.base_stats.get('spe', 0) > 100:  # Fast Pokemon
                    fast_attackers.append(pokemon_name)
        
        if fast_attackers:
            win_conditions.append(("revenge_kill", 0.4, f"Revenge with {fast_attackers}"))
        
        # Sort by viability
        win_conditions.sort(key=lambda x: x[1], reverse=True)
        return win_conditions

# Integration into main expert system
class EnhancedExpertRules(ExpertRules):
    """Enhanced rule system with advanced strategies"""
    
    @staticmethod
    def evaluate_move_priority_advanced(battle: AbstractBattle, move_name: str) -> Tuple[float, str]:
        """Enhanced move evaluation with meta knowledge"""
        # Get base priority from original system
        base_priority, base_reasoning = ExpertRules.evaluate_move_priority(battle, move_name)
        
        advanced_priority = base_priority
        reasoning_parts = [base_reasoning]
        
        # Setup move evaluation
        if move_name.lower() in ["swordsdance", "calmmind", "nastyplot", "agility"]:
            setup_score, setup_reason = AdvancedBattleStrategy.evaluate_setup_opportunity(battle)
            advanced_priority += setup_score * 20  # High multiplier for good setup
            reasoning_parts.append(f"Setup opportunity: {setup_reason}")
        
        # Hazard move evaluation  
        if move_name.lower() in ["spikes", "stealthrock", "toxicspikes"]:
            hazard_score, hazard_reason = AdvancedBattleStrategy.evaluate_hazard_priority(battle)
            advanced_priority += hazard_score * 15
            reasoning_parts.append(f"Hazard value: {hazard_reason}")
        
        # Priority move bonus in endgame
        if move_name.lower() in ["extremespeed", "suckerpunch", "bulletpunch"]:
            alive_count = sum(1 for p in battle.team.values() if not p.fainted)
            if alive_count <= 2:  # Endgame
                advanced_priority += 30
                reasoning_parts.append("Priority move endgame")
        
        # Meta-specific counters
        if battle.opponent_active_pokemon:
            opp_name = battle.opponent_active_pokemon.species.lower()
            if opp_name in MetaGameKnowledge.COMMON_SETS:
                # Bonus for moves that counter common threats
                threat_info = MetaGameKnowledge.COMMON_SETS[opp_name]
                if threat_info["threat_level"] == "setup_sweeper":
                    if move_name.lower() in ["taunt", "roar", "whirlwind"]:
                        advanced_priority += 25
                        reasoning_parts.append("Counter setup sweeper")
        
        combined_reasoning = " | ".join(reasoning_parts)
        return (advanced_priority, combined_reasoning)