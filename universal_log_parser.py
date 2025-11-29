import pandas as pd
from datetime import datetime, timedelta
import re
from typing import Dict, List, Any, Optional, Tuple, Set
import os
from collections import defaultdict, Counter

# Optional imports
try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False

try:
    import easygui
    HAS_EASYGUI = True
except ImportError:
    HAS_EASYGUI = False


def detect_delimiter(file_path: str, sample_lines: int = 50) -> str:
    """Detect the delimiter used in the file."""
    common_delimiters = [',', '\t', '|', ';']
    delimiter_counts = defaultdict(int)
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= sample_lines:
                break
            line = line.strip()
            if line:
                for delim in common_delimiters:
                    delimiter_counts[delim] += line.count(delim)
    
    if delimiter_counts:
        detected = max(delimiter_counts.items(), key=lambda x: x[1])[0]
        delimiter_name = {',': 'comma', '\t': 'tab', '|': 'pipe', ';': 'semicolon'}.get(detected, repr(detected))
        print(f"Detected delimiter: {delimiter_name} ({repr(detected)})")
        return detected
    
    return ','


def is_message_type(value: str) -> bool:
    """Check if a value looks like a message type identifier."""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # Length check: 2-25 characters (increased from 15 to handle longer message types)
    if not (2 <= len(value) <= 25):
        return False
    
    # Pattern check: alphanumeric with underscore/dash
    if not re.match(r'^[A-Za-z0-9_-]+$', value):
        return False
    
    # Not a pure number
    try:
        float(value)
        return False
    except ValueError:
        pass
    
    # Not a timestamp
    if ':' in value or re.match(r'\d{4}-\d{2}-\d{2}', value):
        return False
    
    return True


def is_timestamp_value(value: str) -> bool:
    """Check if a value looks like a timestamp."""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # Date pattern (YYYY-MM-DD or YYYY/MM/DD)
    if re.match(r'\d{4}[-/]\d{2}[-/]\d{2}', value):
        return True
    
    # Time patterns - must be proper time format, not just any string with colon
    # Matches: HH:MM:SS.mmm, HH:MM:SS, HH:MM, MM:SS.mmm, MM:SS
    # Does NOT match: "FLOWMETER: message" or "key: value" patterns
    time_patterns = [
        r'^\d{1,2}:\d{2}:\d{2}(\.\d+)?$',  # HH:MM:SS or HH:MM:SS.mmm
        r'^\d{1,2}:\d{2}(\.\d+)?$',         # HH:MM or MM:SS.m
        r'^\d{4}-\d{2}-\d{2}[T\s]\d{1,2}:\d{2}',  # ISO format with time
    ]
    
    for pattern in time_patterns:
        if re.match(pattern, value):
            return True
    
    return False


