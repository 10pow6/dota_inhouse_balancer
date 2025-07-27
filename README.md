# DOTA Team Balancer

A Python tool that creates balanced DOTA 2 teams based on player MMR using the Root Mean Square (RMS) method, with support for player restrictions.

## Features

- **RMS-based balancing**: Uses quadratic mean for more accurate team balance
- **Multiple options**: Generates top 3 most balanced team configurations
- **Player restrictions**: Prevents specific players from being on the same team
- **Flexible player list**: Maintain a master list and mark who's playing each event
- **Error handling**: Comprehensive validation and helpful error messages
- **Export options**: Save results to file for easy sharing

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Installation

### Option 1: Download from GitHub (Recommended)
1. Visit the repository on GitHub
2. Click the green "Code" button and select "Download ZIP"
3. Extract the ZIP file to your desired location
4. You'll get all necessary files including sample files

### Option 2: Clone with Git
```bash
git clone <repository-url>
cd <repository-name>
```

### Option 3: Download Individual Files
1. Download `dota_team_balancer.py` from the repository
2. Create your player list file (see format below)
3. Optionally create team restrictions file

## Installing Python

### Windows

1. **Download Python**
   - Go to [python.org/downloads](https://python.org/downloads)
   - Click "Download Python 3.x.x" (latest version)
   - **Important**: Check ✅ "Add Python to PATH" during installation

2. **Verify Installation**
   - Open Command Prompt (Win+R, type `cmd`, press Enter)
   - Type: `python --version`
   - You should see: `Python 3.x.x`

### macOS

1. **Install Python** (if not already installed)
   - Option A: Download from [python.org/downloads](https://python.org/downloads)
   - Option B: Use Homebrew: `brew install python3`

2. **Verify Installation**
   - Open Terminal (Cmd+Space, type "Terminal")
   - Type: `python3 --version`
   - You should see: `Python 3.x.x`

### Linux

1. **Install Python** (usually pre-installed)
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3

   # Fedora
   sudo dnf install python3

   # Arch
   sudo pacman -S python
   ```

2. **Verify Installation**
   ```bash
   python3 --version
   ```

## First Time Setup

1. **Create your folder structure:**
   ```
   DotaBalancer/
   ├── dota_team_balancer.py
   ├── player_list.txt
   └── prevent_same_team.txt (optional)
   ```

2. **Test with sample data:**
   - Run the program once without files
   - When prompted, type `y` to create sample files
   - Rename samples: 
     - `player_list_sample.txt` → `player_list.txt`
     - `prevent_same_team_sample.txt` → `prevent_same_team.txt`

3. **Edit player_list.txt** with your players and set exactly 10 to "playing"

## Quick Start

1. **Navigate to your DotaBalancer folder:**
   ```bash
   # Windows
   cd C:\DotaBalancer
   
   # macOS/Linux
   cd ~/DotaBalancer
   ```

2. **Run the program:**
   ```bash
   # Windows
   python dota_team_balancer.py
   
   # macOS/Linux
   python3 dota_team_balancer.py
   ```

3. **Review the top 3 balanced team options**

4. **Choose to save results:**
   - Save a specific option (1, 2, or 3)
   - Save all options
   - Specify custom filename (default: teams.txt)

## File Formats

### player_list.txt (Required)
- **Format**: CSV with headers
- **Columns**: name, mmr, playing
- **Playing values**: yes/no, y/n, true/false, 1/0

Example:
```
name,mmr,playing
Alice,3000,yes
Bob,3500,no
Charlie,4000,yes
David,4500,yes
Eve,5000,yes
```

**Important**: Exactly 10 players must be marked as "playing"

### prevent_same_team.txt (Optional)
- **Format**: Comma-separated player names per line
- **Purpose**: Prevent certain players from being on the same team

Example:
```
Alice,Bob,Charlie
David,Eve
Frank,Grace,Henry
```

This means:
- Alice, Bob, and Charlie cannot all be on the same team
- David and Eve cannot be on the same team
- Frank, Grace, and Henry cannot all be on the same team

## Sample Files

The program can automatically create sample files for you:
- `player_list_sample.txt`: Example with 20 players (10 playing)
- `prevent_same_team_sample.txt`: Example restriction file

To create samples:
1. Run the program without any existing files
2. When prompted, type `y` to create sample files
3. Rename the samples to remove "_sample" from the filename

## How It Works

### RMS (Root Mean Square) Method
The program uses the quadratic mean formula to calculate team strength:
```
Team RMS = √[(MMR₁² + MMR₂² + MMR₃² + MMR₄² + MMR₅²) / 5]
```

This method gives slightly more weight to higher-skilled players compared to simple averaging, providing better balance.

### Algorithm
1. Reads all players marked as "playing" (must be exactly 10)
2. Generates all possible 5v5 team combinations (252 total)
3. Filters out combinations that violate team restrictions
4. Calculates RMS difference for each valid combination
5. Returns the top 3 most balanced options

## Sample Output
```
TOP 3 MOST BALANCED TEAM ASSIGNMENTS
==================================================

OPTION 1
==================================================
TEAM A:
  Jack: 5100
  Eve: 5000
  Henry: 4200
  Charlie: 4000
  Frank: 3200

Team A RMS: 4342.9
Team A Average: 4300.0

------------------------------

TEAM B:
  Ivy: 4700
  David: 4500
  Grace: 3800
  Alice: 3000
  Bob: 3500

Team B RMS: 4344.2
Team B Average: 3900.0

------------------------------
RMS Difference: 1.3
Average Difference: 400.0
```

## Error Handling

The program handles various error cases:
- Missing files (offers to create samples)
- Wrong number of players marked as playing
- Invalid MMR values
- Incorrect file formats
- Duplicate player names
- Invalid player restrictions
- Too restrictive team constraints

## Troubleshooting

**"python is not recognized" (Windows)**
- Python wasn't added to PATH during installation
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Python3x\python.exe dota_team_balancer.py`

**"No such file or directory"**
- Make sure you're in the correct folder
- Use `dir` (Windows) or `ls` (Mac/Linux) to list files
- Use `cd` to change directories

**Permission denied**
- Mac/Linux: Use `python3` instead of `python`
- Make file executable: `chmod +x dota_team_balancer.py`

**"Not enough players" error**
- Ensure exactly 10 players have playing = "yes"

**"No valid team combinations" error**
- Your restrictions may be too strict
- Try removing some restrictions

**File format errors**
- Check for correct number of columns (3)
- Ensure header row exists
- Verify MMR values are numbers

## Tips

1. **Player Pool**: Maintain a larger list of regular players and update the "playing" column for each event

2. **Restrictions**: Use team restrictions to:
   - Separate players who play the same role
   - Keep friends on different teams for variety
   - Prevent personality conflicts

3. **MMR Updates**: Keep MMR values current for best results

4. **Multiple Events**: Save different output files for tournament records

## License

This tool is provided as-is for personal and community use.

## Contributing

Feel free to suggest improvements or report issues!