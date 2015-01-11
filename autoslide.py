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
    -h, --help                Show this help message.
    --version                 Show the version and exit.
    -v, --verbose             Show verbose logging.
    -u, --username=USERNAME   username
    -i, --input=FILE          Markdown slides file [default: slides.md]
    -o, --output=FILE         slides video file [default: slides.mp4]
    --normalvoice             engage normal voice (not deep phaser voice)
"""

name    = "autoslide"
version = "2015-01-11T0409Z"

import os
import sys
import subprocess
import time
import datetime
import logging
import technicolor
import inspect
import docopt
import pyprel
import shijian
from   moviepy.editor import *
from   moviepy.audio.tools.cuts import find_audio_period
import wave
import contextlib

def main(options):

    global program
    program = Program(options = options)

    with open(program.MarkdownFileName, "r") as MarkdownFile:
        Markdown = MarkdownFile.read()

    pyprel.printLine()
    log.info("\nMarkdown input:\n\n{Markdown}".format(Markdown = Markdown))
    pyprel.printLine()
    
    # Create Beamer slides from the Markdown file.
    MarkdownFileToBeamerSlides(
        MarkdownFileName = program.MarkdownFileName,
        fileName         = "slides.pdf"
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
    MarkdownSplitByHash = Markdown.split("#")
    slides = [slide for slide in MarkdownSplitByHash if slide is not ""]
    numberOfSlides = len(slides)
    log.info("number of slides: {numberOfSlides}".format(
        numberOfSlides = numberOfSlides
    ))

    # Convert individual slides to sounds.    
    slideNumber = -1
    slideSoundFileNames = []
    for slide in slides:
        slideNumber += 1
        fileName = "slide_" + str(slideNumber) + ".wav"
        slideSoundFileNames.append(fileName)
        stringToSoundFile(
            text     = slide.rstrip('\n'),
            fileName = fileName
        )

    # Apply sound effects as specified.
    if program.normalvoice is not True:
        for slideSoundFileName in slideSoundFileNames:
            tmp_slideSoundFileName = shijian.proposeFileName(
                fileName = slideSoundFileName
            )
            command =\
                "sox " +\
                slideSoundFileName +\
                " " +\
                tmp_slideSoundFileName +\
                " pitch -400 tempo 0.8 phaser 1 .5 4 .5 1 -s"
            result = subprocess.check_call(
                command,
                shell      = True,
                executable = "/bin/bash"
            )
            command =\
                "mv " +\
                tmp_slideSoundFileName +\
                " " +\
                slideSoundFileName
            result = subprocess.check_call(
                command,
                shell      = True,
                executable = "/bin/bash"
            )

    # Create video clips for each slide and its corresponding sound.
    videoClips = []
    slideDurations = []
    for slideNumber in range(0, numberOfSlides):
        log.debug("compose video clip of slide {slideNumber}".format(
            slideNumber = slideNumber
        ))
        # Include image.
        slideImageFileName = "slide_" + str(slideNumber) + ".png"
        log.debug("slide image: {fileName}".format(
            fileName = slideImageFileName
        ))
        # Include sound.
        slideSoundFileName = "slide_" + str(slideNumber) + ".wav"
        log.debug("slide sound: {fileName}".format(
            fileName = slideSoundFileName
        ))
        imageClip = ImageClip(slideImageFileName)
        soundClip = AudioFileClip(slideSoundFileName)
        # Determine the slide duration using the slide sound duration.
        duration  = soundFileDuration(slideSoundFileName)
        log.debug("slide duration: {duration} s".format(duration = duration))
        videoClip = imageClip.set_duration(duration)
        # Determine the slide start time by calculating the sum of the durations
        # of all previous slides.
        if slideNumber != 0:
            videoStartTime = sum(slideDurations[0:slideNumber])
            log.debug("slide start time: {startTime} s".format(
                startTime = videoStartTime
            ))
        else:
            videoStartTime = 0
        videoClip = videoClip.set_start(videoStartTime)
        videoClip = videoClip.set_audio(soundClip)
        if slideNumber == 0:
            videoClip = videoClip.fadein(0.3)
        videoClips.append(videoClip)
        slideDurations.append(duration)
    fullDuration = sum(slideDurations)
    log.debug("slides full duration: {duration} s".format(
        duration = fullDuration
    ))
    video = concatenate(videoClips)
    log.info("rendering video {fileName}".format(
        fileName = program.videoFileName
    ))
    video.write_videofile(
        program.videoFileName,
        fps         = 30,
        codec       = "mpeg4",
        audio_codec = "libvorbis"
    )

    # Remove junk.
    for slideNumber in range(0, numberOfSlides):
        slideImageFileName = "slide_" + str(slideNumber) + ".png"
        command = [
            "rm",
            slideImageFileName
        ]
        subprocess.call(command)
        slideSoundFileName = "slide_" + str(slideNumber) + ".wav"
        command = [
            "rm",
            slideSoundFileName
        ]
        subprocess.call(command)

    program.terminate()

def soundFileDuration(
    fileName = None
    ):
    with contextlib.closing(wave.open(fileName, 'r')) as soundFile:
        frames = soundFile.getnframes()
        rate = soundFile.getframerate()
        duration = float(frames / float(rate))
    return(duration)

def MarkdownFileToBeamerSlides(
    MarkdownFileName = None,
    fileName = None
    ):
    command = [
        "pandoc",
        "-t",
        "beamer",
        MarkdownFileName,
        "-o",
        fileName
    ]
    subprocess.call(command)

def stringToSoundFile(
    text     = None,
    fileName = None
    ):
    command =\
        "echo \"" +\
        text +\
        "\" | sed -e 's/\([[:punct:]]\)//g' | text2wave -scale 1 -o " +\
        fileName
    result = subprocess.check_call(
        command,
        shell = True,
        executable = "/bin/bash"
    )

class Program(object):

    def __init__(
        self,
        parent  = None,
        options = None
        ):

        # internal options
        self.displayLogo           = True

        # clock
        global clock
        clock = shijian.Clock(name = "program run time")

        # name, version, logo
        if "name" in globals():
            self.name              = name
        else:
            self.name              = None
        if "version" in globals():
            self.version           = version
        else:
            self.version           = None
        if "logo" in globals():
            self.logo              = logo
        elif "logo" not in globals() and hasattr(self, "name"):
            self.logo              = pyprel.renderBanner(
                                         text = self.name.upper()
                                     )
        else:
            self.displayLogo       = False
            self.logo              = None

        # options
        self.options               = options
        self.userName              = self.options["--username"]
        self.verbose               = self.options["--verbose"]
        self.MarkdownFileName      = self.options["--input"]
        self.videoFileName         = self.options["--output"]
        self.normalvoice           = self.options["--normalvoice"]

        # default values
        if self.userName is None:
            self.userName = os.getenv("USER")

        # logging
        global log
        log = logging.getLogger(__name__)
        logging.root.addHandler(technicolor.ColorisingStreamHandler())

        # logging level
        if self.verbose:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

        self.engage()

    def engage(
        self
        ):
        pyprel.printLine()
        # logo
        if self.displayLogo:
            log.info(pyprel.centerString(text = self.logo))
            pyprel.printLine()
        # engage alert
        if self.name:
            log.info("initiate {name}".format(
                name = self.name
            ))
        # version
        if self.version:
            log.info("version: {version}".format(
                version = self.version
            ))
        log.info("initiation time: {time}".format(
            time = clock.startTime()
        ))

    def terminate(
        self
        ):
        clock.stop()
        log.info("termination time: {time}".format(
            time = clock.stopTime()
        ))
        log.info("time full report:\n{report}".format(
            report = shijian.clocks.report(style = "full")
        ))
        log.info("time statistics report:\n{report}".format(
            report = shijian.clocks.report()
        ))
        log.info("terminate {name}".format(
            name = self.name
        ))
        pyprel.printLine()

if __name__ == "__main__":

    options = docopt.docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
