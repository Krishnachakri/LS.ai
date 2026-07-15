import sys
import os
import time

# Ensure backend root is in python path for local app imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.speech_transcriber import SpeechTranscriberService

def run_test():
    if len(sys.argv) < 2:
        print("Usage: python test_speech_transcriber.py <path_to_audio_file>")
        sys.exit(1)
        
    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print(f"Error: File '{audio_path}' does not exist.")
        sys.exit(1)
        
    print(f"[*] Initializing Speech Transcriber Service...")
    try:
        service = SpeechTranscriberService()
        
        print(f"[*] Processing audio file: {os.path.basename(audio_path)}...")
        start_time = time.time()
        
        result = service.transcribe(audio_path)
        
        elapsed = time.time() - start_time
        print("\n==========================================")
        print("    SPEECH TRANSCRIBER TEST RESULTS       ")
        print("==========================================")
        print(f"Target File:      {os.path.basename(audio_path)}")
        print(f"Processing Time:  {elapsed:.3f} seconds")
        print(f"Detected Lang:    {result['language']}")
        print(f"Transcript:")
        print(f"\"{result['transcript']}\"")
        print("==========================================\n")
        
    except Exception as e:
        print(f"[!] Test Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_test()
