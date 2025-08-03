TRYING TO GET A QUICK LOOK? yea its perfectly fine. here you go.




<img width="517" height="507" alt="Screenshot 2025-08-02 181702" src="https://github.com/user-attachments/assets/ba2ee89d-270d-4a97-853d-35a57362298c" />

<img width="396" height="218" alt="Screenshot 2025-08-02 201454" src="https://github.com/user-attachments/assets/832beb8a-4c24-4118-8a01-9223c21fd977" />
<img width="516" height="505" alt="Screenshot 2025-08-02 181714" src="https://github.com/user-attachments/assets/b8e24ebd-d68c-4ec1-9c90-9062ba06978f" />

<img width="399" height="220" alt="Screenshot 2025-08-02 201504" src="https://github.com/user-attachments/assets/f40daac1-17e2-4374-8992-c03694f0c4bc" />












MultiMidi - MIDI to Virtual Piano Key Mapper (OneDir Build)
MultiMidi is a lightweight desktop app that converts MIDI input (from files or live devices) into virtual keyboard key presses. This lets you control virtual pianos, Roblox games, or any keyboard-driven software with your MIDI controller.

This repository provides the source code and instructions for building a standalone OneDir executable with PyInstaller, allowing easy distribution and use without requiring a Python install on the target machine.

Features
Play MIDI files or use live MIDI devices as input

Customizable hotkeys for stopping and pausing playback

Dark mode UI toggle

Clean, modern interface built with CustomTkinter

Portable standalone executable (OneDir folder)

Using the OneDir Executable
Build the app using PyInstaller (instructions below), or download the pre-built OneDir folder (if available).

Inside the OneDir folder, run MultiMidi.exe to launch the app.

Use the GUI to select MIDI files, toggle live MIDI device mode, and configure hotkeys.

Logs and status messages appear in the built-in console window.

/////////////////////////////////////////////////////////////////

If you dont feel safe downloading the full version, you can do it yourself!

Building the OneDir Executable from Source!

To create a standalone OneDir executable from the Python source file (MultiMidi.py), follow these steps:

Why OneDir Instead of OneFile?
OneDir bundles your app and all dependencies into a single folder. This approach avoids issues with large dependencies and complex imports (like MIDI backends and GUI libraries).

The OneFile option compresses everything into a single .exe, but this can cause runtime problems such as missing files, slower startup, or crashes with libraries like mido, pynput, and customtkinter.

Therefore, OneDir is recommended for stability and easier troubleshooting.

Prerequisites
Make sure you have:

Python 3.8 or higher installed

Required Python packages installed (mido, pynput, customtkinter, keyboard, etc.)

You can install them all with:

bash
Copy
Edit
pip install -r requirements.txt
PyInstaller Command for OneDir Build
Run this command in your terminal or PowerShell, replacing MultiMidi.py with the path to your source file if needed:

bash
Copy
Edit
python -m PyInstaller --onedir --windowed --icon=Logo.ico \
--hidden-import=mido.backends.rtmidi \
--hidden-import=mido.backends.rtmidi._rtmidi \
--hidden-import=pynput.keyboard._win32 \
--hidden-import=pynput._util.win32 \
--hidden-import=pynput.mouse._win32 \
--hidden-import=pynput._util.win32_vista \
--hidden-import=pynput.keyboard._base \
--hidden-import=pynput.mouse._base \
--hidden-import=tkinter \
--hidden-import=tkinter.font \
--hidden-import=tkinter.ttk \
--hidden-import=tkinter.constants \
--hidden-import=keyboard \
MultiMidi.py
Output
The build output will be in the dist/MultiMidi folder.

Run MultiMidi.exe inside this folder to start the application.

The entire folder can be moved or shared; no separate Python install is needed on the target machine.
