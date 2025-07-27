import itertools
import math
import csv
import sys

def calculate_rms(team_mmrs):
    """Calculate Root Mean Square (Quadratic Mean) for a team"""
    return math.sqrt(sum(mmr**2 for mmr in team_mmrs) / len(team_mmrs))

def read_team_restrictions(filename="prevent_same_team.txt"):
    """Read team restrictions from file"""
    restrictions = []
    
    # If file doesn't exist, return empty restrictions
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Split by comma and clean up names
                players = [p.strip() for p in line.split(',')]
                
                # Filter out empty strings
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
        # File is optional, so just return empty list
        return []
    except Exception as e:
        print(f"Warning: Error reading {filename}: {str(e)}")
        return []

def check_team_validity(team_indices, player_names, restrictions):
    """Check if a team composition violates any restrictions"""
    # Get the names of players in this team
    team_names = [player_names[i] for i in team_indices]
    
    # Check each restriction
    for restricted_group in restrictions:
        # Count how many restricted players are in this team
        count = sum(1 for player in restricted_group if player in team_names)
        
        # If 2 or more players from a restricted group are on the same team, it's invalid
        if count >= 2:
            return False
    
    return True

def find_best_team_assignments(players_mmr, restrictions=None, top_n=3):
    """Find the top N most balanced team assignments using RMS with restrictions"""
    n = len(players_mmr)
    player_names = [p[0] for p in players_mmr]
    
    # Generate all possible combinations of 5 players for team A
    all_combinations = itertools.combinations(range(n), 5)
    
    # Store all valid assignments with their differences
    assignments = []
    invalid_count = 0
    
    for team_a_indices in all_combinations:
        # Get team B indices (remaining players)
        team_b_indices = tuple(i for i in range(n) if i not in team_a_indices)
        
        # Check if both teams are valid according to restrictions
        if restrictions:
            team_a_valid = check_team_validity(team_a_indices, player_names, restrictions)
            team_b_valid = check_team_validity(team_b_indices, player_names, restrictions)
            
            if not (team_a_valid and team_b_valid):
                invalid_count += 1
                continue
        
        # Get MMRs for each team
        team_a_mmrs = [players_mmr[i][1] for i in team_a_indices]
        team_b_mmrs = [players_mmr[i][1] for i in team_b_indices]
        
        # Calculate RMS for each team
        rms_a = calculate_rms(team_a_mmrs)
        rms_b = calculate_rms(team_b_mmrs)
        
        # Calculate difference
        difference = abs(rms_a - rms_b)
        
        assignments.append({
            'team_a_indices': team_a_indices,
            'team_b_indices': team_b_indices,
            'difference': difference,
            'rms_a': rms_a,
            'rms_b': rms_b
        })
    
    if invalid_count > 0:
        print(f"\nFiltered out {invalid_count} team combinations due to restrictions")
        print(f"Valid combinations remaining: {len(assignments)}")
    
    if not assignments:
        raise ValueError("No valid team combinations found with the given restrictions!")
    
    # Sort by difference and return top N
    assignments.sort(key=lambda x: x['difference'])
    return assignments[:min(top_n, len(assignments))]

