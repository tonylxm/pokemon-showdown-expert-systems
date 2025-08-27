from poke_env.battle import AbstractBattle
from poke_env.player import Player
from typing import Dict, List, Tuple, Optional
from enum import Enum

team = """
Pikachu @ Focus Sash  
Ability: Static  
Tera Type: Electric  
EVs: 8 HP / 248 SpA / 252 Spe  
Timid Nature  
IVs: 0 Atk  
- Thunder Wave  
- Thunder  
- Reflect
- Thunderbolt  
"""


class CustomAgent(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(team=team, *args, **kwargs)

    def choose_move(self, battle: AbstractBattle):
        return self.choose_random_move(battle)

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
