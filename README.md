# NoNetVoice

This tool converts voice to text without an internet connection.

## Downloading Models

Download the language models from the official Vosk website. You need to visit https://alphacephei.com/vosk/models. Choose the models for your preferred languages.

## File Structure

Make a folder named `models` next to the downloaded executable file. Extract the language archives into this folder. Each language needs its own subfolder. Place the `punctuation.json` file in the same directory as the executable.

Correct file placement:

    NoNetVoice-Executable
    punctuation.json
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

Press and release the right Alt button to start or stop recording. A short beep confirms the state change. Hold the right Alt button for one second to display the language selection menu. The graphical interface allows you to select the active language from a dropdown list. The menu contains a checkbox to toggle visual status notifications. The menu contains a checkbox to disable the graphical popup. If you disable the menu, holding the right Alt button cycles through installed languages with a double beep.

## Punctuation and Macros

The tool supports custom punctuation and keyboard actions. You must place a file named `punctuation.json` next to the executable. This file maps spoken words to specific text symbols or keyboard actions. The script reads this file on startup.

Supported macros:
- `<SHIFT_ENTER>` simulates a soft line break.
- `<ENTER>` simulates pressing the Enter button to send a message or start a new paragraph.

Example format for `punctuation.json`:

```json
{
  "model_uk": {
    "кома": ",",
    "крапка": ".",
    "абзац": "<SHIFT_ENTER> <SHIFT_ENTER>",
    "відправити": "<ENTER>"
  },
  "model_en": {
    "comma": ",",
    "period": ".",
    "new line": "<SHIFT_ENTER>",
    "send message": "<ENTER>"
  }
}
```

## Automatic Startup

You can configure the application to launch automatically when your system boots. Configure your operating system task scheduling tools to run the executable file at startup. For Windows, configure the Task Scheduler. For Linux, configure cron. For macOS, configure Automator or launchd.
