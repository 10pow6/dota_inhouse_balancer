import itertools
import math
import csv
import sys

def calculate_rms(team_mmrs):
    """Calculate Root Mean Square (Quadratic Mean) for a team"""
    return math.sqrt(sum(mmr**2 for mmr in team_mmrs) / len(team_mmrs))

def calculate_avg(team_mmrs):
    """Arithmetic mean (average MMR) of a team"""
    return sum(team_mmrs) / len(team_mmrs)

def calculate_std(team_mmrs):
    """Population standard deviation (skill spread) of a team"""
    mean = calculate_avg(team_mmrs)
    return math.sqrt(sum((mmr - mean) ** 2 for mmr in team_mmrs) / len(team_mmrs))

def read_team_restrictions(filename="prevent_same_team.txt"):
    """Read team restrictions from file (players who cannot be on same team)"""
    restrictions = []
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                
                players = [p.strip() for p in line.split(',')]
                players = [p for p in players if p]
                
                if len(players) >= 2:
                    restrictions.append(players)
                elif len(players) == 1:
                    print(f"Warning: Line {line_num} in {filename} has only one player: {players[0]}")
        
        if restrictions:
            print(f"\nLoaded {len(restrictions)} team restrictions from {filename}")
            for i, group in enumerate(restrictions, 1):
                print(f"  {i}. {', '.join(group)} cannot be on the same team")
        
        return restrictions
    
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Warning: Error reading {filename}: {str(e)}")
        return []

def read_force_same_team(filename="force_same_team.txt"):
    """Read forced team combinations from file (players who must be on same team)"""
    forced_groups = []
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                
                players = [p.strip() for p in line.split(',')]
                players = [p for p in players if p]
                
                if len(players) >= 2:
                    forced_groups.append(players)
                elif len(players) == 1:
                    print(f"Warning: Line {line_num} in {filename} has only one player: {players[0]}")
        
        if forced_groups:
            print(f"\nLoaded {len(forced_groups)} forced team combinations from {filename}")
            for i, group in enumerate(forced_groups, 1):
                print(f"  {i}. {', '.join(group)} must be on the same team")
        
        return forced_groups
    
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Warning: Error reading {filename}: {str(e)}")
        return []

def check_team_validity(team_indices, player_names, restrictions):
    """Check if a team composition violates any restrictions"""
    team_names = [player_names[i] for i in team_indices]
    
    for restricted_group in restrictions:
        count = sum(1 for player in restricted_group if player in team_names)
        if count >= 2:
            return False
    
    return True

def check_forced_team_validity(team_a_indices, team_b_indices, player_names, forced_groups):
    """Check if team assignments respect forced team combinations"""
    team_a_names = [player_names[i] for i in team_a_indices]
    team_b_names = [player_names[i] for i in team_b_indices]
    
    for forced_group in forced_groups:
        players_in_a = sum(1 for player in forced_group if player in team_a_names)
        players_in_b = sum(1 for player in forced_group if player in team_b_names)
        
        # If any players from a forced group are present, ALL must be on the same team
        if players_in_a > 0 and players_in_b > 0:
            return False
        
        # Check if all players from the forced group who are playing are together
        total_playing = players_in_a + players_in_b
        if total_playing > 0:
            # If we have some but not all players from the group, and they're split, it's invalid
            if 0 < players_in_a < total_playing or 0 < players_in_b < total_playing:
                # This means they're split between teams
                return False
    
    return True

# How heavily the multi-objective lens weights the spread (std) gap relative to
# the average gap. Both terms are in MMR units, so 1.0 weights them equally.
# Higher = punish lopsided skill distribution (e.g. stacking smurfs) more
# aggressively, at the cost of allowing a slightly larger average gap.
MULTI_STD_WEIGHT = 1.0

# The three balancing "lenses". Each scores the same set of valid combinations
# differently; lower score = more balanced.
#   - average: equalize total team strength (the standard matchmaking metric)
#   - multi:   weighted blend of the average gap and the spread (std) gap, so a
#              split with a slightly worse average but a much fairer skill
#              distribution can win. Stacking high-MMR players onto one team
#              spikes the std gap, so this lens naturally splits the carries.
#   - rms:     equalize the quadratic mean (over-weights high-MMR players)
LENSES = [
    {
        'key': 'multi',
        'title': 'MULTI-OBJECTIVE (Average gap + weighted spread gap)',
        'sort': lambda a: a['avg_diff'] + MULTI_STD_WEIGHT * a['std_diff'],
    },
    {
        'key': 'average',
        'title': 'AVERAGE (Total team strength)',
        'sort': lambda a: a['avg_diff'],
    },
    {
        'key': 'rms',
        'title': 'RMS (Quadratic mean)',
        'sort': lambda a: a['rms_diff'],
    },
]

