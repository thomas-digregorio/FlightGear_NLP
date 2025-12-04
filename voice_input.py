"""
Voice Input Module

Handles voice input using OpenAI Whisper (tiny model) with push-to-talk functionality.
Users hold the spacebar to record audio, which is then transcribed.
"""

import whisper
import sounddevice as sd
import numpy as np
import keyboard
import threading
import queue
import time
import warnings
from typing import Optional


class VoiceInputHandler:
    """Handles voice input with push-to-talk (spacebar) functionality."""
    
    def __init__(self, model_size="tiny", sample_rate=16000, channels=1):
        """
        Initialize voice input handler.
        
        Args:
            model_size: Whisper model size (default: "tiny" for speed)
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.model = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_thread = None
        
        print(f"Loading Whisper model ({model_size})...")
        try:
            # Load model - Whisper will automatically use FP32 on CPU, FP16 on GPU
            # We can explicitly set device to avoid warnings
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(model_size, device=device)
            
            if device == "cpu":
                print("Whisper model loaded on CPU (using FP32)")
            else:
                print("Whisper model loaded on GPU (using FP16)")
            print("Whisper model loaded successfully!")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            raise
    
    def _check_microphone(self):
        """Check if microphone is available."""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                raise RuntimeError("No microphone found. Please connect a microphone.")
            return True
        except Exception as e:
            raise RuntimeError(f"Error checking microphone: {e}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio recording."""
        if status:
            print(f"Audio callback status: {status}")
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def _record_audio_stream(self):
        """Record audio stream in a separate thread."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=1024
            ):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error in audio stream: {e}")
    
    def record_while_spacebar_held(self) -> Optional[np.ndarray]:
        """
        Record audio while spacebar is held down.
        
        Returns:
            Recorded audio as numpy array, or None if recording failed
        """
        self._check_microphone()
        
        audio_frames = []
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_audio_stream, daemon=True)
        self.recording_thread.start()
        
        print("Recording... (release SPACEBAR when done)", end="", flush=True)
        
        # Wait while spacebar is held
        try:
            while keyboard.is_pressed('space'):
                time.sleep(0.05)  # Small delay to avoid CPU spinning
                # Collect audio frames
                while not self.audio_queue.empty():
                    audio_frames.append(self.audio_queue.get())
        except KeyboardInterrupt:
            pass
        finally:
            # Stop recording
            self.is_recording = False
            time.sleep(0.2)  # Give thread time to finish
            
            if audio_frames:
                # Concatenate all audio frames
                audio_data = np.concatenate(audio_frames, axis=0)
                print()  # New line after "Recording..." message
                return audio_data
            else:
                print()  # New line
                return None
    
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text, or None if transcription failed
        """
        if audio_data is None or len(audio_data) == 0:
            return None
        
        try:
            # Ensure audio is in the right format (mono, float32)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe with FP32 on CPU (suppress FP16 warning)
            # Whisper will automatically use FP32 on CPU, but shows a warning we can ignore
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
                result = self.model.transcribe(audio_data, language="en", fp16=False)
            text = result["text"].strip()
            
            return text if text else None
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def get_voice_command(self) -> str:
        """
        Main method to get voice command from user.
        Waits for spacebar to be held, records audio, and transcribes it.
        
        Returns:
            Transcribed text command
        """
        print("\nHold SPACEBAR to speak...", end="", flush=True)
        
        # Wait for spacebar to be pressed and held
        try:
            # Wait for spacebar press
            keyboard.wait('space')
            # Small delay to ensure spacebar is actually held
            time.sleep(0.1)
            
            # Only proceed if spacebar is still being held
            if not keyboard.is_pressed('space'):
                return ""
        except KeyboardInterrupt:
            return ""
        except Exception as e:
            print(f"\nError waiting for spacebar: {e}")
            return ""
        
        # Record while spacebar is held
        audio_data = self.record_while_spacebar_held()
        
        if audio_data is None or len(audio_data) == 0:
            print("No audio recorded. Please try again.")
            return ""
        
        # Check if audio is too short (likely noise or accidental press)
        duration = len(audio_data) / self.sample_rate
        if duration < 0.3:  # Less than 300ms
            print("Recording too short. Please try again.")
            return ""
        
        # Transcribe
        print("Transcribing...", end="", flush=True)
        transcribed_text = self.transcribe_audio(audio_data)
        print()  # New line
        
        if transcribed_text:
            print(f"You said: {transcribed_text}")
            return transcribed_text
        else:
            print("Could not transcribe audio. Please try again.")
            return ""

