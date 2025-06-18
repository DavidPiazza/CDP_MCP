#!/usr/bin/env python3
"""
CDP MCP Server v7 - Ultra-Rigid Workflow
Direct CDP usage exposure with zero interpretation
Now with 4 core tools including data file creation
"""

import os
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import soundfile as sf
import numpy as np

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("CDP Sound Transformer v7")

# Configuration
CDP_PATH = os.environ.get("CDP_PATH", "/Users/davidpiazza/cdpr8/_cdp/_cdprogs")
TEMP_DIR = Path(tempfile.gettempdir()) / "cdp_mcp"
TEMP_DIR.mkdir(exist_ok=True)

# Detect if we're on Apple Silicon
IS_APPLE_SILICON = platform.machine() == "arm64" and platform.system() == "Darwin"

# CDP program categories for organization
CDP_CATEGORIES = {
    "Spectral Processing": [
        "blur", "clean", "combine", "cross", "focus", "formants", 
        "gate", "get", "hilite", "morph", "pitch", "spec", "strange", "stretch"
    ],
    "Time Domain": [
        "modify", "distort", "envel", "extend", "filter", "grain",
        "sfedit", "zigzag"
    ],
    "Synthesis": [
        "synth", "texture", "fracture"
    ],
    "Analysis and Utility": [
        "pvoc", "sndinfo", "housekeep", "submix", "mchshred"
    ],
    "Other": []  # For any programs not categorized
}

# ===== HELPER FUNCTIONS =====

def scan_cdp_programs() -> Dict[str, List[str]]:
    """Scan CDP installation directory for available programs"""
    cdp_dir = Path(CDP_PATH)
    if not cdp_dir.exists():
        return {"error": [f"CDP directory not found: {CDP_PATH}"]}
    
    # Get all executable files
    programs = []
    try:
        for file in cdp_dir.iterdir():
            if file.is_file() and os.access(file, os.X_OK):
                # Skip obvious non-CDP files
                name = file.name
                if not name.startswith('.') and not name.endswith('.txt'):
                    programs.append(name)
    except Exception as e:
        return {"error": [f"Failed to scan CDP directory: {str(e)}"]}
    
    # Categorize programs
    categorized = {cat: [] for cat in CDP_CATEGORIES}
    uncategorized = []
    
    for prog in sorted(programs):
        categorized_flag = False
        for category, prog_list in CDP_CATEGORIES.items():
            if prog in prog_list:
                categorized[category].append(prog)
                categorized_flag = True
                break
        if not categorized_flag:
            uncategorized.append(prog)
    
    # Add uncategorized to "Other"
    if uncategorized:
        categorized["Other"] = uncategorized
    
    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}
    
    return categorized

def run_cdp_for_usage(program: str, subprogram: Optional[str] = None) -> Tuple[int, str, str]:
    """Run CDP program without arguments to get usage information"""
    cmd_path = Path(CDP_PATH) / program
    if not cmd_path.exists():
        return -1, "", f"Program '{program}' not found at {cmd_path}"
    
    # Build command - just program and optional subprogram
    args = []
    if subprogram:
        args.append(subprogram)
    
    # Build command with architecture prefix if needed
    if IS_APPLE_SILICON:
        cmd = ["arch", "-x86_64", str(cmd_path)] + args
    else:
        cmd = [str(cmd_path)] + args
    
    try:
        # Run with no input, expecting usage output
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=5  # Prevent hanging
        )
        
        # CDP typically outputs usage to stdout or stderr
        # Exit code 255 is normal for usage display
        output = result.stdout if result.stdout else result.stderr
        
        return result.returncode, output, result.stderr
        
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out - program may be waiting for input"
    except Exception as e:
        return -1, "", f"Failed to execute: {str(e)}"

