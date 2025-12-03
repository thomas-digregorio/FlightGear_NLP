# FlightGear NLP Control MVP

A Python-based system that uses a lightweight local LLM to interpret natural language commands and control a FlightGear aircraft simulation.

## Features

- Natural language control of FlightGear aircraft via chat interface
- Small local LLM (TinyLlama 1.1B Chat) for command parsing
- HTTP-based communication with FlightGear (no telnet required)
- Support for commands: speed control, altitude control, direction changes, landing, status queries
- Aircraft starts in the air at 5000 feet (configurable)

## Prerequisites

- Python 3.8 or higher
- FlightGear installed and accessible from command line
- Sufficient RAM for running small LLM models (2-4GB recommended)

### Installing FlightGear

**Windows:**
1. Download FlightGear from: https://www.flightgear.org/download/
2. Install FlightGear (default location: `C:\Program Files\FlightGear\`)
3. Add FlightGear to your PATH, or use the full path to `fgfs.exe`
   - The executable is typically at: `C:\Program Files\FlightGear\bin\fgfs.exe`
   - Or: `C:\Program Files (x86)\FlightGear\bin\fgfs.exe`

**Alternative (if not in PATH):**
Instead of `fgfs`, use the full path:
```bash
"C:\Program Files\FlightGear\bin\fgfs.exe" --httpd=8080 --altitude=5000 --heading=090 --speed=150
```

**Linux/Mac:**
- Install via package manager or download from https://www.flightgear.org/download/
- On Linux: `sudo apt-get install flightgear` (Ubuntu/Debian) or `brew install flightgear` (Mac)

## Installation

1. Clone or download this repository

2. Create a conda environment (recommended):
   
   **Option A: Using environment.yml (easiest)**
   ```bash
   conda env create -f environment.yml
   conda activate flightgear-nlp
   ```
   
   **Option B: Manual conda setup**
   ```bash
   conda create -n flightgear-nlp python=3.10
   conda activate flightgear-nlp
   pip install -r requirements.txt
   ```
   
   **Option C: Using venv**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: If using conda, you may want to install PyTorch via conda for better compatibility:
   ```bash
   conda install pytorch -c pytorch
   pip install -r requirements.txt
   ```

## FlightGear Setup

Before running the Python application, start FlightGear with network interface enabled:

**Windows (Easiest - use the helper script):**
```bash
start_flightgear.bat
```
This script starts FlightGear with the plane already flying in the air at 5000 feet, heading 090, and speed 150 knots.

**Windows (Manual - if FlightGear is in your PATH):**
```bash
# Start in the air (recommended)
fgfs --httpd=8080 --altitude=5000 --heading=090 --speed=150

# Or start on the ground
fgfs --httpd=8080 --autostart
```

**Windows (Manual - if not in PATH):**
```bash
# Start in the air (recommended)
"C:\Program Files\FlightGear\bin\fgfs.exe" --httpd=8080 --altitude=5000 --heading=090 --speed=150

# Or start on the ground
"C:\Program Files\FlightGear\bin\fgfs.exe" --httpd=8080 --autostart
```

**Linux/Mac (if not in PATH):**
```bash
# Start in the air (recommended)
/path/to/fgfs --httpd=8080 --altitude=5000 --heading=090 --speed=150

# Or start on the ground
/path/to/fgfs --httpd=8080 --autostart
```

**Note:** You can customize the starting altitude, heading, and speed by changing the values:
- `--altitude=5000` - Starting altitude in feet (e.g., 10000 for 10,000 feet)
- `--heading=090` - Starting heading in degrees (000-360)
- `--speed=150` - Starting speed in knots

**Finding FlightGear on Windows:**
If you're not sure where FlightGear is installed, try:
```powershell
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "fgfs.exe" -ErrorAction SilentlyContinue
Get-ChildItem -Path "C:\Program Files (x86)" -Recurse -Filter "fgfs.exe" -ErrorAction SilentlyContinue
```

The application uses HTTP port 8080 to communicate with FlightGear.

## Usage

1. Start FlightGear with the network interface (see above)

2. Run the main application:
   ```bash
   python main.py
   ```

3. Type natural language commands in the chat interface:
   - "increase speed to 250 knots"
   - "increase altitude to 10000 feet"
   - "turn left 30 degrees"
   - "land the plane"
   - "what's my current speed?"

4. Type 'quit' or 'exit' to stop the application

## Example Commands

- **Speed control**: "increase speed to 250 knots", "slow down", "set speed to 200"
- **Altitude control**: "increase altitude to 10000 feet", "climb to 15000", "descend to 5000", "increase altitude by 2000"
- **Direction control**: "turn left 30 degrees", "head north", "change heading to 090"
- **Takeoff**: "take off", "takeoff", "launch"
- **Landing**: "land the plane", "initiate landing sequence"
- **Status**: "what's my speed?", "show status", "where am I?"
- **System**: "help" - Show all commands, "watch" - Real-time status monitor

## Project Structure

```
NLP_Scratch/
├── requirements.txt
├── environment.yml              # Conda environment file
├── README.md
├── start_flightgear.bat         # Windows helper script to start FlightGear
├── main.py                       # Entry point, chat interface
├── flightgear_controller_simple.py # FlightGear HTTP communication (using flightgear-python)
├── nlp_parser.py                 # LLM command parsing (TinyLlama 1.1B Chat)
├── command_executor.py           # Command execution logic
└── .gitignore
```

## Notes

- **Model**: Uses TinyLlama 1.1B Chat (TinyLlama/TinyLlama-1.1B-Chat-v1.0) from HuggingFace
- The first run will download the LLM model, which may take a few minutes (~2GB download)
- Model inference runs locally - no internet required after initial download
- FlightGear must be running before starting the Python application
- The application connects to FlightGear via HTTP on localhost:8080
- If LLM fails to load, the system will automatically fall back to rule-based parsing
- Aircraft starts in the air at 5000 feet by default (configurable in start_flightgear.bat)

## Troubleshooting

- **Connection refused / Cannot connect to FlightGear**: 
  - Make sure FlightGear is running with `--httpd=8080`
  - Check that port 8080 is not blocked by firewall
  - Verify FlightGear is listening: `netstat -an | findstr 8080` (Windows) or `netstat -an | grep 8080` (Linux/Mac)
  - Make sure you're using the `start_flightgear.bat` script or manually start with `fgfs --httpd=8080`

- **Model download issues**: 
  - Check internet connection for initial model download
  - Model (TinyLlama 1.1B Chat) will be cached in `~/.cache/huggingface/` after first download
  - If download fails, the system will use rule-based parsing as fallback
  - Model size: ~2GB

- **Slow response**: 
  - LLM inference may take 2-5 seconds depending on your hardware
  - CPU inference is slower than GPU - consider using CUDA if available
  - Rule-based parsing (fallback) is much faster but less flexible
  - TinyLlama is optimized for speed but may be slower on older CPUs

- **Import errors**: 
  - Make sure all dependencies are installed: `pip install -r requirements.txt`
  - Use Python 3.8 or higher
  - If `flightgear-python` fails to install, try: `pip install --upgrade flightgear-python`

- **Position/Altitude showing as 0**: 
  - This may indicate FlightGear property paths need adjustment
  - The system tries multiple property paths automatically
  - Check FlightGear is fully loaded before running the Python application

- **Commands not recognized**: 
  - The system uses TinyLlama 1.1B Chat for parsing - try rephrasing your command
  - Use the `help` command to see available command formats
  - Rule-based fallback handles common commands if LLM fails

