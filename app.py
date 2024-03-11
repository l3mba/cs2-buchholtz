from flask import Flask, render_template, request, jsonify, session
from working import simulate_tournament, get_team_finishing_positions, Team
import os
import threading
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def create_default_teams():
    return [
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

simulation_thread = None
simulations_completed = {}
simulation_threads = {}
simulation_results = {}
session_teams = {}
teams = create_default_teams()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/simulate', methods=['GET', 'POST'])
def simulate():
    if 'session_id' not in session:
        session['session_id'] = str(uuid4())

    session_id = session['session_id']

    if session_id not in simulation_results:
        simulation_results[session_id] = {
            'team_positions': {},
            'team_qualified_count': {},
            'stage_results': {}
        }

    if session_id not in session_teams:
        session_teams[session_id] = create_default_teams()

    if session_id not in simulations_completed:
        simulations_completed[session_id] = 0

    if request.method == 'POST':
        num_simulations = int(request.form.get('num_simulations', 0))
        max_simulations = 100000
        if num_simulations > max_simulations:
            return "Error: Maximum number of simulations exceeded."

        session_simulation_results = simulation_results[session_id]
        session_simulation_results['team_positions'].clear()
        session_simulation_results['team_qualified_count'].clear()
        session_simulation_results['stage_results'].clear()
        simulations_completed[session_id] = 0

        def run_simulations(thread_id, start, end):
            team_qualified_count = {team.name: 0 for team in session_teams[session_id]}
            team_positions = {}
            for i in range(start, end):
                simulation_teams = [Team(team.name, team.elo, team.seed) for team in session_teams[session_id]]
                remaining_teams, stage_results = simulate_tournament(simulation_teams)
                positions = get_team_finishing_positions(remaining_teams)
                for team, position in positions.items():
                    if team not in team_positions:
                        team_positions[team] = {
                            '3-0': 0, '3-1': 0, '3-2': 0,
                            '2-3': 0, '1-3': 0, '0-3': 0
                        }
                    team_positions[team][position] += 1
                    if position in ['3-0', '3-1', '3-2']:
                        team_qualified_count[team] += 1
                simulations_completed[session_id] += 1

            with threading.Lock():
                for team, count in team_qualified_count.items():
                    if team not in session_simulation_results['team_qualified_count']:
                        session_simulation_results['team_qualified_count'][team] = 0
                    session_simulation_results['team_qualified_count'][team] += count

                for team, positions in team_positions.items():
                    if team not in session_simulation_results['team_positions']:
                        session_simulation_results['team_positions'][team] = {
                            '3-0': 0, '3-1': 0, '3-2': 0,
                            '2-3': 0, '1-3': 0, '0-3': 0
                        }
                    for position, count in positions.items():
                        session_simulation_results['team_positions'][team][position] += count

        num_threads = 4
        simulations_per_thread = num_simulations // num_threads
        threads = []

        for i in range(num_threads):
            start = i * simulations_per_thread
            end = start + simulations_per_thread
            if i == num_threads - 1:
                end = num_simulations
            thread = threading.Thread(target=run_simulations, args=(i, start, end))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_simulations = num_simulations
        for team in session_simulation_results['team_positions']:
            for position in session_simulation_results['team_positions'][team]:
                session_simulation_results['team_positions'][team][position] = round(
                    session_simulation_results['team_positions'][team][position] / total_simulations * 100, 2
                )
            session_simulation_results['team_positions'][team]['qualified'] = round(
                session_simulation_results['team_qualified_count'][team] / total_simulations * 100, 2
            )
            session_simulation_results['team_positions'][team]['eliminated'] = round(
                100 - session_simulation_results['team_positions'][team]['qualified'], 2
            )

    return render_template('simulate.html', teams=session_teams[session_id],
                           simulations_completed=simulations_completed[session_id],
                           simulation_results=simulation_results[session_id])

@app.route('/simulations-completed')
def get_simulations_completed():
    session_id = request.args.get('session_id')
    if session_id is None or session_id not in simulations_completed:
        return jsonify(simulations_completed=0, simulation_results={})
    return jsonify(simulations_completed=simulations_completed[session_id],
                   simulation_results=simulation_results[session_id])

@app.route('/update-teams', methods=['POST'])
def update_teams():
    session_id = session['session_id']
    updated_teams = []
    for i in range(16):
        team_name = request.form[f'team_name_{i}']
        team_elo = int(request.form[f'team_elo_{i}'])
        updated_teams.append(Team(team_name, team_elo, i+1))
    session_teams[session_id] = updated_teams
    return render_template('simulate.html', teams=session_teams[session_id],
                           simulations_completed=len(simulation_results[session_id].get('team_positions', [])),
                           simulation_results=simulation_results[session_id])

@app.route('/reset-teams', methods=['POST'])
def reset_teams():
    session_id = session['session_id']
    session_teams[session_id] = create_default_teams()
    return render_template('simulate.html', teams=session_teams[session_id],
                           simulations_completed=len(simulation_results[session_id].get('team_positions', [])),
                           simulation_results=simulation_results[session_id])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)