def run_cdp_command(command: List[str]) -> Tuple[int, str, str]:
    """Execute a CDP command given as array"""
    if not command:
        return -1, "", "Empty command array"
    
    program = command[0]
    cmd_path = Path(CDP_PATH) / program
    
    if not cmd_path.exists():
        return -1, "", f"Program '{program}' not found at {cmd_path}"
    
    # Build full command with architecture prefix if needed
    if IS_APPLE_SILICON:
        full_cmd = ["arch", "-x86_64", str(cmd_path)] + command[1:]
    else:
        full_cmd = [str(cmd_path)] + command[1:]
    
    # Log for debugging
    import sys
    print(f"Executing: {' '.join(full_cmd)}", file=sys.stderr)
    
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            cwd=TEMP_DIR  # Use temp dir as working directory
        )
        
        return result.returncode, result.stdout, result.stderr
        
    except Exception as e:
        return -1, "", f"Execution failed: {str(e)}"

def get_sound_info(filepath: str) -> Dict[str, Any]:
    """Get basic information about a sound file"""
    try:
        info = sf.info(filepath)
        data, _ = sf.read(filepath)
        
        return {
            "duration": info.duration,
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "peak_amplitude": float(np.max(np.abs(data))),
            "format": info.format,
            "frames": info.frames
        }
    except Exception as e:
        return {"error": str(e)}

# ===== CORE MCP TOOLS =====

@mcp.tool()
def list_cdp_programs() -> Dict[str, List[str]]:
    """
    List all available CDP programs organized by category.
    
    Returns:
        Dictionary with categories as keys and program lists as values
        
    Example response:
    {
        "Spectral Processing": ["blur", "focus", "morph", ...],
        "Time Domain": ["modify", "distort", "envel", ...],
        "Synthesis": ["synth", "texture"],
        "Analysis and Utility": ["pvoc", "housekeep", ...]
    }
    """
    return scan_cdp_programs()

@mcp.tool()
def get_cdp_usage(
    program: str,
    subprogram: Optional[str] = None
) -> Dict[str, str]:
    """
    Get usage information for a CDP program by running it without arguments.
    This returns the raw usage text directly from CDP.
    
    Args:
        program: CDP program name (e.g., 'blur', 'modify')
        subprogram: Optional subprogram (e.g., 'brassage' for modify)
        
    Returns:
        Dictionary with usage text and program info
        
    Example:
        get_cdp_usage('blur') 
        # Returns the full blur usage text showing all modes and parameters
        
        get_cdp_usage('modify', 'brassage')
        # Returns usage for modify brassage specifically
    """
    exit_code, output, stderr = run_cdp_for_usage(program, subprogram)
    
    # Build response
    response = {
        "program": program,
        "subprogram": subprogram or "none",
        "usage_text": output if output else stderr,
        "exit_code": exit_code
    }
    
    # Add hints based on common patterns
    if output or stderr:
        text = output if output else stderr
        
        # Check for common indicators
        if "USAGE:" in text or "Usage:" in text:
            response["has_usage"] = True
            
        if "MODES:" in text or "Modes:" in text:
            response["has_modes"] = True
            
        if any(flag in text for flag in ["-", "FLAGS:", "Options:"]):
            response["has_flags"] = True
            
        # Check for double syntax
        if f"{program} {program}" in text.lower():
            response["note"] = f"This program uses double syntax: {program} {program}"
    
    return response

@mcp.tool()
def execute_cdp(command: List[str]) -> Dict[str, Any]:
    """
    Execute a CDP command given as an array of strings.
    This is direct execution with no interpretation.
    
    Args:
        command: Complete command as array (e.g., ["blur", "blur", "in.ana", "out.ana", "50"])
        
    Returns:
        Execution result with status, output, and errors
        
    Examples:
        execute_cdp(["blur", "blur", "input.ana", "output.ana", "50"])
        execute_cdp(["modify", "speed", "1", "input.wav", "output.wav", "2.0"])
        execute_cdp(["housekeep", "chans", "4", "stereo.wav", "mono.wav"])
    """
    if not command:
        return {
            "status": "failed",
            "error": "Empty command array provided"
        }
    
    # Execute the command
    exit_code, stdout, stderr = run_cdp_command(command)
    
    # Determine success
    # CDP often returns non-zero codes even on success
    success = (
        exit_code == 0 or 
        (exit_code == 1 and stdout and not stderr) or
        (len(command) > 2 and Path(command[-1]).exists())  # Output file created
    )
    
    result = {
        "status": "success" if success else "failed",
        "exit_code": exit_code,
        "command": " ".join(command),
        "stdout": stdout if stdout else "",
        "stderr": stderr if stderr else ""
    }
    
    # Add output file info if it appears to be a file operation
    if len(command) > 2:
        possible_output = command[-1]
        if not possible_output.startswith('-') and '.' in possible_output:
            result["output_file"] = possible_output
            if Path(possible_output).exists():
                result["output_exists"] = True
    
    return result

