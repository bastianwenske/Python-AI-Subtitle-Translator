# Python AI Subtitle Translator

This project is a Python script that processes video files by converting them from MP4 to MKV format, normalizing subtitles, translating subtitles from German to English using Azure Translator, and muxing the translated subtitles back into the video file.

## Features

- Convert MP4 files to MKV format using FFmpeg.
- Normalize subtitles by removing HTML content.
- Translate subtitles from German to English using Azure Translator.
- Mux the translated subtitles back into the video file.

## Requirements

- Python 3.6+
- FFmpeg
- Azure Translator API credentials

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/ai-subtitle-translator.git
    cd ai-subtitle-translator
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Ensure FFmpeg is installed and available in your system's PATH.

## Usage

1. Prepare your video files and subtitles in the working directory.

2. Run the script with the required arguments:
    ```sh
    python main.py --working-directory /path/to/working/directory --video-format mp4 --azure-translator-endpoint https://your-translator-endpoint.cognitiveservices.azure.com --azure-api-key your-azure-api-key
    ```

### Arguments

- `--working-directory`: Directory containing the video files and subtitles.
- `--video-format`: Format of the video files (e.g., mp4, mkv).
- `--azure-translator-endpoint`: Endpoint for the Azure Translator API.
- `--azure-api-key`: Key for the Azure Translator API.
- `--debug`: Set the log level to debug.

## Example

```sh
python [main.py](http://_vscodecontentref_/0) --working-directory ./videos --video-format mp4 --azure-translator-endpoint https://api.cognitive.microsofttranslator.com --azure-api-key YOUR_API_KEY