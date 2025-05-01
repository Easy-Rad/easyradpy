# EasyRadPy

A simple AutoHotkey script generator using Python and the `ahk` library.

## Features

- Creates AutoHotkey scripts programmatically
- Supports both 32-bit and 64-bit Windows executables
- Automated builds via GitHub Actions

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run all:
```bash
python -m main
```

Run only the AHK module:
```bash
python -m src.ahk
```

Run only the GUI module:
```bash
python -m src.gui
```

Show reports with mock data:
```bash
python -m test.generate_tables
```

Run the crawler script:
```bash
python -m tools.crawler
```

## Building

The project uses GitHub Actions to automatically build executables for both 32-bit and 64-bit Windows. You can find the latest builds in the Actions tab of this repository. 