@mcp.tool()
def create_data_file(
    filepath: str,
    content: str
) -> Dict[str, Any]:
    """
    Create a data file for CDP programs that require them.
    Data files are text files containing parameters specific to each CDP program.
    
    Args:
        filepath: Output path for the data file (should end in .txt)
        content: The exact text content to write to the file
        
    Returns:
        Dictionary with creation status and file path
        
    Examples:
        # For tesselate - two lines with repeat counts and delays
        create_data_file("tess_data.txt", "5 5 5 5\\n0.0 0.1 0.2 0.3")
        
        # For texture - note data with MIDI pitches and timing
        create_data_file("texture_notes.txt", "0.0 60 0.5 100\\n0.5 64 0.5 100")
        
        # For extend repetitions - times file
        create_data_file("times.txt", "0.0\\n1.5\\n3.2\\n4.8")
    """
    try:
        # Ensure filepath is absolute or relative to temp dir
        if not os.path.isabs(filepath):
            filepath = str(TEMP_DIR / filepath)
        
        # Write the content
        Path(filepath).write_text(content)
        
        # Verify it was created
        if Path(filepath).exists():
            lines = content.strip().split('\n')
            return {
                "status": "success",
                "filepath": filepath,
                "lines": len(lines),
                "size": len(content),
                "preview": content[:200] + "..." if len(content) > 200 else content
            }
        else:
            return {
                "status": "failed",
                "error": "File was not created"
            }
            
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Failed to create data file: {str(e)}"
        }

@mcp.tool()
def analyze_sound(filepath: str) -> Dict[str, Any]:
    """
    Analyze a sound file and return its properties.
    
    Args:
        filepath: Path to the sound file
        
    Returns:
        Dictionary with duration, sample_rate, channels, peak_amplitude, etc.
    """
    if not Path(filepath).exists():
        return {"error": f"File not found: {filepath}"}
        
    return get_sound_info(filepath)

@mcp.tool()
def prepare_spectral(
    input_file: str,
    output_file: str,
    window_size: int = 2048
) -> Dict[str, Any]:
    """
    Helper to prepare spectral file using PVOC analysis.
    This is a convenience wrapper around execute_cdp.
    
    Args:
        input_file: Input audio file path
        output_file: Output analysis file path (.ana)
        window_size: FFT window size (powers of 2: 64-8192)
        
    Returns:
        Result of PVOC analysis execution
    """
    # Check if input is already spectral
    if input_file.endswith('.ana'):
        return {
            "status": "info",
            "message": "Input is already a spectral file",
            "ana_file": input_file
        }
    
    # Check input file
    if not Path(input_file).exists():
        return {
            "status": "failed",
            "error": f"Input file not found: {input_file}"
        }
    
    # Build PVOC command
    command = [
        "pvoc", "anal", "1",
        input_file,
        output_file,
        f"-c{window_size}"
    ]
    
    # Execute
    result = execute_cdp(command)
    
    if result["status"] == "success":
        result["ana_file"] = output_file
        
    return result

# ===== RESOURCES =====

