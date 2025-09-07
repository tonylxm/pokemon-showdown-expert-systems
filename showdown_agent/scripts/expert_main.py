# node pokemon-showdown start --no-security

import asyncio
import importlib
import os
import sys
from typing import List

import poke_env as pke
from poke_env import AccountConfiguration
from poke_env.player.player import Player
from tabulate import tabulate


def rank_players_by_victories(results_dict, top_k=10):
    victory_scores = {}

    for player, opponents in results_dict.items():
        victories = [
            1 if (score is not None and score > 0.5) else 0
            for opp, score in opponents.items()
            if opp != player
        ]
        victory_scores[player] = sum(victories) / len(victories) if victories else 0.0

    # Sort by descending victory rate
    sorted_players = sorted(victory_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_players[:top_k]


def gather_players():
    player_folders = os.path.join(os.path.dirname(__file__), "players")
    players = []

    replay_dir = os.path.join(os.path.dirname(__file__), "replays")
    os.makedirs(replay_dir, exist_ok=True)

    for module_name in os.listdir(player_folders):
        if module_name.endswith(".py"):
            module_path = f"{player_folders}/{module_name}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            if hasattr(module, "CustomAgent"):
                player_name = module_name[:-3]
                agent_class = getattr(module, "CustomAgent")

                agent_replay_dir = os.path.join(replay_dir, f"{player_name}")
                os.makedirs(agent_replay_dir, exist_ok=True)

                account_config = AccountConfiguration(player_name, None)
                player = agent_class(
                    account_configuration=account_config,
                    battle_format="gen9ubers",
                )
                player._save_replays = agent_replay_dir
                players.append(player)

    return players


def gather_bots():
    bot_folders = os.path.join(os.path.dirname(__file__), "bots")
    bot_teams_folders = os.path.join(bot_folders, "teams")

    generic_bots = []
    bot_teams = {}

    for team_file in os.listdir(bot_teams_folders):
        if team_file.endswith(".txt"):
            with open(os.path.join(bot_teams_folders, team_file), "r", encoding="utf-8") as file:
                bot_teams[team_file[:-4]] = file.read()

    for module_name in os.listdir(bot_folders):
        if module_name.endswith(".py"):
            module_path = f"{bot_folders}/{module_name}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            for team_name, team in bot_teams.items():
                if hasattr(module, "CustomAgent"):
                    agent_class = getattr(module, "CustomAgent")
                    config_name = f"{module_name[:-3]}-{team_name}"
                    account_config = AccountConfiguration(config_name, None)
                    generic_bots.append(
                        agent_class(
                            team=team,
                            account_configuration=account_config,
                            battle_format="gen9ubers",
                        )
                    )

    return generic_bots


async def cross_evaluate(agents: List[Player]):
    return await pke.cross_evaluate(agents, n_challenges=3)


def evalute_againts_bots(players: List[Player]):
    print(f"{len(players)} are competing in this challenge")
    print("Running Cross Evaluations...")

    cross_evaluation_results = asyncio.run(cross_evaluate(players))
    print("Evaluations Complete")

    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation_results.items():
        table.append([p_1] + [cross_evaluation_results[p_1][p_2] for p_2 in results])

    headers = table[0]
    data = table[1:]
    print(tabulate(data, headers=headers, floatfmt=".2f"))

    print("Rankings")
    top_players = rank_players_by_victories(cross_evaluation_results, top_k=len(cross_evaluation_results))
    return top_players


def assign_marks(rank: int) -> float:
    modifier = 1.0 if rank > 10 else 0.5
    top_marks = 10.0 if rank < 10 else 5.0
    mod_rank = rank % 10
    marks = top_marks - (mod_rank - 1) * modifier
    return max(marks, 0.0)


def main():
    try:
        generic_bots = gather_bots()
        players = gather_players()

        results_file = os.path.join(os.path.dirname(__file__), "results", "marking_results.txt")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)

        with open(results_file, "w", encoding="utf-8") as file:
            pass  # Clear previous results

        for player in players:
            agents = [player] + generic_bots
            print(f"Evaluating player: {player.username}")

            agent_rankings = evalute_againts_bots(agents)

            player_rank = len(agents) + 1
            player_mark = 0.0
            print("Rank. Player - Win Rate - Mark")
            for rank, (agent, winrate) in enumerate(agent_rankings, 1):
                mark = assign_marks(rank)
                print(f"{rank}. {agent} - {winrate:.2f} - {mark}")
                if agent == player.username:
                    player_rank = rank
                    player_mark = mark

            print(f"{player.username} ranked #{player_rank} with a mark of {player_mark}\n")

            with open(results_file, "a", encoding="utf-8") as file:
                file.write(f"{player.username} #{player_rank} {player_mark}\n")

    except KeyboardInterrupt:
        print("\n⚠️ Evaluation interrupted! Saving progress...")
    finally:
        print("✅ Exiting gracefully. Results saved to:", results_file)


if __name__ == "__main__":
    main()
