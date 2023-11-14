# Android App Manager

![Preview](preview.png)

Android App Manager is a Python-based GUI application that allows users to manage their Android applications via ADB (Android Debug Bridge). It provides functionality to list, disable, and enable applications.

## Features

- List all installed applications on your Android device.
- Disable any application.
- Enable any application.
- Search for applications.

## Requirements

- Python 3.x
- Tkinter
- ttkthemes
- ADB installed and set in PATH

## Usage

1. Connect your Android device to your computer.
2. Enable USB debugging on your Android device.
3. Run the script.

\`\`\`bash
python app_manager.py
\`\`\`

The application will start and display a GUI.

- Click "Update List" to fetch and display a list of all installed applications on your Android device.
- Select an application from the list and click "Disable App" to disable the selected application.
- Select an application from the list and click "Enable App" to enable the selected application.
- Use the "Search" box to filter the applications list.

## Note

This tool uses ADB commands to manage applications. Please ensure you understand the implications of disabling/enabling applications on your Android device. Always use this tool responsibly.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Disclaimer

This tool is for educational purposes only. The developer is not responsible for any misuse of this tool.
