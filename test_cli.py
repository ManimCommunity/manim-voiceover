import sys
import subprocess

print("Testing Manim CLI with --use-cloud-whisper flag")

# Run the manim command with our custom flag
cmd = ["manim", "--help"]
print(f"Running command: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

# Check if our flag is in the help output
if "--use-cloud-whisper" in result.stdout:
    print("✅ Success: --use-cloud-whisper flag is available in the help output")
else:
    print("❌ Error: --use-cloud-whisper flag is not available in the help output")
    print("Help output:")
    print(result.stdout)

# Try running the command with our flag
cmd = ["manim", "-pql", "--use-cloud-whisper", "examples/cloud_whisper_demo.py", "CloudWhisperDemo"]
print(f"\nRunning command: {' '.join(cmd)}")
print("(This will not actually run the command, just checking if the flag is recognized)")

# Just check if the flag is recognized, don't actually run the command
cmd = ["manim", "--use-cloud-whisper", "--help"]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Success: --use-cloud-whisper flag is recognized")
else:
    print("❌ Error: --use-cloud-whisper flag is not recognized")
    print("Error output:")
    print(result.stderr) 