import argparse
import re
import os
import pysrt
import glob
import logging
import coloredlogs
import subprocess
import multiprocessing
from pymkv import MKVFile, MKVTrack
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.core.exceptions import HttpResponseError


def convert_mp4_to_mkv(input_file, output_file):
    """
    Convert an MP4 file to MKV format using FFmpeg.

    Args:
        input_file (str): Path to the input MP4 file.
        output_file (str): Path to the output MKV file.
    """
    if not os.path.isfile(input_file):
        logging.error("Input file '%s' not found.", input_file)
        return

    num_threads = multiprocessing.cpu_count()

    command = [
        'ffmpeg', '-i', input_file,
        '-c', 'copy',
        '-threads', str(num_threads),
        output_file
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        process.wait()
        if process.returncode == 0:
            logging.info("Conversion successful: '%s'", output_file)
        else:
            logging.error("Conversion failed with code: %s", process.returncode)
    except FileNotFoundError:
        logging.error("FFmpeg is not installed or not in the PATH.")
    except Exception as e:
        logging.error("Error during conversion: %s", e)

def normalize_subtitles(subtitles):
    """
    Remove all HTML content from subtitles.

    Args:
        subtitles (pysrt.SubRipFile): SubRipFile object containing subtitles.

    Returns:
        pysrt.SubRipFile: SubRipFile object with normalized subtitles.
    """
    pattern = r"<[^>]+>"
    for sub in subtitles:
        sub.text = re.sub(pattern, '', sub.text)
    return subtitles

def translate_text(client, text, to_language=["en"]):
    """
    Translate text from German to the specified language using Azure Translator.

    Args:
        client (TextTranslationClient): Azure Text Translation client.
        text (str): Text to be translated.
        to_language (list): List of target languages for translation.

    Returns:
        list: List of translated text.
    """
    try:
        response = client.translate(
            body=[{"Text": text}],
            from_language="de",
            to_language=to_language
        )
        return [item['translations'][0]['text'] for item in response]
    except HttpResponseError as e:
        logging.error("Translation error: %s", e)
        return []

def process_video_file(client, file, args, output_directory):
    """
    Process a single video file: convert, normalize subtitles, translate, and mux.

    Args:
        client (TextTranslationClient): Azure Text Translation client.
        file (str): Path to the video file.
        args (argparse.Namespace): Parsed command-line arguments.
        output_directory (str): Directory to save the output files.
    """
    name = os.path.splitext(os.path.basename(file))[0]

    video_input_path = f"{args.working_directory}/{name}.{args.video_format}"
    video_input_path_mkv = video_input_path.replace('mp4', 'mkv')
    srt_german_path = f"{args.working_directory}/{name}.srt"
    srt_english_path = f"{args.working_directory}/{name}_en.srt"
    srt_combined_path = f"{args.working_directory}/{name}_combined.srt"
    video_output_path = f"{output_directory}/{name}.mkv"

    if os.path.exists(video_output_path):
        return

    logging.info("- Started operations on file %s", name)

    if args.video_format == "mp4":
        convert_mp4_to_mkv(video_input_path, video_input_path_mkv)

    mkv = MKVFile(video_input_path_mkv)
    for track in mkv.tracks:
        if track.track_type == "audio":
            track.track_name = "Deutsch"

    subs_german = normalize_subtitles(pysrt.open(srt_german_path))
    subs_german.save(srt_german_path)
    subs_german_list = [line.text for line in subs_german]
    subs_english_list = translate_text(client, subs_german_list)

    subs_english = subs_german

    for index, subtitle in enumerate(subs_english):
        subtitle.text = subs_english_list[index]

    subs_english.save(srt_english_path)

    subs_combined = subs_german
    for index, subtitle in enumerate(subs_combined):
        subtitle.text = f"<font color='#42f5f2'>{subs_german_list[index]}</font>\n<font color='#b042f5'>{subs_english_list[index]}</font>"

    subs_combined.save(srt_combined_path)

    english_subtitle_track = MKVTrack(srt_english_path)
    english_subtitle_track.track_name = "Englisch"
    mkv.add_track(english_subtitle_track)

    combined_subtitle_track = MKVTrack(srt_combined_path)
    combined_subtitle_track.track_name = "Deutsch + Englisch"
    mkv.add_track(combined_subtitle_track)

    german_subtitle_track = MKVTrack(srt_german_path)
    german_subtitle_track.track_name = "Deutsch"
    mkv.add_track(german_subtitle_track)

    mkv.mux(video_output_path)
    logging.info("Finished operations of file %s", name)

if __name__ == "__main__":
    coloredlogs.install(level='INFO')

    parser = argparse.ArgumentParser(description='Python AI Subtitle Translator')
    parser.add_argument('--working-directory', type=str, help='Directory containing the video files')
    parser.add_argument('--video-format', type=str, help='Format of the video files. eg. mp4, mkv')
    parser.add_argument('--azure-translator-endpoint', type=str, help='Endpoint for the Azure Translator API eg. https:/xyz.cognitiveservices.azure.com')
    parser.add_argument('--azure-api-key', type=str, help='Key for the Azure Translator API')
    parser.add_argument('--debug', action=coloredlogs.set_level(logging.DEBUG), help='Set the log level to debug')
    args = parser.parse_args()

    output_directory = rf"{args.working_directory}/output"
    os.makedirs(f"{args.working_directory}/output", exist_ok=True)

    credential = AzureKeyCredential(args.azure_api_key)
    client = TextTranslationClient(endpoint=args.azure_translator_endpoint, credential=credential)

    video_files = sorted(glob.glob(os.path.join(args.working_directory, f'*.{args.video_format}')))
    for file in video_files:
        process_video_file(client, file, args, output_directory)