def evaluate_all_assignments(players_mmr, restrictions=None, forced_groups=None):
    """Score every valid team split, returning a metrics dict per combination."""
    n = len(players_mmr)
    player_names = [p[0] for p in players_mmr]

    # Anchor index 0 to team A so each split is counted once
    # (otherwise {0,1,2,3,4} vs {5,6,7,8,9} appears twice with teams swapped)
    all_combinations = (
        (0,) + combo
        for combo in itertools.combinations(range(1, n), 4)
    )

    assignments = []
    invalid_count = 0
    restriction_violations = 0
    forced_violations = 0

    for team_a_indices in all_combinations:
        team_b_indices = tuple(i for i in range(n) if i not in team_a_indices)

        # Check restrictions (cannot be on same team)
        if restrictions:
            team_a_valid = check_team_validity(team_a_indices, player_names, restrictions)
            team_b_valid = check_team_validity(team_b_indices, player_names, restrictions)

            if not (team_a_valid and team_b_valid):
                restriction_violations += 1
                invalid_count += 1
                continue

        # Check forced teams (must be on same team)
        if forced_groups:
            if not check_forced_team_validity(team_a_indices, team_b_indices, player_names, forced_groups):
                forced_violations += 1
                invalid_count += 1
                continue

        team_a_mmrs = [players_mmr[i][1] for i in team_a_indices]
        team_b_mmrs = [players_mmr[i][1] for i in team_b_indices]

        avg_a, avg_b = calculate_avg(team_a_mmrs), calculate_avg(team_b_mmrs)
        rms_a, rms_b = calculate_rms(team_a_mmrs), calculate_rms(team_b_mmrs)
        std_a, std_b = calculate_std(team_a_mmrs), calculate_std(team_b_mmrs)

        assignments.append({
            'team_a_indices': team_a_indices,
            'team_b_indices': team_b_indices,
            'avg_a': avg_a, 'avg_b': avg_b, 'avg_diff': abs(avg_a - avg_b),
            'rms_a': rms_a, 'rms_b': rms_b, 'rms_diff': abs(rms_a - rms_b),
            'std_a': std_a, 'std_b': std_b, 'std_diff': abs(std_a - std_b),
        })

    if invalid_count > 0:
        print(f"\nFiltered out {invalid_count} team combinations:")
        if restriction_violations > 0:
            print(f"  - {restriction_violations} due to 'prevent same team' restrictions")
        if forced_violations > 0:
            print(f"  - {forced_violations} due to 'force same team' requirements")
        print(f"Valid combinations remaining: {len(assignments)}")

    if not assignments:
        raise ValueError("No valid team combinations found with the given restrictions and forced teams!")

    return assignments

def top_by_lens(assignments, lens, top_n=3):
    """Return the top N assignments ranked by the given lens' sort key."""
    ranked = sorted(assignments, key=lens['sort'])
    return ranked[:min(top_n, len(ranked))]

