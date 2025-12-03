# FlightGear NLP Control MVP

A Python-based system that uses a lightweight local LLM to interpret natural language commands and control a FlightGear aircraft simulation.

## Features

- Natural language control of FlightGear aircraft via chat interface
- Small local LLM (TinyLlama or Phi-2) for command parsing
- Real-time visualization of aircraft state and flight path
- Support for basic commands: speed control, direction changes, landing, status queries

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
"C:\Program Files\FlightGear\bin\fgfs.exe" --telnet=5500 --httpd=8080
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

**Windows (Manual - if FlightGear is in your PATH):**
```bash
fgfs --telnet=5500 --httpd=8080
```

**Windows (Manual - if not in PATH):**
```bash
"C:\Program Files\FlightGear\bin\fgfs.exe" --telnet=5500 --httpd=8080
```

**Linux/Mac (if not in PATH):**
```bash
/path/to/fgfs --telnet=5500 --httpd=8080
```

**Finding FlightGear on Windows:**
If you're not sure where FlightGear is installed, try:
```powershell
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "fgfs.exe" -ErrorAction SilentlyContinue
Get-ChildItem -Path "C:\Program Files (x86)" -Recurse -Filter "fgfs.exe" -ErrorAction SilentlyContinue
```

The default telnet port is 5500, which the application will use to communicate with FlightGear.

## Usage

1. Start FlightGear with the network interface (see above)

2. Run the main application:
   ```bash
   python main.py
   ```

3. Type natural language commands in the chat interface:
   - "increase speed to 250 knots"
   - "turn left 30 degrees"
   - "land the plane"
   - "what's my current speed?"

4. Type 'quit' or 'exit' to stop the application

## Example Commands

- **Speed control**: "increase speed to 250 knots", "slow down", "set speed to 200"
- **Direction control**: "turn left 30 degrees", "head north", "change heading to 090"
- **Landing**: "land the plane", "initiate landing sequence"
- **Status**: "what's my speed?", "show status", "where am I?"

## Project Structure

```
NLP_Scratch/
├── requirements.txt
├── environment.yml         # Conda environment file
├── README.md
├── start_flightgear.bat    # Windows helper script to start FlightGear
├── main.py                 # Entry point, chat interface
├── flightgear_controller.py # FlightGear communication
├── nlp_parser.py           # LLM command parsing
├── command_executor.py     # Command execution logic
├── visualizer.py           # Visualization utilities
└── .gitignore
```

## Notes

- The first run will download the LLM model (TinyLlama), which may take a few minutes (~2GB download)
- Model inference runs locally - no internet required after initial download
- FlightGear must be running before starting the Python application
- The application will attempt to connect to FlightGear on localhost:5500
- If LLM fails to load, the system will automatically fall back to rule-based parsing

## Troubleshooting

- **Connection refused**: 
  - Make sure FlightGear is running with `--telnet=5500`
  - Check that port 5500 is not blocked by firewall
  - Try: `netstat -an | findstr 5500` (Windows) or `netstat -an | grep 5500` (Linux/Mac) to verify FlightGear is listening

- **Model download issues**: 
  - Check internet connection for initial model download
  - Model will be cached in `~/.cache/huggingface/` after first download
  - If download fails, the system will use rule-based parsing as fallback

- **Slow response**: 
  - LLM inference may take 2-5 seconds depending on your hardware
  - CPU inference is slower than GPU - consider using CUDA if available
  - Rule-based parsing (fallback) is much faster but less flexible

- **Import errors**: 
  - Make sure all dependencies are installed: `pip install -r requirements.txt`
  - Use Python 3.8 or higher

- **Visualization not showing**: 
  - Make sure matplotlib backend is properly configured
  - On some systems, you may need: `export MPLBACKEND=TkAgg` (Linux/Mac)

