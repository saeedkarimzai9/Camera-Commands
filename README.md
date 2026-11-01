# Camera Commands

A small Windows desktop controller for a webcam or capture device. It applies effects and sends the processed video to a virtual camera, so apps such as Discord, Zoom, and browsers can select it as their camera.

## Features

- Pixelate effect with adjustable block size
- Invert colors
- Freeze / unfreeze controls
- Single-frame stepping while frozen
- Camera device selection
- Optional global mouse controls: left mouse button freezes the output; right mouse button resumes live video
- Keyboard shortcuts: F advances one frame while frozen, Space toggles freeze, Esc quits

## Important: virtual camera setup

Install OBS Studio and start OBS Virtual Camera (or install another compatible virtual-camera driver) before launching this app. This program sends frames to that virtual camera using pyvirtualcam; it does not install a camera driver itself.

## Install (Windows 10/11)

1. Install Python 3.10 or newer from https://www.python.org/downloads/ . During setup, enable Add Python to PATH.
2. Install OBS Studio from https://obsproject.com/ .
3. Download or clone this repository.
4. Double-click run_windows.bat.
5. In the app, choose your camera and press Start camera.
6. In OBS, Discord, Zoom, or another app, choose OBS Virtual Camera as the camera.

The first launch installs the Python packages from requirements.txt.

## Controls

- Click Freeze to hold the current output frame.
- Click Unfreeze to return to live video.
- While frozen, click Step 1 frame or press F to advance one input frame and remain frozen.
- Turn on Global mouse controls to use the left and right mouse buttons anywhere: left = freeze, right = unfreeze.

The mouse controls are optional because they capture global mouse clicks while enabled. Turn them off if they interfere with other apps.

## Troubleshooting

- No virtual camera found: Start OBS Virtual Camera first. If pyvirtualcam cannot connect, check that OBS Virtual Camera is installed and running.
- Black preview: Check the selected camera index and close other apps that may be using the webcam.
- Camera busy: Close apps currently using the webcam, then restart Camera Commands.
- Permission error: Allow desktop apps to use the camera in Windows Settings > Privacy & security > Camera.

## Notes

This is a starter project. Camera device indices and virtual-camera support depend on the Windows drivers installed on your PC.