def read_players_from_file(filename="player_list.txt"):
    """Read players from a CSV file with headers: name,mmr,playing"""
    all_players = []
    playing_players = []
    errors = []
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            lines = file.readlines()
            
            if not lines:
                raise ValueError("File is empty")
            
            first_line = lines[0].strip()
            start_line = 0

            # Detect a header row by structure, not by substring match, so that
            # player names like "Nameless" or "Mmravic" aren't mistaken for headers.
            header_fields = None
            for delim in [',', '\t', '|', ';']:
                candidate = [p.strip().lower() for p in first_line.split(delim)]
                if len(candidate) >= 2:
                    header_fields = candidate
                    break

            if header_fields:
                # It's a header if a known column name appears as a full field, or if
                # the second column isn't an integer (data rows always have numeric MMR).
                if header_fields[0] == 'name' or 'mmr' in header_fields or 'playing' in header_fields:
                    start_line = 1
                else:
                    try:
                        int(header_fields[1])
                    except ValueError:
                        start_line = 1
            
            for line_num, line in enumerate(lines[start_line:], start_line + 1):
                line = line.strip()
                if not line:
                    continue
                
                delimiter = ','
                parts = line.split(delimiter)
                
                if len(parts) != 3:
                    for delim in ['\t', '|', ';']:
                        parts = line.split(delim)
                        if len(parts) == 3:
                            delimiter = delim
                            break
                    else:
                        errors.append(f"Line {line_num}: Expected 3 columns but got {len(parts)}: {line}")
                        continue
                
                player_name = parts[0].strip()
                if not player_name:
                    errors.append(f"Line {line_num}: Player name is empty")
                    continue
                
                try:
                    mmr = int(parts[1].strip())
                    if mmr < 0:
                        errors.append(f"Line {line_num}: MMR cannot be negative: {mmr}")
                        continue
                    if mmr > 10000:
                        errors.append(f"Line {line_num}: MMR seems too high (>10000): {mmr}")
                except ValueError:
                    errors.append(f"Line {line_num}: MMR must be a number, got: '{parts[1].strip()}'")
                    continue
                
                playing_status = parts[2].strip().lower()
                is_playing = playing_status in ['yes', 'y', 'true', '1']
                
                if playing_status not in ['yes', 'y', 'true', '1', 'no', 'n', 'false', '0']:
                    errors.append(f"Line {line_num}: Invalid playing status '{parts[2].strip()}'. Use yes/no, y/n, true/false, or 1/0")
                    continue
                
                all_players.append({
                    'name': player_name,
                    'mmr': mmr,
                    'playing': is_playing
                })
                
                if is_playing:
                    playing_players.append((player_name, mmr))
            
            if errors:
                print("\nWarnings/Errors found while reading file:")
                for error in errors[:5]:
                    print(f"  - {error}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more errors")
                print()
            
            return all_players, playing_players
    
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filename}' not found. Please create a file named 'player_list.txt' with columns: name,mmr,playing")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def validate_player_count(playing_players):
    """Validate that exactly 10 players are marked as playing"""
    count = len(playing_players)
    
    if count < 10:
        print("\nERROR: Not enough players!")
        print(f"Need exactly 10 players marked as 'playing', but only found {count}")
        print("\nPlayers currently marked as playing:")
        for i, (name, mmr) in enumerate(playing_players, 1):
            print(f"  {i}. {name}: {mmr}")
        print(f"\nPlease mark {10 - count} more player(s) as 'playing' in the player_list.txt file")
        return False
    
    elif count > 10:
        print("\nERROR: Too many players!")
        print(f"Need exactly 10 players marked as 'playing', but found {count}")
        print("\nPlayers currently marked as playing:")
        for i, (name, mmr) in enumerate(playing_players, 1):
            print(f"  {i}. {name}: {mmr}")
        print(f"\nPlease change {count - 10} player(s) to 'no' in the player_list.txt file")
        return False
    
    return True

