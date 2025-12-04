# FlightGear NLP Control System

A Python-based system that uses voice commands and AI models to control FlightGear aircraft simulation in real-time. Features natural language understanding with dialogue state tracking and optimized inference for edge devices.

## Features

- **Voice-Controlled Interface**: Speak commands using OpenAI Whisper (tiny model) with push-to-talk (hold SPACEBAR)
- **Natural Language Understanding**: TinyLlama 1.1B Chat model for parsing voice commands into structured intents
- **Dialogue State Tracking (DST)**: Maintains conversation context across multiple turns
  - Remembers previous commands and parameters
  - Handles corrections and updates (e.g., "actually, make it 6000")
  - Resolves coreferences (pronouns like "it", "there", "that")
  - Fills missing parameters from previous turns
- **Model Optimizations**: 
  - INT8 quantization for CPU inference (4× memory reduction, 2-3× speedup)
  - Optimized generation settings (greedy decoding, reduced tokens)
  - FP16 support on GPU for faster inference
- **HTTP-based Communication**: Direct FlightGear control via HTTP (no telnet required)
- **Real-time Status Monitoring**: Live aircraft state display
- **Support for Commands**: Speed control, altitude control, direction changes, takeoff, landing, status queries

## Prerequisites

- Python 3.8 or higher
- FlightGear installed and accessible from command line
- Microphone for voice input
- Sufficient RAM for running AI models:
  - **Minimum**: 4GB RAM (CPU inference)
  - **Recommended**: 8GB+ RAM with NVIDIA GPU (CUDA) for best performance

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

3. **Voice Input Mode**: The system uses voice commands only (no typing)
   - **Hold SPACEBAR** to start recording
   - **Speak your command** while holding SPACEBAR
   - **Release SPACEBAR** when done speaking
   - The system will transcribe and process your command

4. Example voice commands:
   - "increase speed to 250 knots"
   - "increase altitude to 10000 feet"
   - "turn left 30 degrees"
   - "land the plane"
   - "what's my current speed?"

5. Say 'quit' or 'exit' to stop the application

## Example Commands

- **Speed control**: "increase speed to 250 knots", "slow down", "set speed to 200"
- **Altitude control**: "increase altitude to 10000 feet", "climb to 15000", "descend to 5000", "increase altitude by 2000"
- **Direction control**: "turn left 30 degrees", "head north", "change heading to 090"
- **Takeoff**: "take off", "takeoff", "launch"
- **Landing**: "land the plane", "initiate landing sequence"
- **Status**: "what's my speed?", "show status", "where am I?"
- **System**: "help" - Show all commands, "watch" - Real-time status monitor, "reset" - Clear conversation state

## Multi-Turn Conversations (Dialogue State Tracking)

The system maintains conversation context, enabling natural multi-turn interactions:

**Corrections and Updates:**
- User: "Set altitude to 5000 feet"
- User: "Actually, make it 6000" → System remembers the altitude command and updates to 6000

**Parameter Completion:**
- User: "I want to change altitude"
- User: "to 10000 feet" → System combines the intent from turn 1 with parameter from turn 2

**Coreference Resolution:**
- User: "Take off and circle Alpha point"
- User: "Now land it there" → System understands "it" refers to the aircraft and "there" refers to Alpha point

**Context-Aware Commands:**
- User: "Increase speed to 250 knots"
- User: "Now turn left 30 degrees" → System maintains context of previous commands

To reset the conversation state, say `reset`, `clear`, or `new conversation`.

## Model Optimizations

The system includes several optimizations for faster inference:

- **INT8 Quantization**: TinyLlama model is quantized to INT8 on CPU (4× memory reduction, 2-3× speedup)
- **Optimized Generation**: Reduced token generation (75 tokens max) and greedy decoding for faster inference
- **FP16 Support**: Automatic FP16 on GPU for faster inference
- **Whisper Tiny**: Uses the smallest Whisper model for fast speech recognition

**Performance Targets:**
- Whisper transcription: ~150-500ms (depending on hardware)
- TinyLlama inference: ~50-200ms (CPU with quantization) or ~20-50ms (GPU with FP16)
- Total end-to-end latency: <1 second on modern hardware

## Project Structure