def read_players_from_file(filename="player_list.txt"):
    """Read players from a CSV file with headers: name,mmr,playing"""
    all_players = []
    playing_players = []
    errors = []
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
            lines = file.readlines()
            
            if not lines:
                raise ValueError("File is empty")
            
            # Check first line for header
            first_line = lines[0].strip()
            start_line = 0
            
            # Detect if first line is header
            if 'name' in first_line.lower() or 'mmr' in first_line.lower():
                start_line = 1
            else:
                # Check if first line has non-numeric MMR value (likely header)
                parts = first_line.split(',')
                if len(parts) >= 2:
                    try:
                        int(parts[1].strip())
                    except ValueError:
                        start_line = 1
            
            # Process data lines
            for line_num, line in enumerate(lines[start_line:], start_line + 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Try different delimiters
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
                
                # Parse player data
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
                        # Still process but warn
                except ValueError:
                    errors.append(f"Line {line_num}: MMR must be a number, got: '{parts[1].strip()}'")
                    continue
                
                playing_status = parts[2].strip().lower()
                is_playing = playing_status in ['yes', 'y', 'true', '1']
                
                # Check for invalid playing status
                if playing_status not in ['yes', 'y', 'true', '1', 'no', 'n', 'false', '0']:
                    errors.append(f"Line {line_num}: Invalid playing status '{parts[2].strip()}'. Use yes/no, y/n, true/false, or 1/0")
                    continue
                
                # Store player
                all_players.append({
                    'name': player_name,
                    'mmr': mmr,
                    'playing': is_playing
                })
                
                if is_playing:
                    playing_players.append((player_name, mmr))
            
            # Report any errors found
            if errors:
                print("\nWarnings/Errors found while reading file:")
                for error in errors[:5]:  # Show first 5 errors
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

def print_assignment(players_data, assignment, option_num):
    """Print a single team assignment"""
    team_a = [players_data[i] for i in assignment['team_a_indices']]
    team_b = [players_data[i] for i in assignment['team_b_indices']]
    
    # Calculate team statistics
    team_a_mmrs = [player[1] for player in team_a]
    team_b_mmrs = [player[1] for player in team_b]
    
    avg_a = sum(team_a_mmrs) / 5
    avg_b = sum(team_b_mmrs) / 5
    
    print(f"\n{'='*50}")
    print(f"OPTION {option_num}")
    print(f"{'='*50}")
    
    print("\nTEAM A:")
    for player, mmr in sorted(team_a, key=lambda x: x[1], reverse=True):
        print(f"  {player}: {mmr}")
    print(f"\nTeam A RMS: {assignment['rms_a']:.1f}")
    print(f"Team A Average: {avg_a:.1f}")
    
    print("\n" + "-"*30)
    
    print("\nTEAM B:")
    for player, mmr in sorted(team_b, key=lambda x: x[1], reverse=True):
        print(f"  {player}: {mmr}")
    print(f"\nTeam B RMS: {assignment['rms_b']:.1f}")
    print(f"Team B Average: {avg_b:.1f}")
    
    print("\n" + "-"*30)
    print(f"RMS Difference: {assignment['difference']:.1f}")
    print(f"Average Difference: {abs(avg_a - avg_b):.1f}")

def write_assignment_to_file(file, players_data, assignment, option_num):
    """Write a single assignment to file"""
    team_a = [players_data[i] for i in assignment['team_a_indices']]
    team_b = [players_data[i] for i in assignment['team_b_indices']]
    
    team_a_mmrs = [player[1] for player in team_a]
    team_b_mmrs = [player[1] for player in team_b]
    
    avg_a = sum(team_a_mmrs) / 5
    avg_b = sum(team_b_mmrs) / 5
    
    file.write(f"\nOPTION {option_num}\n")
    file.write("="*50 + "\n\n")
    
    file.write("TEAM A:\n")
    for player, mmr in sorted(team_a, key=lambda x: x[1], reverse=True):
        file.write(f"  {player}: {mmr}\n")
    file.write(f"\nTeam A RMS: {assignment['rms_a']:.1f}\n")
    file.write(f"Team A Average: {avg_a:.1f}\n")
    
    file.write("\n" + "-"*30 + "\n\n")
    
    file.write("TEAM B:\n")
    for player, mmr in sorted(team_b, key=lambda x: x[1], reverse=True):
        file.write(f"  {player}: {mmr}\n")
    file.write(f"\nTeam B RMS: {assignment['rms_b']:.1f}\n")
    file.write(f"Team B Average: {avg_b:.1f}\n")
    
    file.write("\n" + "-"*30 + "\n")
    file.write(f"RMS Difference: {assignment['difference']:.1f}\n")
    file.write(f"Average Difference: {abs(avg_a - avg_b):.1f}\n")

def create_sample_files():
    """Create sample files"""
    # Create player_list.txt sample
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
    
    # Create prevent_same_team.txt sample
    prevent_content = """Alice,Bob,Charlie
David,Eve
Frank,Grace,Henry
"""
    with open("prevent_same_team_sample.txt", "w") as f:
        f.write(prevent_content)
    
    print("Created sample files:")
    print("  - 'player_list_sample.txt' (rename to 'player_list.txt')")
    print("  - 'prevent_same_team_sample.txt' (rename to 'prevent_same_team.txt')")

def main():
    print("DOTA Team Balancer (RMS Method)")
    print("="*50)
    
    try:
        # Read players from file
        all_players, playing_players = read_players_from_file("player_list.txt")
        
        # Check if we got any valid data
        if not all_players:
            raise ValueError("No valid player data found in file")
        
        print(f"\nTotal players in list: {len(all_players)}")
        print(f"Players marked as playing: {len(playing_players)}")
        
        # Validate player count
        if not validate_player_count(playing_players):
            return
        
        print("\nPlayers being used for team balance:")
        for i, (name, mmr) in enumerate(playing_players, 1):
            print(f"  {i}. {name}: {mmr}")
        
        # Check for duplicate names
        names = [name for name, _ in playing_players]
        if len(names) != len(set(names)):
            print("\nWARNING: Duplicate player names detected!")
            duplicates = [name for name in names if names.count(name) > 1]
            print(f"Duplicates: {', '.join(set(duplicates))}")
        
        # Read team restrictions
        restrictions = read_team_restrictions("prevent_same_team.txt")
        
        # Validate restrictions against playing players
        if restrictions:
            validate_restrictions(restrictions, playing_players)
        
        # Find top 3 best assignments with restrictions
        try:
            top_assignments = find_best_team_assignments(playing_players, restrictions, top_n=3)
        except ValueError as e:
            print(f"\nERROR: {e}")
            print("\nThe team restrictions might be too strict. Consider relaxing some restrictions.")
            return
        
        print("\n" + "="*50)
        print("TOP 3 MOST BALANCED TEAM ASSIGNMENTS")
        if restrictions:
            print("(With team restrictions applied)")
        print("="*50)
        
        # Display all options (might be less than 3 if restrictions are tight)
        for i, assignment in enumerate(top_assignments, 1):
            print_assignment(playing_players, assignment, i)
        
        if len(top_assignments) < 3:
            print(f"\nNote: Only {len(top_assignments)} valid team combinations found due to restrictions")
        
        # Let user choose which option to save
        print("\n" + "="*50)
        save = input("\nSave results to file? (y/n): ").strip().lower()
        if save == 'y':
            option = input("Which option to save? (1/2/3/all): ").strip().lower()
            output_filename = input("Enter output filename (default: teams.txt): ").strip()
            if not output_filename:
                output_filename = "teams.txt"
            
            try:
                with open(output_filename, 'w') as f:
                    f.write("DOTA TEAM ASSIGNMENTS\n")
                    if restrictions:
                        f.write("(With team restrictions applied)\n")
                    f.write("="*50 + "\n")
                    
                    if option == 'all':
                        for i, assignment in enumerate(top_assignments, 1):
                            write_assignment_to_file(f, playing_players, assignment, i)
                            if i < len(top_assignments):
                                f.write("\n\n")
                    elif option in ['1', '2', '3']:
                        idx = int(option) - 1
                        if idx < len(top_assignments):
                            write_assignment_to_file(f, playing_players, top_assignments[idx], int(option))
                        else:
                            print(f"Option {option} not available. Saving Option 1.")
                            write_assignment_to_file(f, playing_players, top_assignments[0], 1)
                    else:
                        print("Invalid option. Saving Option 1 by default.")
                        write_assignment_to_file(f, playing_players, top_assignments[0], 1)
                
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

if __name__ == "__main__":
    main()