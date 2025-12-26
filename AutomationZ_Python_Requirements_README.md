# Python & GUI Requirements (AutomationZ)

AutomationZ tools are written in **Python** and use a **simple graphical interface (Tkinter / ttk)**.  
This document explains **what is required**, **how to install it**, and **how to verify everything works** before running any AutomationZ tool.

If you already have Python installed and AutomationZ starts correctly, you can ignore this file.

---

## Overview (Quick Start)

### You need:
- Python **3.9 or newer**
- Tkinter (GUI library)
- Windows, Linux, or macOS

### Quick test:
Run this command:
```bash
python -m tkinter
```

If a small window opens → **you are ready to use AutomationZ**.

---

## Why Python Is Required

AutomationZ is designed as:
- Open-source
- Lightweight
- Long-term stable
- Easy to inspect and modify

Python allows AutomationZ to:
- Run for years without breaking
- Work across operating systems
- Avoid heavy external dependencies

---

## Installing Python

### Windows (Recommended)

1. Download Python from:
   https://www.python.org/downloads/
2. Run the installer  
3. **IMPORTANT:** Check the box **Add Python to PATH**
4. Click **Install**

Verify installation:
```bash
python --version
```

---

### Linux (Debian / Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version
```

---

### macOS

```bash
brew install python
python3 --version
```

---

## GUI Requirement: Tkinter (IMPORTANT)

AutomationZ uses **Tkinter / ttk** for its graphical interface.

### Windows
Tkinter is included by default with Python from python.org.

### Linux
```bash
sudo apt install python3-tk
```

### macOS (Homebrew)
```bash
brew install python-tk
```

---

## Testing Tkinter

```bash
python -m tkinter
```

If a small window appears, Tkinter is working correctly.

---

## Common Problems

### “python is not recognized”
- Python not installed
- Python not added to PATH

### GUI does not open
- Tkinter missing
- Install python3-tk (Linux) or python-tk (macOS)

---

AutomationZ Project  
https://github.com/DayZ-AutomationZ