```
FlightGear_NLP/
├── requirements.txt              # Python dependencies
├── environment.yml               # Conda environment file
├── README.md                     # This file
├── start_flightgear.bat          # Windows helper script to start FlightGear
├── main.py                       # Entry point, voice interface
├── flightgear_controller_simple.py # FlightGear HTTP communication
├── nlp_parser.py                 # LLM command parsing (TinyLlama 1.1B Chat)
├── command_executor.py           # Command execution logic
├── dialogue_state_tracker.py     # Dialogue state tracking and context management
└── voice_input.py                # Voice input handler (Whisper ASR)
```

## Technical Details

### Models Used

- **TinyLlama 1.1B Chat**: Natural language understanding model (~2GB, quantized to ~500MB on CPU)
  - Location: `~/.cache/huggingface/` after first download
  - Optimizations: INT8 quantization (CPU), FP16 (GPU), greedy decoding, reduced tokens
  
- **Whisper Tiny**: Speech recognition model (~75MB)
  - Location: `~/.cache/whisper/` after first download
  - Optimizations: FP32 on CPU, FP16 on GPU

### Inference Pipeline

1. **Voice Input**: User holds SPACEBAR and speaks → Audio recorded
2. **Speech Recognition**: Whisper transcribes audio to text
3. **Dialogue State**: System retrieves conversation context
4. **NLU Parsing**: TinyLlama parses text + context → Structured intent
5. **State Update**: Dialogue state tracker updates with new information
6. **Command Execution**: Command executor sends control signals to FlightGear
7. **Response**: System displays result and updated aircraft state

### Performance Notes

- **First Run**: Models will be downloaded automatically (~2GB total)
- **Model Inference**: Runs locally - no internet required after initial download
- **CPU vs GPU**: GPU (CUDA) provides 3-5× speedup for both models
- **Quantization**: INT8 quantization on CPU provides 2-3× speedup with minimal accuracy loss
- **Fallback**: If LLM fails to load, system automatically falls back to rule-based parsing

## Troubleshooting

### Connection Issues

- **Connection refused / Cannot connect to FlightGear**: 
  - Make sure FlightGear is running with `--httpd=8080`
  - Check that port 8080 is not blocked by firewall
  - Verify FlightGear is listening: `netstat -an | findstr 8080` (Windows) or `netstat -an | grep 8080` (Linux/Mac)
  - Make sure you're using the `start_flightgear.bat` script or manually start with `fgfs --httpd=8080`

### Model Issues

- **Model download issues**: 
  - Check internet connection for initial model download
  - Models will be cached in `~/.cache/huggingface/` and `~/.cache/whisper/` after first download
  - If download fails, the system will use rule-based parsing as fallback
  - Model sizes: TinyLlama ~2GB, Whisper tiny ~75MB

- **Slow response**: 
  - LLM inference may take 2-5 seconds on CPU, <1 second on GPU
  - CPU inference is slower than GPU - consider using CUDA if available
  - Quantization helps significantly on CPU (2-3× speedup)
  - Rule-based parsing (fallback) is much faster but less flexible

- **Import errors**: 
  - Make sure all dependencies are installed: `pip install -r requirements.txt`
  - Use Python 3.8 or higher
  - If `flightgear-python` fails to install, try: `pip install --upgrade flightgear-python`
  - If `whisper` fails, ensure you have `ffmpeg` installed (required for audio processing)

### Voice Input Issues

- **Microphone not detected**:
  - Ensure microphone is connected and working
  - Check microphone permissions in system settings
  - Try a different microphone if available

- **No audio recorded**:
  - Check microphone volume levels
  - Ensure you're holding SPACEBAR long enough (>300ms)
  - Try speaking louder or closer to microphone

- **Poor transcription accuracy**:
  - Speak clearly and at moderate pace
  - Reduce background noise
  - Ensure good microphone quality

### FlightGear Issues

- **Position/Altitude showing as 0**: 
  - This may indicate FlightGear property paths need adjustment
  - The system tries multiple property paths automatically
  - Check FlightGear is fully loaded before running the Python application

- **Commands not recognized**: 
  - The system uses TinyLlama for parsing - try rephrasing your command
  - Say "help" to see available command formats
  - Rule-based fallback handles common commands if LLM fails

## License

This project is provided as-is for educational and research purposes.
