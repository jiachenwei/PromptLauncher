# Prompt Launcher

**Prompt Launcher** is a desktop application based on PyQt6 for managing and quickly accessing custom prompts.

## Features
- **Group Management**: Create, delete and rename groups.
- **Prompt Search**: Quickly search prompts within the current group.
- **Hotkey Support**: Use a global hotkey to show or hide the main window.
- **Usage Count**: Records the usage count of each prompt.
- **Tray Icon**: Access the app from the system tray.
- **SSH Backup**: Periodically back up prompt data via SSH/SFTP and display the last sync time and status in the interface.

## Installation

### Environment Setup
1. Create and activate a Python environment:
   ```bash
   conda create -n pyqt6_env python=3.10
   conda activate pyqt6_env
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install PyInstaller if you want to package the application:
   ```bash
   pip install pyinstaller
   ```

### Building the Application
Run the following command to build the application:
```bash
pyinstaller PromptLauncher.spec
```
After building, the executable will be located in the `dist/PromptLauncher/` directory.

## Usage
1. After launching the application, the main window shows all groups and their prompts.
2. Use the search box to quickly find prompts.
3. Double-click a prompt to edit it.
4. Use the tray icon or the global hotkey (default `Ctrl+Alt+P`) to show or hide the main window.

## Project Structure
```plaintext
PromptLauncher/
├── gui.py                        # Main window logic
├── main.py                       # Program entry point
├── tray.py                       # System tray logic
├── hotkey.py                     # Global hotkey management
├── hotkey_dialog.py              # Custom hotkey dialog
├── ssh_backup.py                 # SSH backup management
├── prompt.json                   # Prompt data file
├── requirements.txt              # Dependency list
├── PromptLauncher.spec           # PyInstaller build config
├── icon.png                      # Application icon
├── README.md                     # Project documentation (Chinese)
├── README_EN.md                  # Project documentation (English)
├── dialogs/                      # Dialog modules
│   ├── new_prompt_dialog.py      # Create prompt dialog
│   ├── edit_prompt_dialog.py     # Edit prompt dialog
│   ├── ssh_config_dialog.py      # SSH configuration dialog
│   └── custom_hotkey_dialog.py   # Custom hotkey dialog
└── widgets/                      # Custom widgets
    └── prompt_item_widget.py     # Prompt list item widget
```

## License
This project is licensed under the [Apache License](LICENSE).
