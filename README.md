# Vivid Downloader - APK Build Instructions

This is a Kivy-based video downloader application that can be built into an Android APK. Due to platform limitations on Windows, building the APK requires a Linux environment.

## Prerequisites

- Python 3.7 or higher
- Kivy
- yt-dlp
- Buildozer

## Building the APK - Recommended Approaches

### Option 1: GitHub Actions (Easiest for Windows users)

1. Push this repository to GitHub
2. The included GitHub Actions workflow will automatically build the APK
3. Download the built APK from the Actions artifacts

### Option 2: Linux Environment (VM or WSL)

1. Set up a Linux environment (Ubuntu recommended)
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y build-essential git python3 python3-dev python3-pip
   pip3 install buildozer cython kivy python-for-android yt-dlp
   ```
3. Navigate to the project directory
4. Build the APK:
   ```bash
   buildozer android debug
   ```
5. Find the APK in the `bin/` directory

### Option 3: Google Colab

1. Upload the project files to Google Drive
2. Open Google Colab
3. Mount Google Drive and navigate to your project
4. Install dependencies and build the APK in the cloud

## Project Structure

- `main.py`: Main application code
- `buildozer.spec`: Build configuration
- `.github/workflows/build.yml`: GitHub Actions workflow for automatic building

## Application Features

- Download videos from various platforms using yt-dlp
- Queue management for multiple downloads
- Quality selection for videos
- Progress tracking
- Android storage integration

## Troubleshooting

If you encounter issues during the build process:

1. Ensure all dependencies are installed correctly
2. Check that the Android SDK and NDK paths are properly configured
3. Verify that your system has enough RAM (at least 4GB recommended)
4. Make sure you're using a Linux environment as Buildozer doesn't work directly on Windows

For any issues, please refer to the Kivy and Buildozer documentation.