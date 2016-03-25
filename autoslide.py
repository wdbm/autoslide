#!/usr/bin/env python

"""
################################################################################
#                                                                              #
# autoslide                                                                    #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# This program produces automatic slide presentations.                         #
#                                                                              #
# copyright (C) 2015 William Breaden Madden                                    #
#                                                                              #
# This software is released under the terms of the GNU General Public License  #
# version 3 (GPLv3).                                                           #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for     #
# more details.                                                                #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# <http://www.gnu.org/licenses/>.                                              #
#                                                                              #
################################################################################

Usage:
    program [options]

Options:
    -h, --help               Show this help message.
    --version                Show the version and exit.
    -v, --verbose            Show verbose logging.
    -s, --silent             silent
    -u, --username=USERNAME  username
    -i, --input=FILE         Markdown slides file [default: slides.md]
    -o, --output=FILE        slides video file    [default: slides.mp4]
    --normalvoice            engage normal voice (not deep phaser voice)
"""

name    = "autoslide"
version = "2016-03-25T1717Z"
logo    = None

import contextlib
import datetime
import docopt
import inspect
import logging
import os
import subprocess
import sys
import time
import wave

from   moviepy.editor import *
from   moviepy.audio.tools.cuts import find_audio_period
import propyte
import pyprel
import shijian
import technicolor

def main(options):

    global program
    program = propyte.Program(
        options = options,
        name    = name,
        version = version,
        logo    = logo
    )
    global log
    from propyte import log

    # access options and arguments
    Markdown_filename = options["--input"]
    video_filename    = options["--output"]
    normal_voice      = options["--normalvoice"]

    with open(Markdown_filename, "r") as Markdown_file:
        Markdown = Markdown_file.read()

    pyprel.print_line()
    log.info("\nMarkdown input:\n\n{Markdown}".format(Markdown = Markdown))
    pyprel.print_line()
    
    # Create Beamer slides from the Markdown file.
    Markdown_file_to_Beamer_slides(
        Markdown_filename = Markdown_filename,
        filename          = "slides.pdf"
    )

    # Convert Beamer slides to images.
    command = [
        "convert",
        "-density",
        "1200",
        "slides.pdf",
        "-quality",
        "85",
        "-scale",
        "1200x900",
        "slide_%01d.png"
    ]
    subprocess.call(command)
    
    # Determine the number of slides and split the Markdown into slides.
    Markdown_split_by_hash = Markdown.split("#")
    slides = [slide for slide in Markdown_split_by_hash if slide is not ""]
    number_of_slides = len(slides)
    log.info("number of slides: {number_of_slides}".format(
        number_of_slides = number_of_slides
    ))

    # Convert individual slides to sounds.    
    slide_number = -1
    slide_sound_filenames = []
    for slide in slides:
        slide_number += 1
        filename = "slide_" + str(slide_number) + ".wav"
        slide_sound_filenames.append(filename)
        string_to_sound_file(
            text     = slide.rstrip('\n'),
            filename = filename
        )

    # Apply sound effects as specified.
    if normal_voice is not True:
        for slide_sound_filename in slide_sound_filenames:
            tmp_slide_sound_filename = shijian.propose_filename(
                filename = slide_sound_filename
            )
            command                      =\
                "sox "                   +\
                slide_sound_filename     +\
                " "                      +\
                tmp_slide_sound_filename +\
                " pitch -400 tempo 0.8 phaser 1 .5 4 .5 1 -s"
            result = subprocess.check_call(
                command,
                shell      = True,
                executable = "/bin/bash"
            )
            command                      =\
                "mv "                    +\
                tmp_slide_sound_filename +\
                " "                      +\
                slide_sound_filename
            result = subprocess.check_call(
                command,
                shell      = True,
                executable = "/bin/bash"
            )

    # Create video clips for each slide and its corresponding sound.
    video_clips = []
    slide_durations = []
    for slide_number in range(0, number_of_slides):
        log.debug("compose video clip of slide {slide_number}".format(
            slide_number = slide_number
        ))
        # Include image.
        slide_image_filename = "slide_" + str(slide_number) + ".png"
        log.debug("slide image: {filename}".format(
            filename = slide_image_filename
        ))
        # Include sound.
        slide_sound_filename = "slide_" + str(slide_number) + ".wav"
        log.debug("slide sound: {filename}".format(
            filename = slide_sound_filename
        ))
        image_clip = ImageClip(slide_image_filename)
        sound_clip = AudioFileClip(slide_sound_filename)
        # Determine the slide duration using the slide sound duration.
        duration  = sound_file_duration(slide_sound_filename)
        log.debug("slide duration: {duration} s".format(duration = duration))
        video_clip = image_clip.set_duration(duration)
        # Determine the slide start time by calculating the sum of the durations
        # of all previous slides.
        if slide_number != 0:
            video_start_time = sum(slide_durations[0:slide_number])
            log.debug("slide start time: {start_time} s".format(
                start_time = video_start_time
            ))
        else:
            video_start_time = 0
        video_clip = video_clip.set_start(video_start_time)
        video_clip = video_clip.set_audio(sound_clip)
        if slide_number == 0:
            video_clip = video_clip.fadein(0.3)
        video_clips.append(video_clip)
        slide_durations.append(duration)
    full_duration = sum(slide_durations)
    log.debug("slides full duration: {duration} s".format(
        duration = full_duration
    ))
    video = concatenate(video_clips)
    log.info("rendering video {filename}".format(
        filename = video_filename
    ))
    video.write_videofile(
        video_filename,
        fps         = 30,
        codec       = "mpeg4",
        audio_codec = "libvorbis"
    )

    # Remove junk.
    for slide_number in range(0, number_of_slides):
        slide_image_filename = "slide_" + str(slide_number) + ".png"
        command = [
            "rm",
            slide_image_filename
        ]
        subprocess.call(command)
        slide_sound_filename = "slide_" + str(slide_number) + ".wav"
        command = [
            "rm",
            slide_sound_filename
        ]
        subprocess.call(command)

    program.terminate()

def sound_file_duration(
    filename = None
    ):
    with contextlib.closing(wave.open(filename, 'r')) as soundFile:
        frames = soundFile.getnframes()
        rate = soundFile.getframerate()
        duration = float(frames / float(rate))
    return(duration)

def Markdown_file_to_Beamer_slides(
    Markdown_filename = None,
    filename          = None
    ):
    command = [
        "pandoc",
        "-t",
        "beamer",
        Markdown_filename,
        "-o",
        filename
    ]
    subprocess.call(command)

def string_to_sound_file(
    text     = None,
    filename = None
    ):
    command =\
        "echo \"" +\
        text +\
        "\" | sed -e 's/\([[:punct:]]\)//g' | text2wave -scale 1 -o " +\
        filename
    result = subprocess.check_call(
        command,
        shell = True,
        executable = "/bin/bash"
    )

if __name__ == "__main__":

    options = docopt.docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