def parse_mmss_timestamp(value: str) -> Optional[float]:
    """
    Parse MM:SS.s or HH:MM:SS.sss format timestamp and convert to seconds.
    Returns None if parsing fails or values are invalid.
    
    Examples:
        '00:00.0' -> 0.0
        '00:01.5' -> 1.5
        '01:30.2' -> 90.2
        '00:00:01.500' -> 1.5
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    
    try:
        # Try HH:MM:SS.sss format first
        if value.count(':') == 2:
            parts = value.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            # Validate reasonable ranges for elapsed time
            # Allow up to 99 hours, 59 minutes, 59.999 seconds
            if hours < 0 or hours > 99:
                return None
            if minutes < 0 or minutes > 59:
                return None
            if seconds < 0 or seconds >= 60:
                return None
            
            return hours * 3600 + minutes * 60 + seconds
        
        # Try MM:SS.s format
        elif value.count(':') == 1:
            parts = value.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            
            # Validate reasonable ranges for elapsed time
            # Allow up to 9999 minutes (about 166 hours), 59.999 seconds
            if minutes < 0 or minutes > 9999:
                return None
            if seconds < 0 or seconds >= 60:
                return None
            
            return minutes * 60 + seconds
        
    except (ValueError, IndexError):
        pass
    
    return None


def is_mmss_timestamp(value: str) -> bool:
    """Check if a value is in MM:SS.s or HH:MM:SS.sss format."""
    return parse_mmss_timestamp(value) is not None


def is_likely_header_row(parts: List[str]) -> bool:
    """Determine if a row is likely a header."""
    if len(parts) == 0:
        return False
    
    # If first value is a timestamp, definitely not a header
    if parts[0] and is_timestamp_value(parts[0]):
        return False
    
    # Common header keywords - expanded for drone/flight data
    header_keywords = {
        # Data types
        'int', 'float', 'string', 'bool', 'datetime',
        # Units
        'm', 'cm', 'mm', 's', 'ms', 'deg', 'rad', 'meter', 'second', 'degree',
        'unit', 'type', 'v', 'a', 'c', 'hz', 'khz', 'mhz',
        # Position/navigation
        'lat', 'latitude', 'lon', 'longitude', 'height', 'altitude', 'alt',
        'yaw', 'pitch', 'roll', 'heading', 'bearing',
        # Speed/motion
        'speed', 'velocity', 'climb_rate', 'descent_rate', 'groundspeed',
        # Flight state
        'mode', 'armed', 'flying', 'landed', 'disarmed',
        # Waypoints
        'wp', 'waypoint', 'mission', 'seq', 'sequence',
        # Spray/agriculture
        'spray', 'flow', 'flowrate', 'dosage', 'pump', 'nozzle',
        # RC channels
        'rc1', 'rc2', 'rc3', 'rc4', 'rc5', 'rc6', 'rc7', 'rc8', 'rc9', 'rc10',
        'rc11', 'rc12', 'rc13', 'rc14', 'rc15', 'rc16',
        # Sensors
        'gps', 'accel', 'gyro', 'mag', 'baro', 'compass',
        # Battery/power
        'voltage', 'current', 'battery', 'power',
    }
    
    # Fields with units in parentheses are headers (e.g., "height(m)", "speed(m/s)")
    unit_pattern = re.compile(r'.*\([^)]+\)$')
    
    header_count = 0
    data_count = 0
    
    for part in parts:
        part_clean = part.strip().lower()
        
        if not part_clean:
            continue
        
        # Check for unit notation like "height(m)", "speed(m/s)"
        if unit_pattern.match(part_clean):
            header_count += 1
            continue
        
        # Check against header keywords
        if part_clean in header_keywords:
            header_count += 1
            continue
        
        # Numeric values are definitely data
        try:
            float(part_clean)
            data_count += 1
            continue
        except ValueError:
            pass
        
        # Timestamp values are data
        if is_timestamp_value(part_clean):
            data_count += 1
            continue
        
        # Special patterns that indicate data, not headers
        data_patterns = [
            r'^-?\d+\.\d+$',  # Float numbers
            r'^-?\d+$',        # Integer numbers
            r'^(true|false)$', # Boolean
            r'^[A-Z]+$',       # All caps (likely enum values like "LOITER", "ARMED")
            r'^not-',          # Negation prefix (like "not-flying")
        ]
        
        is_data = any(re.match(pattern, part_clean) for pattern in data_patterns)
        if is_data:
            data_count += 1
        else:
            header_count += 1
    
    # Header if majority are header-like
    total = header_count + data_count
    if total == 0:
        return False
    
    return header_count > data_count


def detect_message_type_column(sample_rows: List[List[str]], max_col: int = 10) -> Optional[int]:
    """Detect which column contains message type identifiers."""
    if not sample_rows:
        return None
    
    # Filter out log level keywords that aren't message types
    log_level_keywords = {'INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL', 'TRACE', 'WARN', 'FATAL'}
    
    # Check each column position
    for col_idx in range(min(max_col, max(len(row) for row in sample_rows))):
        msg_types = []
        msg_type_set = set()
        original_case_types = []  # Track original case
        
        for row in sample_rows:
            if col_idx < len(row):
                original_value = row[col_idx].strip()
                value = original_value.upper()
                
                # Skip if it's a log level keyword
                if value in log_level_keywords:
                    continue
                    
                if is_message_type(value):
                    msg_types.append(value)
                    msg_type_set.add(value)
                    original_case_types.append(original_value)
        
        # If at least 30% of rows have message type in this column
        if len(msg_types) >= len(sample_rows) * 0.3:
            # And there are 2+ unique types (indicates grouping)
            if len(msg_type_set) >= 2:
                # Additional validation: Check if these are likely actual message types
                # Real message types are typically:
                # 1. ALL CAPS (at least 80% of them)
                # 2. Have underscores or dashes
                # 3. Are NOT simple lowercase words
                
                all_caps_count = sum(1 for v in original_case_types if v.isupper())
                has_separators = sum(1 for v in original_case_types if '_' in v or '-' in v)
                all_lowercase_count = sum(1 for v in original_case_types if v.islower())
                
                # If most are all lowercase, it's probably data, not message types
                if all_lowercase_count > len(original_case_types) * 0.5:
                    continue
                
                # Require either: most are ALL CAPS, or many have underscores/dashes
                if all_caps_count > len(original_case_types) * 0.6 or has_separators > len(original_case_types) * 0.3:
                    print(f"  Message type column detected at position {col_idx}")
                    print(f"  Found {len(msg_type_set)} types: {sorted(list(msg_type_set)[:10])}")
                    if len(msg_type_set) > 10:
                        print(f"  ... and {len(msg_type_set) - 10} more")
                    return col_idx
    
    return None


def sample_file(file_path: str, delimiter: str, n_lines: int = 50) -> List[List[str]]:
    """Sample first N lines from file."""
    sample = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= n_lines:
                break
            line = line.strip()
            if line:
                parts = [p.strip() for p in line.split(delimiter)]
                # Strip trailing empty columns
                while parts and not parts[-1]:
                    parts.pop()
                if parts:  # Only add if there's actual content
                    sample.append(parts)
    return sample


def generate_column_names(n_cols: int, sample_values: List[List[str]], msg_type_col: Optional[int] = None) -> List[str]:
    """Generate column names, detecting timestamp columns."""
    columns = []
    
    for col_idx in range(n_cols):
        # Skip message type column
        if msg_type_col is not None and col_idx == msg_type_col:
            columns.append('message_type')
            continue
        
        # Check if this column contains timestamps
        timestamp_count = 0
        sample_to_check = sample_values[:20]  # Check first 20 rows
        for row in sample_to_check:
            if col_idx < len(row) and is_timestamp_value(row[col_idx]):
                timestamp_count += 1
        
        # Fixed threshold: compare against rows actually checked, not total sample_values
        # Also handle empty sample case: if no rows to check, don't name as timestamp
        if len(sample_to_check) > 0 and timestamp_count >= len(sample_to_check) * 0.5:
            # Find unique timestamp column name
            base_name = 'timestamp'
            col_name = base_name
            suffix = 1
            while col_name in columns:
                col_name = f"{base_name}_{suffix}"
                suffix += 1
            columns.append(col_name)
        else:
            columns.append(f'column_{col_idx}')
    
    return columns


def infer_value_type(value: str) -> Tuple[str, Any]:
    """Infer the data type of a string value and convert it."""
    value = value.strip()
    
    if not value or value.lower() in ('none', 'null', 'nan', ''):
        return ('null', None)
    
    # Try boolean
    if value.lower() in ('true', 'false', 'yes', 'no'):
        bool_val = value.lower() in ('true', 'yes')
        return ('bool', bool_val)
    
    # Try MM:SS.s format (like 00:00.0) - check before full datetime
    # IMPORTANT: Only convert MM:SS.s (1 colon) to seconds automatically
    # HH:MM:SS (2 colons) should be handled by datetime parser
    # This prevents ambiguity between elapsed time and clock time
    if value.count(':') == 1:  # Only MM:SS.s format
        mmss_seconds = parse_mmss_timestamp(value)
        if mmss_seconds is not None:
            # Double-check it's not part of a full datetime string
            if not re.match(r'\d{4}[-/]\d{2}[-/]\d{2}', value):
                return ('mmss_timestamp', mmss_seconds)
    
    # Try datetime (includes HH:MM:SS format)
    if is_timestamp_value(value):
        try:
            # Try various datetime formats
            for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', 
                       '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
                       '%H:%M:%S.%f', '%H:%M:%S']:  # Added time-only formats
                try:
                    dt = datetime.strptime(value, fmt)
                    return ('datetime', dt)
                except (ValueError, TypeError):
                    continue
        except (ValueError, TypeError, AttributeError):
            pass
    
    # Try numeric
    try:
        if '.' in value or 'e' in value.lower():
            return ('float', float(value))
        else:
            return ('int', int(value))
    except (ValueError, TypeError, AttributeError):
        pass
    
    # Default to string
    return ('string', value)


def infer_column_types_from_data(data_rows: List[List[str]], headers: List[str]) -> Dict[str, str]:
    """Infer column types from data rows."""
    column_types = {header: 'string' for header in headers}
    type_samples = {header: [] for header in headers}
    
    # Sample up to 100 rows for type inference
    sample_size = min(100, len(data_rows))
    for row in data_rows[:sample_size]:
        for i, value in enumerate(row):
            if i < len(headers):
                inferred_type, _ = infer_value_type(value)
                type_samples[headers[i]].append(inferred_type)
    
    # Determine type by majority vote
    for header in headers:
        samples = type_samples[header]
        if not samples:
            continue
        
        # Count types
        type_counter = Counter(samples)
        
        # If mostly null, keep as string
        null_ratio = type_counter.get('null', 0) / len(samples)
        if null_ratio > 0.9:
            column_types[header] = 'string'
            continue
        
        # Remove nulls for type determination
        non_null_types = [t for t in samples if t != 'null']
        if not non_null_types:
            column_types[header] = 'string'
            continue
        
        # Use most common type
        most_common = Counter(non_null_types).most_common(1)[0][0]
        column_types[header] = most_common
    
    return column_types


def convert_row_values(row: List[str], column_types: Dict[str, str], headers: List[str]) -> List[Any]:
    """Convert row values based on inferred types."""
    converted = []
    for i, value in enumerate(row):
        # Only process values up to the number of headers
        # This ensures output matches header length
        if i >= len(headers):
            break  # Truncate extra columns
        
        header = headers[i]
        target_type = column_types.get(header, 'string')
        
        _, converted_value = infer_value_type(value)
        converted.append(converted_value)
    
    # Pad with None if row is shorter than headers
    while len(converted) < len(headers):
        converted.append(None)
    
    return converted


def apply_timestamp_offset(df: pd.DataFrame, offset: timedelta) -> pd.DataFrame:
    """Apply timestamp offset to datetime columns."""
    if offset == timedelta(0):
        return df
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col] + offset
    
    return df


def parse_universal_log(file_path: str = None, timestamp_offset: timedelta = timedelta(hours=5, minutes=30)) -> Tuple[Dict[str, pd.DataFrame], str]:
    """Universal log parser that handles various formats."""
    
    # File selection
    if file_path is None:
        if HAS_EASYGUI:
            file_path = easygui.fileopenbox(
                msg="Select log file",
                title="File Selection",
                filetypes=["*.log", "*.txt", "*.csv", "*.tsv", "*.*"]
            )
        else:
            print("Error: easygui not available and no file path provided")
            return {}, ""
        
        if not file_path:
            print("No file selected")
            return {}, ""
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return {}, ""
    
    # Check file size and warn for large files
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 100:
        print(f"⚠️  Large file detected ({file_size_mb:.1f} MB)")
        print(f"    Loading may take significant time and memory...")
    
    filename = os.path.basename(file_path)
    print(f"Parsing: {filename}")
    print("="*70)
    
    # Detect delimiter
    delimiter = detect_delimiter(file_path)
    
    # Sample file
    sample = sample_file(file_path, delimiter, n_lines=100)
    if not sample:
        print("Error: Empty or invalid file")
        return {}, filename
    
    print(f"Sample: {len(sample)} lines")
    
    # Detect message type column
    msg_type_col = detect_message_type_column(sample)
    
    if msg_type_col is not None:
        # Interleaved format
        dataframes = parse_interleaved_format(file_path, delimiter, msg_type_col, timestamp_offset)
    else:
        # Check for mixed format (different column counts)
        col_counts = Counter(len(row) for row in sample)
        if len(col_counts) > 1:
            print(f"  Mixed format detected: {len(col_counts)} different column counts")
            dataframes = parse_mixed_format(file_path, delimiter, timestamp_offset)
        else:
            # Standard CSV/TSV
            dataframes = parse_standard_format(file_path, delimiter, sample, timestamp_offset)
    
    print("\n" + "="*70)
    print(f"Parsing complete: {len(dataframes)} DataFrames created")
    for name, df in dataframes.items():
        print(f"  {name}: {len(df)} rows, {len(df.columns)} columns")
    
    return dataframes, filename


def parse_interleaved_format(file_path: str, delimiter: str, msg_type_col: int, timestamp_offset: timedelta) -> Dict[str, pd.DataFrame]:
    """Parse interleaved format with message types - FIXED VERSION."""
    message_headers = {}
    message_data = defaultdict(list)
    message_raw_data = defaultdict(list)
    message_raw_headers = {}  # Store raw header lines
    
    print("\nParsing interleaved format...")
    
    # Determine how many columns before message type (common prefix)
    common_prefix_cols = msg_type_col  # Columns before message type (timestamp, process, loglevel, etc.)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                original_line = line.rstrip('\n\r')
                line = line.strip()
                if not line:
                    continue
                
                parts = [p.strip() for p in line.split(delimiter)]
                
                # Strip trailing empty columns
                while parts and not parts[-1]:
                    parts.pop()
                
                if len(parts) <= msg_type_col:
                    continue
                
                message_type = parts[msg_type_col].strip().upper()
                
                if not is_message_type(message_type):
                    continue
                
                # Extract prefix (timestamp, process, log level) and message-specific data
                prefix = parts[:msg_type_col]
                message_specific = parts[msg_type_col+1:]  # Data after message type
                
                # Check if header or data BY LOOKING ONLY AT MESSAGE-SPECIFIC COLUMNS
                if message_type not in message_headers:
                    # First occurrence - check if it's header or data
                    # IMPORTANT: Only check message-specific columns, not the prefix
                    if is_likely_header_row(message_specific):
                        # Generate names for prefix columns, use actual names for message-specific
                        prefix_names = generate_column_names(len(prefix), [prefix])
                        # Store combined header names
                        message_headers[message_type] = prefix_names + message_specific
                        # Store the raw header line for later reference
                        message_raw_headers[message_type] = original_line
                        print(f"  Header for '{message_type}': {message_specific}")
                    else:
                        # First row is data, generate column names for all
                        full_row = prefix + message_specific
                        message_headers[message_type] = generate_column_names(len(full_row), [full_row])
                        message_data[message_type].append(full_row)
                        message_raw_data[message_type].append(original_line)
                        print(f"  '{message_type}': No header, generated {len(full_row)} column names")
                elif is_likely_header_row(message_specific):
                    # Skip subsequent header rows (metadata)
                    continue
                else:
                    # Data row - reconstruct full row with prefix
                    full_row = prefix + message_specific
                    message_data[message_type].append(full_row)
                    message_raw_data[message_type].append(original_line)
    except Exception as e:
        raise RuntimeError(f"Critical parsing error at line {line_num}: {e}")
    
    # Create DataFrames - FIXED: Properly use headers as column names
    dataframes = {}
    
    for msg_type, headers in message_headers.items():
        if msg_type not in message_data or not message_data[msg_type]:
            print(f"  Warning: No data found for '{msg_type}' (only header)")
            continue
        
        data_rows = message_data[msg_type]
        
        # Ensure consistent column count
        max_cols = max(len(row) for row in data_rows)
        if len(headers) < max_cols:
            # Extend headers if needed
            for i in range(len(headers), max_cols):
                headers.append(f'column_{i}')
        elif len(headers) > max_cols:
            # Trim headers if needed
            headers = headers[:max_cols]
        
        # Pad rows to match header length
        padded_data = []
        for row in data_rows:
            if len(row) < len(headers):
                padded_row = row + [''] * (len(headers) - len(row))
            else:
                padded_row = row[:len(headers)]
            padded_data.append(padded_row)
        
        # Infer types
        column_types = infer_column_types_from_data(padded_data, headers)
        
        # Convert data with proper types
        converted_data = []
        for row in padded_data:
            converted_row = convert_row_values(row, column_types, headers)
            converted_data.append(converted_row)
        
        # Create DataFrame with explicit column names - THIS IS THE FIX
        df = pd.DataFrame(converted_data, columns=headers)
        
        # Add raw data column
        raw_col_name = '__parser_raw_line__'
        if msg_type in message_raw_data and len(message_raw_data[msg_type]) == len(df):
            df[raw_col_name] = message_raw_data[msg_type]
        
        # Store raw header line if it exists (for context menu display)
        if msg_type in message_raw_headers:
            df.attrs['__parser_raw_header__'] = message_raw_headers[msg_type]
        
        # Apply proper data types
        for col_name, col_type in column_types.items():
            if col_name in df.columns:
                try:
                    if col_type == 'datetime':
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                    elif col_type == 'mmss_timestamp':
                        # Convert to float (seconds) for plotting
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                        print(f"  Converted '{col_name}' from MM:SS.s format to seconds")
                    elif col_type == 'int':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                    elif col_type == 'float':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                    elif col_type == 'bool':
                        df[col_name] = df[col_name].astype('bool')
                except Exception as e:
                    print(f"  Warning: Could not convert column '{col_name}' to {col_type}: {e}")
        
        # Apply timestamp offset
        df = apply_timestamp_offset(df, timestamp_offset)
        
        dataframes[msg_type] = df
        print(f"  Created DataFrame for '{msg_type}': {len(df)} rows × {len(df.columns)} columns")
    
    return dataframes


def parse_standard_format(file_path: str, delimiter: str, sample: List[List[str]], timestamp_offset: timedelta) -> Dict[str, pd.DataFrame]:
    """Parse standard CSV/TSV format."""
    print("\nParsing standard CSV/TSV format...")
    
    # Check if first row is header
    first_row = sample[0]
    has_header = is_likely_header_row(first_row)
    raw_header_line = None
    
    if has_header:
        print("  Detected header row")
        headers = first_row
        skip_rows = 1
        # Get the raw header line
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_header_line = f.readline().rstrip('\n\r')
    else:
        print("  No header detected, generating column names...")
        headers = generate_column_names(len(first_row), sample)
        skip_rows = 0
    
    # Read all data
    all_data = []
    all_raw_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f):
                if line_num < skip_rows:
                    continue
                
                original_line = line.rstrip('\n\r')
                line = line.strip()
                if not line:
                    continue
                
                parts = [p.strip() for p in line.split(delimiter)]
                while parts and not parts[-1]:
                    parts.pop()
                if parts:
                    all_data.append(parts)
                    all_raw_data.append(original_line)
    except Exception as e:
        raise RuntimeError(f"Critical parsing error at line {line_num}: {e}")
    
    # Infer types
    column_types = infer_column_types_from_data(all_data, headers)
    
    # Convert data
    converted_data = []
    for row in all_data:
        converted_data.append(convert_row_values(row, column_types, headers))
    
    # Create DataFrame with explicit column names
    df = pd.DataFrame(converted_data, columns=headers)
    
    # Add raw data column
    raw_col_name = '__parser_raw_line__'
    if len(all_raw_data) == len(df):
        df[raw_col_name] = all_raw_data
    
    # Store raw header line if it exists
    if raw_header_line:
        df.attrs['__parser_raw_header__'] = raw_header_line
    
    # Apply types
    for col_name, col_type in column_types.items():
        if col_name in df.columns:
            try:
                if col_type == 'datetime':
                    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                elif col_type == 'mmss_timestamp':
                    # Convert to float (seconds) for plotting
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                    print(f"  Converted '{col_name}' from MM:SS.s format to seconds")
                elif col_type == 'int':
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                elif col_type == 'float':
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                elif col_type == 'bool':
                    df[col_name] = df[col_name].astype('bool')
            except (ValueError, TypeError, AttributeError) as e:
                print(f"  Warning: Could not convert column '{col_name}' to {col_type}: {e}")
    
    df = apply_timestamp_offset(df, timestamp_offset)
    
    # Normalize timestamp column name: recognize various time-related names and rename to 'timestamp'
    # This helps the plotter work consistently
    if 'timestamp' not in df.columns:
        # Try exact matches first
        exact_matches = ['time', 'Time', 'TIME', 'datetime', 'DateTime', 'DATETIME']
        for col in exact_matches:
            if col in df.columns:
                df.rename(columns={col: 'timestamp'}, inplace=True)
                print(f"  Renamed '{col}' column to 'timestamp' for consistency")
                break
        
        # If no exact match, try partial matches (case-insensitive)
        if 'timestamp' not in df.columns:
            time_patterns = ['time_sec', 'time_s', 'elapsed', 'duration', 'timestamp']
            for col in df.columns:
                col_lower = col.lower()
                # Check if column name contains time-related patterns
                if any(pattern in col_lower for pattern in time_patterns):
                    # Also check if it's numeric (likely to be elapsed seconds)
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df.rename(columns={col: 'timestamp'}, inplace=True)
                        print(f"  Renamed '{col}' column to 'timestamp' for consistency")
                        break
    
    return {'DATA': df}


def parse_mixed_format(file_path: str, delimiter: str, timestamp_offset: timedelta) -> Dict[str, pd.DataFrame]:
    """Parse mixed format, grouping by column count."""
    print("\nParsing mixed format...")
    
    grouped_data = defaultdict(list)
    grouped_raw_data = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                original_line = line.rstrip('\n\r')
                line = line.strip()
                if not line:
                    continue
                
                parts = [p.strip() for p in line.split(delimiter)]
                while parts and not parts[-1]:
                    parts.pop()
                if parts:
                    n_cols = len(parts)
                    grouped_data[n_cols].append(parts)
                    grouped_raw_data[n_cols].append(original_line)
    except Exception as e:
        raise RuntimeError(f"Critical parsing error at line {line_num}: {e}")
    
    print(f"  Found {len(grouped_data)} different column counts")
    
    dataframes = {}
    
    for n_cols, rows in grouped_data.items():
        print(f"  Processing {len(rows)} rows with {n_cols} columns...")
        
        # Generate column names
        headers = generate_column_names(n_cols, rows[:20])
        
        # Infer types
        column_types = infer_column_types_from_data(rows, headers)
        
        # Convert data
        converted_data = []
        for row in rows:
            converted_data.append(convert_row_values(row, column_types, headers))
        
        # Create DataFrame with explicit column names
        df = pd.DataFrame(converted_data, columns=headers)
        
        # Add raw data column
        raw_col_name = '__parser_raw_line__'
        if n_cols in grouped_raw_data and len(grouped_raw_data[n_cols]) == len(df):
            df[raw_col_name] = grouped_raw_data[n_cols]
        
        # Apply types
        for col_name, col_type in column_types.items():
            if col_name in df.columns:
                try:
                    if col_type == 'datetime':
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                    elif col_type == 'mmss_timestamp':
                        # Convert to float (seconds) for plotting
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                        print(f"  Converted '{col_name}' from MM:SS.s format to seconds")
                    elif col_type == 'int':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')
                    elif col_type == 'float':
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                    elif col_type == 'bool':
                        df[col_name] = df[col_name].astype('bool')
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"  Warning: Could not convert column '{col_name}' to {col_type}: {e}")
        
        df = apply_timestamp_offset(df, timestamp_offset)
        
        df_name = f'DATA_MISC_{n_cols}COLS'
        dataframes[df_name] = df
    
    return dataframes


def convert_to_polars(pandas_dfs: Dict[str, pd.DataFrame]) -> Dict:
    """Convert pandas DataFrames to Polars DataFrames."""
    if not HAS_POLARS:
        return {}
    
    polars_dfs = {}
    for name, df in pandas_dfs.items():
        try:
            polars_dfs[name] = pl.from_pandas(df, nan_to_null=True)
        except Exception as e:
            print(f"Warning: Could not convert {name} to Polars: {e}")
    return polars_dfs


def parse_log_file(file_path: str = None, timestamp_offset: timedelta = timedelta(hours=5, minutes=30)) -> Tuple[Dict[str, pd.DataFrame], str]:
    """Wrapper for log_plotter.py compatibility."""
    return parse_universal_log(file_path=file_path, timestamp_offset=timestamp_offset)


def main():
    """Main function for testing"""
    print("Universal CSV/TSV/Log Parser - FIXED VERSION")
    print("Handles: Interleaved, Standard CSV, TSV, Mixed formats")
    print("="*70)
    
    dataframes, filename = parse_universal_log()
    
    if not dataframes:
        return None, None
    
    polars_dataframes = convert_to_polars(dataframes)
    
    print("\nDETAILED RESULTS:")
    print("="*70)
    
    for df_name, df in dataframes.items():
        print(f"\n{df_name}:")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Dtypes:\n{df.dtypes}")
        print(f"\n  First 3 rows:")
        print(df.head(3).to_string(index=False))
    
    print(f"\nLoaded: {filename}")
    
    return dataframes, polars_dataframes


if __name__ == "__main__":
    pandas_dfs, polars_dfs = main()
    if pandas_dfs:
        print("\n✓ Parsing completed successfully!")
