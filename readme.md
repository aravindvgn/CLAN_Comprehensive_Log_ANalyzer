# CLAN - Comprehensive Log ANalyzer

**Version 0.95**

A powerful, universal log file parser and plotter for analyzing time-series data from various log formats.


**Key Features:**
- Universal log parser with smart format detection
- Dual-axis plotting with matplotlib integration
- Two independent Dataframe/Table viewers
- Advanced fuzzy search with column selection
- Optimized for large datasets (Lazy loading of Table for large datasets)
- Auto-detects CSV, TSV, PSV, SSV delimiters
- Handles interleaved message type logs
- Supports MM:SS.s elapsed time format
- Export to CSV functionality
- Raw log line access for debugging

---

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported File Formats](#supported-file-formats)
- [User Interface Guide](#user-interface-guide)
- [Advanced Features](#advanced-features)
- [Tips & Tricks](#tips--tricks)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Core Capabilities
- **Universal Parser**: Automatically detects and parses CSV, TSV, PSV, SSV, and custom log formats
- **Dual-Axis Plotting**: Plot multiple variables on left and right Y-axes
- **Multi-Table Viewing**: Three independent table tabs for simultaneous data viewing
- **Advanced Search**: Fuzzy search across multiple columns with case-sensitive options
- **Large File Support**: Lazy loading handles datasets with millions of rows efficiently
- **Column Management**: Show/hide columns with persistent settings per table
- **Data Export**: Export any table view to CSV format
- **Raw Data Access**: View original log lines for any row

### Smart Detection
- Auto-detects delimiters (comma, tab, pipe, semicolon)
- Auto-identifies timestamp columns
- Handles interleaved message types (e.g., drone telemetry logs)
- Converts MM:SS.s elapsed time format to seconds automatically
- Detects and splits mixed numerical/non-numerical data

---

## 🚀 Installation

### Requirements
```bash
pip install pandas numpy matplotlib easygui
```

### Optional (Recommended)
```bash
pip install polars  # For enhanced performance with large datasets
```

### Running the Application
```bash
python log_plotter.py
```

---

## 🎯 Quick Start

1. **Launch CLAN**
   ```bash
   python log_plotter.py
   ```

2. **Load a Log File**
   - Click `Load Log File` button
   - Select your log/CSV/TSV file
   - Parser automatically detects format and creates DataFrames

3. **View Data**
   - Double-click any DataFrame in the left panel → Opens in **Table-1**
   - Right double-click a DataFrame → Opens in **Table-2**

4. **Plot Variables**
   - Select variable(s) in the left panel
   - Click `Plot Selected` → Plots on left Y-axis
   - Or double-click a variable → Toggle plot on/off
   - Right double-click a variable → Plots on right Y-axis

5. **Search Data**
   - Press `Ctrl+F` (Windows/Linux) or `Cmd+F` (Mac) in any table
   - Or click the `Search` button
   - Results appear in the **Search Results** tab

---

## 📂 Supported File Formats

### Standard Formats
- **CSV** (Comma-Separated Values) ✅
- **TSV** (Tab-Separated Values) ✅
- **PSV** (Pipe-Separated Values) ✅
- **SSV** (Semicolon-Separated Values) ✅

All delimiters are **auto-detected** by analyzing the first 50 lines of your file.

### Special Formats

#### Interleaved Message Type Logs
Logs where different message types are mixed:
```
timestamp, process, INFO, GPS_DATA, lat, lon, alt
timestamp, process, INFO, IMU_DATA, accel_x, accel_y, accel_z
timestamp, process, INFO, GPS_DATA, lat, lon, alt
```
→ Automatically splits into separate `GPS_DATA` and `IMU_DATA` DataFrames

#### Mixed Column Count Files
Files with varying column counts are grouped by column count:
```
DATA_MISC_5COLS
DATA_MISC_8COLS
```

#### Time Format Support
- ISO datetime: `2024-01-15 14:30:45.123`
- Date only: `2024-01-15`, `01/15/2024`
- Time only: `14:30:45.123`
- **Elapsed time**: `00:01.5` (MM:SS.s) → Converted to seconds (1.5)
- **Extended elapsed**: `01:30:45.250` (HH:MM:SS.sss) → Converted to seconds (5445.25)

---

## 🖥️ User Interface Guide

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ CLAN v0.95 - filename.log                                   │
├──────────────┬──────────────────────────────────────────────┤
│              │  [Plotter] [Table-1] [Table-2] [Search]      │
│ [Load Log]   │                                              │
│ [Plot Sel.]  │                                              │
│ [Clear Plot] │         Main Content Area                    │
│              │                                              │
│ Variable     │                                              │
│ Selection    │                                              │
│ Tree         │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### Variable Tree (Left Panel)

**Structure:**
```
📁 DataFrame_Name (DataFrame, 1000 rows)
  ├─ variable_1 (float64, 1000 rows)
  ├─ variable_2 (int64, 998 rows)
  └─ variable_3 (float64, 1000 rows)
```

**Interactions:**
- **Single-click**: Select variable(s)
- **Double-click variable**: Toggle plot on left Y-axis
- **Right double-click variable**: Toggle plot on right Y-axis
- **Double-click DataFrame**: Open in Table-1
- **Right double-click DataFrame**: Open in Table-2

**Visual Indicators:**
- 🔵 **Light blue**: Plotted on left Y-axis
- 🔴 **Light pink**: Plotted on right Y-axis

---

## 📊 Plotter Tab

### Controls
- **Plot Selected**: Plot selected variables on left Y-axis
- **Clear Plot**: Remove all plots and reset
- **Refresh Plot**: Update plot with current settings
- **Y-axis scale**: Toggle between Linear/Log scale

### Plotting Features

#### Left Y-Axis (Blue)
- Default plotting axis
- All variables plot here unless specified otherwise

#### Right Y-Axis (Red)
- For variables with different scales
- Activate by right double-clicking a variable

#### Plot Interactions
- **Zoom**: Matplotlib toolbar zoom button
- **Pan**: Matplotlib toolbar pan button
- **Save**: Export plot as PNG/PDF/SVG
- **Home**: Reset view to original

---

## 📋 Table Tabs

### Table-1 & Table-2
Independent table viewers for simultaneous data comparison.

### Features

#### Column Management
- **Show/Hide Columns** button
  - Select which columns to display
  - Timestamp column always visible
  - Settings persist per table
- **Quick actions**:
  - `Hide All` / `Unhide All`
  - `Select All` / `Deselect All`

#### Context Menus

**Right-click on column header:**
- `Hide '[column]' Column`
- `Show Hidden Columns`
- `View Raw Header` (if available)

**Right-click on cell:**
- `View Full Content` - See complete cell value
- `Copy Cell Value` - Copy to clipboard
- `View Raw Data` - See original log line (if available)

#### Large Dataset Handling
- **Lazy Loading**: Loads 500 rows at a time
- Auto-loads more as you scroll
- `Load All Rows` button for full dataset
- Shows progress: "Loaded 500/10000 rows (auto-loading...)"

### Search Results Tab
Displays search matches with context:
- Source DataFrame name
- Search term and options used
- Columns searched
- Match count
- Full search results table

---

## 🔍 Advanced Features

### Search Functionality

**Keyboard Shortcut:** `Ctrl+F` / `Cmd+F` in any table tab

**Search Options:**

1. **Approximate String Search (Fuzzy)**
   - Finds similar matches (≥80% similarity)
   - Useful for typos or variations
   - Example: "GPS" finds "GPS_DATA", "GPS_FIX"

2. **Case Sensitive**
   - Match exact letter case
   - Off by default

3. **Column Selection**
   - Search specific columns or all
   - Timestamp column excluded by default
   - `Select All` / `Deselect All` buttons

**Search Behavior:**
- Shows progress for large datasets (>1000 rows)
- Results open in Search Results tab
- Original DataFrame unchanged

### Cell Content Viewer

**Double-click any cell** to see:
- Full untruncated content
- Array/list elements with indices
- Numeric statistics for arrays (min, max, average, sum)
- Comma-separated format for easy copying

**Example:**
```
List/Tuple content (list):

Length: 5

Elements:
[0]: 1.234
[1]: 2.345
[2]: 3.456
[3]: 4.567
[4]: 5.678

Comma-separated:
1.234, 2.345, 3.456, 4.567, 5.678

Numeric Statistics (5/5 elements):
  Min: 1.234
  Max: 5.678
  Average: 3.456
  Sum: 17.280
```

### Data Export

**Export to CSV:**
- Click `Export to CSV` in any table
- Exports currently displayed data
- Search results can be exported separately
- Excludes internal raw data columns

### Raw Data Access

For files parsed by the universal parser:
- Right-click any row → `View Raw Data`
- See the original log line before parsing
- Useful for debugging parsing issues

---

## 💡 Tips & Tricks

### Working with Large Files
1. **Files >100MB**: Parser shows warning but handles them
2. **Lazy loading**: Tables load in batches - scroll triggers auto-load
3. **Load strategically**: Don't load all rows unless needed
4. **Search efficiently**: Use column selection to narrow search scope

### Effective Plotting
1. **Dual Y-Axes**: Use for variables with vastly different scales
   - Example: Temperature (0-100°C) + Altitude (0-5000m)
2. **Log Scale**: Useful for exponential data or wide value ranges
3. **Legend**: Shows all plotted variables with axis indicator `[R]` for right axis
4. **Color Coding**: Tree highlights show which variables are plotted

### Table Management
1. **Three Tables**: Compare different DataFrames side-by-side
   - Table-1: Full dataset
   - Table-2: Filtered/different dataset
   - Search Results: Query matches
2. **Column Hiding**: Focus on relevant data
   - Hide metadata columns
   - Keep analysis clean
3. **Hidden Column Indicator**: Shows count of hidden columns

### Search Strategies
1. **Fuzzy Search**: When you're not sure of exact spelling
2. **Column Selection**: Faster search on specific columns
3. **Export Results**: Save search results as separate CSV
4. **Iterative Refinement**: Search results can be searched again

### Timestamp Handling
- Parser auto-detects timestamp columns
- If none found, you'll be prompted to select one
- Can rename columns like "time", "elapsed", "duration" to "timestamp"
- Supports timestamp offset (default: +5:30 hours IST)

---

## 📦 Requirements

### Python Version
- **Python 3.12 or higher** (required for latest features)

### Required Libraries
```
pandas >= 2.0.0       # DataFrame operations with nullable Int64 support
numpy >= 1.24.0       # Numerical computations
matplotlib >= 3.7.0   # Plotting and visualization
```

### Optional Libraries
```
polars >= 0.19.0      # Enhanced performance for large datasets
easygui >= 0.98.3     # File dialog (fallback to tkinter if unavailable)
```

### Installation Command
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pandas>=2.0.0 numpy>=1.24.0 matplotlib>=3.7.0 easygui>=0.98.3 polars>=0.19.0
```

### Note on tkinter
- **tkinter** is included with standard Python installations
- If missing on Linux: `sudo apt-get install python3-tk`
- If missing on macOS: Reinstall Python with tcl/tk support

---

## 📝 File Format Examples

### Standard CSV with Header
```csv
timestamp,latitude,longitude,altitude,speed
2024-01-15 10:30:00,28.6139,77.2090,500,25.5
2024-01-15 10:30:01,28.6140,77.2091,502,26.0
```

### TSV (Tab-Separated)
```tsv
timestamp	temperature	pressure	humidity
10:30:00	25.5	1013.25	65
10:30:01	25.6	1013.24	65
```

### PSV (Pipe-Separated)
```
timestamp|sensor_id|value|status
10:30:00|TEMP_01|25.5|OK
10:30:01|TEMP_01|25.6|OK
```

### SSV (Semicolon-Separated)
```
timestamp;voltage;current;power
10:30:00;12.5;2.3;28.75
10:30:01;12.6;2.4;30.24
```

### Interleaved Message Types
```csv
timestamp,process,level,message_type,data1,data2,data3
10:30:00,mavros,INFO,GPS,lat,lon,alt
10:30:00,mavros,INFO,IMU,ax,ay,az
10:30:01,mavros,INFO,GPS,lat,lon,alt
```
→ Creates separate GPS and IMU DataFrames

### Elapsed Time Format
```csv
time,height,speed
00:00.0,0,0
00:01.5,10,5.2
01:30.2,500,25.8
```
→ Time column converted to seconds: 0.0, 1.5, 90.2

---

## 🤝 Contributing

Found a bug or have a feature request? 
- The code is well-structured with extensive configuration options
- Check `Config` class in `log_plotter.py` for customizable parameters
- Parser behavior can be modified in `universal_log_parser.py`

---

## 📜 License

This tool is provided as-is for log analysis and data visualization purposes only.

---