def validate_restrictions(restrictions, playing_players):
    """Validate that restriction names match playing players"""
    player_names = [p[0] for p in playing_players]
    warnings = []
    
    for i, group in enumerate(restrictions, 1):
        for player in group:
            if player not in player_names:
                warnings.append(f"Restriction {i}: '{player}' is not in the list of playing players")
    
    if warnings:
        print("\nWarnings about restrictions:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

def validate_forced_teams(forced_groups, playing_players):
    """Validate that forced team names match playing players"""
    player_names = [p[0] for p in playing_players]
    warnings = []
    
    for i, group in enumerate(forced_groups, 1):
        for player in group:
            if player not in player_names:
                warnings.append(f"Forced team {i}: '{player}' is not in the list of playing players")
    
    if warnings:
        print("\nWarnings about forced teams:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

def print_assignment(players_data, assignment, option_num):
    """Print a single team assignment with avg / RMS / std for both teams"""
    team_a = [players_data[i] for i in assignment['team_a_indices']]
    team_b = [players_data[i] for i in assignment['team_b_indices']]

    print(f"\n{'='*50}")
    print(f"OPTION {option_num}")
    print(f"{'='*50}")

    print("\nTEAM A:")
    for player, mmr in sorted(team_a, key=lambda x: x[1], reverse=True):
        print(f"  {player}: {mmr}")
    print(f"\nTeam A  Avg: {assignment['avg_a']:.1f}  RMS: {assignment['rms_a']:.1f}  Std: {assignment['std_a']:.1f}")

    print("\n" + "-"*30)

    print("\nTEAM B:")
    for player, mmr in sorted(team_b, key=lambda x: x[1], reverse=True):
        print(f"  {player}: {mmr}")
    print(f"\nTeam B  Avg: {assignment['avg_b']:.1f}  RMS: {assignment['rms_b']:.1f}  Std: {assignment['std_b']:.1f}")

    print("\n" + "-"*30)
    print(f"Average Difference: {assignment['avg_diff']:.1f}")
    print(f"RMS Difference:     {assignment['rms_diff']:.1f}")
    print(f"Std Difference:     {assignment['std_diff']:.1f}")

def write_assignment_to_file(file, players_data, assignment, option_num):
    """Write a single assignment to file with avg / RMS / std for both teams"""
    team_a = [players_data[i] for i in assignment['team_a_indices']]
    team_b = [players_data[i] for i in assignment['team_b_indices']]

    file.write(f"\nOPTION {option_num}\n")
    file.write("="*50 + "\n\n")

    file.write("TEAM A:\n")
    for player, mmr in sorted(team_a, key=lambda x: x[1], reverse=True):
        file.write(f"  {player}: {mmr}\n")
    file.write(f"\nTeam A  Avg: {assignment['avg_a']:.1f}  RMS: {assignment['rms_a']:.1f}  Std: {assignment['std_a']:.1f}\n")

    file.write("\n" + "-"*30 + "\n\n")

    file.write("TEAM B:\n")
    for player, mmr in sorted(team_b, key=lambda x: x[1], reverse=True):
        file.write(f"  {player}: {mmr}\n")
    file.write(f"\nTeam B  Avg: {assignment['avg_b']:.1f}  RMS: {assignment['rms_b']:.1f}  Std: {assignment['std_b']:.1f}\n")

    file.write("\n" + "-"*30 + "\n")
    file.write(f"Average Difference: {assignment['avg_diff']:.1f}\n")
    file.write(f"RMS Difference:     {assignment['rms_diff']:.1f}\n")
    file.write(f"Std Difference:     {assignment['std_diff']:.1f}\n")

def create_sample_files():
    """Create sample files"""
    player_content = """name,mmr,playing
Alice,3000,yes
Bob,3500,yes
Charlie,4000,yes
David,4500,yes
Eve,5000,yes
Frank,3200,yes
Grace,3800,yes
Henry,4200,yes
Ivy,4700,yes
Jack,5100,yes
Kate,4300,no
Leo,3900,no
Mike,4600,no
Nancy,4400,no
Oscar,3700,no
"""
    with open("player_list_sample.txt", "w") as f:
        f.write(player_content)
    
    prevent_content = """Alice,Bob,Charlie
David,Eve
Frank,Grace,Henry
"""
    with open("prevent_same_team_sample.txt", "w") as f:
        f.write(prevent_content)
    
    force_content = """Alice,David
Frank,Jack
"""
    with open("force_same_team_sample.txt", "w") as f:
        f.write(force_content)
    
    print("Created sample files:")
    print("  - 'player_list_sample.txt' (rename to 'player_list.txt')")
    print("  - 'prevent_same_team_sample.txt' (rename to 'prevent_same_team.txt')")
    print("  - 'force_same_team_sample.txt' (rename to 'force_same_team.txt')")

def main():
    print("DOTA Team Balancer (Multi-Objective / Average / RMS lenses)")
    print("="*50)
    
    try:
        all_players, playing_players = read_players_from_file("player_list.txt")
        
        if not all_players:
            raise ValueError("No valid player data found in file")
        
        print(f"\nTotal players in list: {len(all_players)}")
        print(f"Players marked as playing: {len(playing_players)}")
        
        if not validate_player_count(playing_players):
            return
        
        print("\nPlayers being used for team balance:")
        for i, (name, mmr) in enumerate(playing_players, 1):
            print(f"  {i}. {name}: {mmr}")
        
        names = [name for name, _ in playing_players]
        if len(names) != len(set(names)):
            print("\nWARNING: Duplicate player names detected!")
            duplicates = [name for name in names if names.count(name) > 1]
            print(f"Duplicates: {', '.join(set(duplicates))}")
        
        # Read both restrictions and forced teams
        restrictions = read_team_restrictions("prevent_same_team.txt")
        forced_groups = read_force_same_team("force_same_team.txt")
        
        if restrictions:
            validate_restrictions(restrictions, playing_players)
        
        if forced_groups:
            validate_forced_teams(forced_groups, playing_players)
        
        # Check for conflicts between restrictions and forced teams
        if restrictions and forced_groups:
            for forced_group in forced_groups:
                for restricted_group in restrictions:
                    # Check if any two players are in both forced and restricted
                    common = set(forced_group) & set(restricted_group)
                    if len(common) >= 2:
                        print("\nWARNING: Conflict detected!")
                        print(f"Players {', '.join(common)} are both forced to be together AND restricted from being together!")
                        print("This will make it impossible to find valid teams.")
                        return
        
        try:
            all_assignments = evaluate_all_assignments(playing_players, restrictions, forced_groups)
        except ValueError as e:
            print(f"\nERROR: {e}")
            print("\nThe team restrictions and forced teams might be conflicting or too strict.")
            print("Consider relaxing some restrictions or forced team requirements.")
            return

        # Rank the same valid combinations under each lens
        lens_results = {
            lens['key']: top_by_lens(all_assignments, lens, top_n=3)
            for lens in LENSES
        }

        for lens in LENSES:
            top_assignments = lens_results[lens['key']]
            print("\n" + "="*50)
            print(f"TOP 3 BY {lens['title']}")
            if restrictions or forced_groups:
                print("(With team restrictions and forced teams applied)")
            print("="*50)

            for i, assignment in enumerate(top_assignments, 1):
                print_assignment(playing_players, assignment, i)

            if len(top_assignments) < 3:
                print(f"\nNote: Only {len(top_assignments)} valid team combinations found due to restrictions/forced teams")

        print("\n" + "="*50)
        print("Tip: the Multi-Objective lens (average gap, std tiebreaker) is the")
        print("recommended default. Average targets equal total strength; RMS")
        print("over-weights high-MMR players.")

        print("\n" + "="*50)
        save = input("\nSave results to file? (y/n): ").strip().lower()
        if save == 'y':
            valid_keys = [lens['key'] for lens in LENSES]
            lens_choice = input(f"Which lens to save? ({'/'.join(valid_keys)}/all): ").strip().lower()
            output_filename = input("Enter output filename (default: teams.txt): ").strip()
            if not output_filename:
                output_filename = "teams.txt"

            lenses_to_save = LENSES if lens_choice in ('all', '') else \
                [lens for lens in LENSES if lens['key'] == lens_choice]
            if not lenses_to_save:
                print(f"Unknown lens '{lens_choice}'. Saving all lenses by default.")
                lenses_to_save = LENSES

            try:
                with open(output_filename, 'w') as f:
                    f.write("DOTA TEAM ASSIGNMENTS\n")
                    if restrictions or forced_groups:
                        f.write("(With team restrictions and forced teams applied)\n")
                    f.write("="*50 + "\n")

                    for lens in lenses_to_save:
                        top_assignments = lens_results[lens['key']]
                        f.write(f"\nTOP {len(top_assignments)} BY {lens['title']}\n")
                        f.write("="*50 + "\n")
                        for i, assignment in enumerate(top_assignments, 1):
                            write_assignment_to_file(f, playing_players, assignment, i)
                            f.write("\n")
                        f.write("\n")

                print(f"\nResults saved to {output_filename}")
            except Exception as e:
                print(f"Error saving file: {str(e)}")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        create_sample = input("\nWould you like to create sample files? (y/n): ").strip().lower()
        if create_sample == 'y':
            create_sample_files()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nExpected files:")
        print("\n1. 'player_list.txt' with format:")
        print("   name,mmr,playing")
        print("   Alice,3000,yes")
        print("   Bob,3500,no")
        print("\n2. 'prevent_same_team.txt' (optional) with format:")
        print("   player1,player2,player3")
        print("   player4,player5")
        print("\n3. 'force_same_team.txt' (optional) with format:")
        print("   player1,player2")
        print("   player3,player4")

if __name__ == "__main__":
    main()