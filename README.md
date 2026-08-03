# NoNetVoice

This tool converts voice to text without an internet connection.

## Downloading Models

Download the language models from the official Vosk website. You need to visit https://alphacephei.com/vosk/models. Choose the models for your preferred languages.

## File Structure

Make a folder named `models` next to the downloaded executable file. Extract the language archives into this folder. Each language needs its own subfolder.

Correct file placement:

    NoNetVoice-Executable
    models/
      model_en/
        am/
        conf/
        graph/
        ivector/
      model_uk/
        am/
        conf/
        graph/
        ivector/

## Running the Application

Download the compiled application from the Releases page in this repository. Run the executable file corresponding to your operating system. Linux requires running the file through the terminal with administrative privileges. macOS requires granting accessibility permissions in the system security settings.

## Instructions

Press and release the right Alt key to start or stop recording. A short beep confirms the state change. To switch between installed languages, hold the right Alt key for one second. A double beep confirms the switch.

## Automatic Startup

You can configure the application to launch automatically when your system boots. Configure your operating system's built-in task scheduling tools to run the executable file at startup. For Windows, configure the Task Scheduler. For Linux, configure cron. For macOS, configure Automator or launchd.
