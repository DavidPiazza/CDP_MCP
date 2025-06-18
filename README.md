# CDP MCP Server

A Model Context Protocol (MCP) server that provides direct access to the Composers' Desktop Project (CDP) sound transformation programs. This server offers an ultra-rigid workflow with zero interpretation, exposing CDP's raw functionality through simple, reliable tools.

## Overview

CDP MCP Server v7 implements a minimalist approach to CDP integration:
- **Direct execution** - No command parsing or interpretation
- **Raw usage text** - See exactly what CDP shows
- **Simple tools** - Just 6 core functions
- **Data file support** - Create parameter files for complex operations

## Features

- 🎵 **Full CDP Access** - Execute any CDP program with complete control
- 📚 **Program Discovery** - List all available CDP programs by category
- 📖 **Usage Information** - Get raw usage text directly from CDP
- 📄 **Data File Creation** - Create parameter files required by CDP programs
- 🎛️ **Spectral Preparation** - Helper for PVOC analysis
- 📊 **Sound Analysis** - Get basic properties of audio files

## Requirements

### System Requirements
- macOS, Linux, or Windows
- Python 3.8 or higher
- CDP (Composers' Desktop Project) installed

### Python Dependencies
```
mcp
soundfile
numpy
```

### CDP Installation
1. Download CDP from the [official website](https://www.unstablesound.net/cdp.html)
2. Install CDP following the platform-specific instructions
3. Set the `CDP_PATH` environment variable to your CDP programs directory:
   ```bash
   export CDP_PATH="/path/to/cdp/programs"
   ```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DavidPiazza/CDP_MCP.git
cd CDP_MCP
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install mcp soundfile numpy
```

### 3. Configure CDP Path
Set your CDP installation path:
```bash
export CDP_PATH="/Users/yourname/cdpr8/_cdp/_cdprogs"  # macOS example
```

### 4. Run the Server
```bash
python CDP_MCP_v7.py
```

## MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add to your configuration:

```json
{
  "mcpServers": {
    "cdp": {
      "command": "python",
      "args": ["/path/to/CDP_MCP_v7.py"],
      "env": {
        "CDP_PATH": "/path/to/cdp/programs"
      }
    }
  }
}
```

## Usage

### Basic Workflow

1. **List Available Programs**
   ```python
   list_cdp_programs()
   # Returns categorized list of all CDP programs
   ```

2. **Get Program Usage**
   ```python
   get_cdp_usage('blur')
   # Returns exact CDP usage text
   ```

3. **Execute Commands**
   ```python
   execute_cdp(['blur', 'blur', 'input.ana', 'output.ana', '50'])
   # Direct execution with no interpretation
   ```

### Example Operations

#### Time Stretch
```python
# Check usage
get_cdp_usage('stretch')

# Execute
execute_cdp(['stretch', 'time', '1', 'input.ana', 'output.ana', '2.0'])
```

#### Spectral Blur
```python
# Note the double syntax for blur
execute_cdp(['blur', 'blur', 'input.ana', 'output.ana', '50'])
```

#### Granular Synthesis
```python
execute_cdp(['modify', 'brassage', '4', 'input.wav', 'output.wav', '0.02', '-0.5', '-r200'])
```

#### Using Data Files
```python
# Create data file for tesselate
create_data_file('tess_data.txt', '5 5 5 5\n0.0 0.1 0.2 0.3')

# Execute with data file
execute_cdp(['tesselate', 'tesselate', '1', 'in1.wav', 'in2.wav', 'in3.wav', 'in4.wav', 'output.wav', '0.5', 'tess_data.txt'])
```

## Tools Reference

### `list_cdp_programs()`
Lists all available CDP programs organized by category (Spectral Processing, Time Domain, Synthesis, etc.)

### `get_cdp_usage(program, subprogram=None)`
Returns raw usage information for a CDP program by running it without arguments.

### `execute_cdp(command)`
Executes a CDP command given as an array of strings. No parsing or interpretation.

### `create_data_file(filepath, content)`
Creates text data files required by certain CDP programs.

### `prepare_spectral(input_file, output_file, window_size=2048)`
Helper function to perform PVOC analysis for spectral processing.

### `analyze_sound(filepath)`
Returns basic properties of a sound file (duration, sample rate, channels, etc.)

## Architecture

The server follows an ultra-rigid design philosophy:
- **No command parsing** - Commands are arrays, not strings
- **No parameter validation** - CDP handles all validation
- **No output interpretation** - Raw CDP output is returned
- **Minimal abstraction** - Direct CDP access only

## Tips

- Always check usage with `get_cdp_usage()` before executing
- CDP may return non-zero exit codes even on success
- Check if output files exist to verify successful execution
- Use exact command arrays - the server does no interpretation
- Create data files when CDP usage mentions DATAFILE requirements

## Troubleshooting

### CDP Not Found
Ensure `CDP_PATH` environment variable points to your CDP programs directory.

### Apple Silicon Issues
The server automatically handles x86_64 emulation on Apple Silicon Macs using `arch -x86_64`.

### Command Failures
1. Check the exact usage with `get_cdp_usage()`
2. Verify all file paths exist
3. Ensure proper command array format
4. Check CDP's stderr output for specific errors

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Composers' Desktop Project](https://www.unstablesound.net/cdp.html) for the amazing sound transformation tools
- [Model Context Protocol](https://github.com/anthropics/model-context-protocol) for the MCP framework 