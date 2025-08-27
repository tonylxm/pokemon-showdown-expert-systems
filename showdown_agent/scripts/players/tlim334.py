from poke_env.battle import AbstractBattle
from poke_env.player import Player
from typing import Dict, List, Tuple

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
