import random
import math

class Team:
    def __init__(self, name, elo, seed):
        self.name = name
        self.elo = elo
        self.seed = seed
        self.initial_seed = seed
        self.wins = 0
        self.losses = 0
        self.score = 0
        self.opponents = []
        self.total_buchholtz = 0

def calculate_win_probability(team1_elo, team2_elo):
    exp = (team2_elo - team1_elo) / 400
    return 1 / (1 + math.pow(10, exp))

def simulate_match(team1, team2, is_best_of_three):
    team1_prob = calculate_win_probability(team1.elo, team2.elo)
    team2_prob = 1 - team1_prob
    team1_wins = 0
    team2_wins = 0
    num_games = 3 if is_best_of_three else 1

    for _ in range(num_games):
        if random.random() < team1_prob:
            team1_wins += 1
        else:
            team2_wins += 1
        if is_best_of_three and (team1_wins == 2 or team2_wins == 2):
            break

    return team1 if team1_wins > team2_wins else team2

def update_scores(teams):
    for team in teams:
        team.score = team.wins - team.losses

def update_buchholtz_scores(teams):
    for team in teams:
        team.total_buchholtz = sum(opponent.score for opponent in team.opponents)

def reseed_teams(teams, stage):
    print(f"Before reseeding (Stage {stage}):")
    for team in teams:
        print(f"{team.name}: Seed = {team.seed}, Buchholz = {team.total_buchholtz}")

    if stage == 2:
        teams.sort(key=lambda x: x.initial_seed)
    else:
        teams.sort(key=lambda x: (-x.total_buchholtz, x.initial_seed))
        same_buchholz_teams = {}
        for i, team in enumerate(teams, start=1):
            if team.total_buchholtz not in same_buchholz_teams:
                same_buchholz_teams[team.total_buchholtz] = []
            same_buchholz_teams[team.total_buchholtz].append(team)
            team.seed = i

        for buchholz, buchholz_teams in same_buchholz_teams.items():
            buchholz_teams.sort(key=lambda x: x.initial_seed)
            for i, team in enumerate(buchholz_teams, start=teams.index(buchholz_teams[0]) + 1):
                team.seed = i

    print(f"After reseeding (Stage {stage}):")
    for team in teams:
        print(f"{team.name}: Seed = {team.seed}, Buchholz = {team.total_buchholtz}")

def swap_opponents(team1, team2, matchups):
    print(f"Swapping opponents of {team1.name} and {team2.name}")
    team1_opponent = next((opponent for match in matchups for opponent in match if team1 in match and opponent != team1), None)
    team2_opponent = next((opponent for match in matchups for opponent in match if team2 in match and opponent != team2), None)
    if team1_opponent and team2_opponent:
        matchups.remove((team1, team1_opponent))
        matchups.remove((team2, team2_opponent))
        matchups.append((team1, team2_opponent))
        matchups.append((team2, team1_opponent))
    else:
        print("Error: Could not find suitable opponents to swap")

def has_played_before(team1, team2):
    return team2 in team1.opponents or team1 in team2.opponents

def count_repeated_matchups(matchups):
    count = 0
    for match in matchups:
        if has_played_before(match[0], match[1]):
            count += 1
    return count

def create_matchups(teams):
    matchups = []
    num_teams = len(teams)
    selected_teams = set()

    for i in range(num_teams):
        team1 = teams[i]
        if team1 in selected_teams:
            continue

        opponent_found = False
        for j in range(num_teams - 1, i, -1):
            team2 = teams[j]
            if team2 not in selected_teams and not has_played_before(team1, team2) and team1 != team2:
                matchups.append((team1, team2))
                selected_teams.add(team1)
                selected_teams.add(team2)
                opponent_found = True
                break

        if not opponent_found:
            remaining_teams = [team for team in teams if team not in selected_teams and team != team1]
            if len(remaining_teams) == 0:
                break

            if len(teams) == 6:  # Special case for stage 5
                opponent_found = False
                for team2 in remaining_teams:
                    if not has_played_before(team1, team2):
                        matchups.append((team1, team2))
                        selected_teams.add(team1)
                        selected_teams.add(team2)
                        opponent_found = True
                        break

                if not opponent_found:
                    team2 = remaining_teams[0]
                    matchups.append((team1, team2))
                    selected_teams.add(team1)
                    selected_teams.add(team2)
            else:
                while not opponent_found:
                    for team2 in remaining_teams:
                        if not has_played_before(team1, team2):
                            matchups.append((team1, team2))
                            selected_teams.add(team1)
                            selected_teams.add(team2)
                            opponent_found = True
                            break

                    if not opponent_found:
                        for team2 in remaining_teams:
                            if team2 not in [match[0] for match in matchups] and team2 not in [match[1] for match in matchups]:
                                swap_team = team2
                                swap_index = teams.index(swap_team)
                                for j in range(swap_index + 1, num_teams):
                                    swap_candidate = teams[j]
                                    if swap_candidate not in selected_teams and not has_played_before(team1, swap_candidate):
                                        swap_opponents(swap_team, swap_candidate, matchups)
                                        selected_teams.add(team1)
                                        selected_teams.add(swap_candidate)
                                        opponent_found = True
                                        break
                                if opponent_found:
                                    break

                        if not opponent_found:
                            team2 = remaining_teams[0]
                            matchups.append((team1, team2))
                            selected_teams.add(team1)
                            selected_teams.add(team2)
                            break

    return matchups

