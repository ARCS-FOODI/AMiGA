import cv2
import os
import sys
import glob

# This script is an interactive utility to generate videos from captured sessions.
# Usage: python3 timelapse_processor.py

def list_sessions(base_dir="recordings"):
    """
    Scans the recordings folder and returns a list of session directories.
    """
    if not os.path.exists(base_dir):
        return []
    
    # Identify all subdirectories in recordings/
    sessions = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    # Sort YYYYMMDD_HHMMSS folders so newest are first
    sessions.sort(reverse=True)
    return sessions

def create_timelapse(image_folder, pattern, output_name, fps=30):
    """
    Stitches images matching a pattern into an MKV video.
    """
    images = sorted(glob.glob(os.path.join(image_folder, pattern)))
    
    if not images:
        print(f"   [SKIP] No images found matching: {pattern}")
        return

    # Initialize VideoWriter using dimensions from the first image
    first_frame = cv2.imread(images[0])
    if first_frame is None:
        return
        
    height, width, _ = first_frame.shape
    
    # Output file will be placed in the parent 'recordings' folder
    parent_dir = os.path.dirname(image_folder)
    output_path = os.path.join(parent_dir, output_name)
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"   [PROCESSING] Building {output_name} ({len(images)} frames)...")
    
    for i, image_path in enumerate(images):
        frame = cv2.imread(image_path)
        if frame is not None:
            video.write(frame)
        
        if (i + 1) % 100 == 0:
            print(f"      - {i + 1} frames processed...")

    video.release()
    print(f"   [SUCCESS] Saved: {output_path}")

if __name__ == "__main__":
    print("\n" + "="*40)
    print("   MOISTURE TIMELAPSE PROCESSOR")
    print("="*40)
    
    sessions = list_sessions()
    
    if not sessions:
        print("\n[!] No sessions found in 'recordings/'.")
        print("    Run moisture_tracker.py first to capture data.")
        sys.exit(0)

    print("\n--- Available Sessions (Newest First) ---")
    for i, s in enumerate(sessions):
        print(f"  [{i+1}] {s}")

    try:
        prompt = f"\nSelect a session to process (1-{len(sessions)}) or 'q' to quit: "
        choice = input(prompt).strip()
        
        if choice.lower() == 'q':
            print("Exiting.")
            sys.exit(0)
            
        selection_idx = int(choice) - 1
        if selection_idx < 0 or selection_idx >= len(sessions):
            print("[!] Invalid selection.")
            sys.exit(1)
            
        session_name = sessions[selection_idx]
        selected_path = os.path.join("recordings", session_name)
        
        print(f"\n--- GENERATING TIMELAPSES FOR: {session_name} ---")

        # Generate separate videos for Raw IR and Heatmap
        # 30 FPS means 1 second of video = 30 seconds of real-time monitoring
        create_timelapse(selected_path, "*_raw.jpg", f"{session_name}_raw_timelapse.mkv", fps=30)
        create_timelapse(selected_path, "*_heat.jpg", f"{session_name}_heat_timelapse.mkv", fps=30)
        
        print("\n[COMPLETE] Both time-lapse videos are ready in the 'recordings/' folder.")
        
    except ValueError:
        print("[!] Input must be a number.")
    except KeyboardInterrupt:
        print("\nGeneration cancelled.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected issue occurred: {e}")