@mcp.resource("cdp://workflow")
def workflow_guide() -> str:
    """CDP v7 Workflow - Ultra-rigid approach"""
    return """# CDP MCP v7 - Ultra-Rigid Workflow

## The Core Process

### 1. List Available Programs
```python
programs = list_cdp_programs()
# Returns categorized list of all CDP programs
```

### 2. Get Usage for Selected Program
```python
usage = get_cdp_usage('blur')
# Returns exact CDP usage text - no interpretation!
```

### 3. Create Data Files if Needed
```python
# When usage mentions DATAFILE, create one:
create_data_file('data.txt', '5 5 5 5\\n0.0 0.1 0.2 0.3')
```

### 4. Execute Exact Command
```python
result = execute_cdp(['blur', 'blur', 'input.ana', 'output.ana', '50'])
# Direct execution of command array
```

## Why This Works

1. **No Parsing** - We don't interpret CDP's output
2. **No Guessing** - You see exactly what CDP shows
3. **Full Control** - You build the exact command array
4. **Simple Server** - Just four core tools, minimal code

## Example Workflow

```python
# User wants to blur a spectrum
# Step 1: Find blur program
programs = list_cdp_programs()
# See 'blur' in "Spectral Processing" category

# Step 2: Get blur usage
usage = get_cdp_usage('blur')
# Read CDP's exact usage text showing:
# "blur blur infile outfile blur"

# Step 3: Execute
result = execute_cdp(['blur', 'blur', 'input.ana', 'output.ana', '20'])
```

## Tips

- Always check usage before executing
- CDP exit codes can be non-zero even on success
- Check if output file exists to verify success
- Use exact command arrays - no interpretation

## Common Patterns

### Simple command:
```python
execute_cdp(['program', 'mode', 'infile', 'outfile', 'params...'])
```

### Compound program:
```python
execute_cdp(['program', 'subprogram', 'mode', 'infile', 'outfile', 'params...'])
```

### With flags:
```python
execute_cdp(['program', 'mode', 'infile', 'outfile', '-flag', 'value'])
```
"""

@mcp.resource("cdp://quickstart")
def quickstart_examples() -> str:
    """Quick examples for common CDP operations"""
    return """# CDP v7 Quick Start Examples

## Get Started in 3 Steps

### 1. See What's Available
```python
list_cdp_programs()
```

### 2. Learn How to Use It
```python
get_cdp_usage('modify', 'speed')
```

### 3. Execute It
```python
execute_cdp(['modify', 'speed', '1', 'input.wav', 'output.wav', '2.0'])
```

## Common Operations

### Time Stretch (Spectral)
```python
# Check usage
get_cdp_usage('stretch')

# Execute
execute_cdp(['stretch', 'time', '1', 'input.ana', 'output.ana', '2.0'])
```

### Spectral Blur
```python
# Check usage
get_cdp_usage('blur')

# Execute (note double syntax)
execute_cdp(['blur', 'blur', 'input.ana', 'output.ana', '50'])
```

### Granular Synthesis
```python
# Check usage
get_cdp_usage('modify', 'brassage')

# Execute
execute_cdp(['modify', 'brassage', '4', 'input.wav', 'output.wav', '0.02', '-0.5', '-r200'])
```

### Convert to Mono
```python
# Check usage
get_cdp_usage('housekeep', 'chans')

# Execute
execute_cdp(['housekeep', 'chans', '4', 'stereo.wav', 'mono.wav'])
```

### Spectral Analysis
```python
# Using helper
prepare_spectral('input.wav', 'output.ana', 2048)

# Or directly
execute_cdp(['pvoc', 'anal', '1', 'input.wav', 'output.ana', '-c2048'])
```

### Tesselate with Data File
```python
# Check usage
get_cdp_usage('tesselate')
# See it needs a DATAFILE with repeat counts and delays

# Create the data file
create_data_file('tess_data.txt', '5 5 5 5\\n0.0 0.1 0.2 0.3')

# Execute with data file
execute_cdp(['tesselate', 'tesselate', '1', 'in1.wav', 'in2.wav', 'in3.wav', 'in4.wav', 'output.wav', '0.5', 'tess_data.txt'])
```

## Remember

- Read usage first with get_cdp_usage()
- Create data files when usage mentions DATAFILE
- Build exact command arrays
- Check output file existence for success
- CDP may return non-zero exit codes even when successful
"""

if __name__ == "__main__":
    mcp.run()