def get_teams_by_record(teams, wins, losses):
    return [team for team in teams if team.wins == wins and team.losses == losses]

def simulate_tournament(teams):
    stage = 1
    stage_results = {}

    while stage <= 5:
        print(f"Stage {stage} Matchups:")
        matchups = []
        active_teams = [team for team in teams if team.wins < 3 and team.losses < 3]

        if stage == 1:
            matchups = [
                (active_teams[0], active_teams[8]),   # Cloud9 vs ECSTATIC
                (active_teams[1], active_teams[9]),   # Eternal Fire vs Mongolz
                (active_teams[2], active_teams[10]),  # ENCE vs Imperial
                (active_teams[3], active_teams[11]),  # Apeks vs Pain
                (active_teams[4], active_teams[12]),  # Heroic vs Lynn
                (active_teams[5], active_teams[13]),  # 9Pandas vs AMKAL
                (active_teams[6], active_teams[14]),  # SAW vs KOI
                (active_teams[7], active_teams[15])   # FURIA vs Legacy
            ]
        else:
            update_scores(teams)  # Update scores for all teams
            update_buchholtz_scores(teams)  # Update Buchholz scores for all teams
            for wins in range(stage):
                for losses in range(stage):
                    if wins + losses == stage - 1:
                        record_teams = get_teams_by_record(active_teams, wins, losses)
                        print(f"Teams with record {wins}-{losses}:")
                        for team in record_teams:
                            print(f"{team.name}: Seed = {team.seed}, Buchholz = {team.total_buchholtz}")
                        reseed_teams(record_teams, stage)
                        matchups.extend(create_matchups(record_teams))

        stage_winners = []
        stage_losers = []
        for matchup in matchups:
            team1, team2 = matchup
            is_best_of_three = (team1.wins == 2 or team1.losses == 2) or (team2.wins == 2 or team2.losses == 2)
            match_type = "Bo3" if is_best_of_three else "Bo1"
            print(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - {match_type}")
            winner = simulate_match(team1, team2, is_best_of_three)
            loser = team1 if winner == team2 else team2
            team1.opponents.append(team2)
            team2.opponents.append(team1)
            winner.wins += 1
            loser.losses += 1
            stage_winners.append(winner)
            stage_losers.append(loser)

        stage_results[stage] = {
            "winners": [team.name for team in stage_winners],
            "losers": [team.name for team in stage_losers]
        }
        print()
        print(f"Stage {stage} Winners:")
        print(", ".join(stage_results[stage]["winners"]))
        print()
        stage += 1

    return teams, stage_results

def get_team_finishing_positions(teams):
    team_positions = {}
    for team in teams:
        record = (team.wins, team.losses)
        if record == (3, 0):
            team_positions[team.name] = "3-0"
        elif record == (3, 1):
            team_positions[team.name] = "3-1"
        elif record == (3, 2):
            team_positions[team.name] = "3-2"
        elif record == (2, 3):
            team_positions[team.name] = "2-3"
        elif record == (1, 3):
            team_positions[team.name] = "1-3"
        elif record == (0, 3):
            team_positions[team.name] = "0-3"
    return team_positions

# Create team instances with their Elo ratings and seedings
teams = [
    Team("Cloud9", 1520, 1),
    Team("Eternal Fire", 1508, 2),
    Team("ENCE", 1454, 3),
    Team("Apeks", 1436, 4),
    Team("Heroic", 1433, 5),
    Team("9Pandas", 1173, 6),
    Team("SAW", 1140, 7),
    Team("FURIA", 1391, 8),
    Team("ECSTATIC", 1127, 9),
    Team("Mongolz", 1433, 10),
    Team("Imperial", 1152, 11),
    Team("paiN Gaming", 1048, 12),
    Team("Lynn Vision", 1152, 13),
    Team("AMKAL", 1083, 14),
    Team("KOI", 1046, 15),
    Team("Legacy", 1009, 16)
]

# Simulate the tournament and get each team's finishing position
remaining_teams, stage_results = simulate_tournament(teams)
team_positions = get_team_finishing_positions(remaining_teams)

# Print each team's finishing position
print("Team Finishing Positions:")
for team_name, position in team_positions.items():
    print(f"{team_name}: {position}")