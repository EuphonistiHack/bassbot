#! /usr/bin/env python
# This is a simple demonstration on how to stream
# audio from microphone and then extract the pitch
# and volume directly with help of PyAudio and Aubio
# Python libraries. The PyAudio is used to interface
# the computer microphone. While the Aubio is used as
# a pitch detection object. There is also NumPy
# as well to convert format between PyAudio into
# the Aubio.
import aubio
import numpy as num
import pyaudio
import sys
from threading import Thread, Event
import argparse
import random
import datetime

NOTE_NAMES = 'C C# D D# E F F# G G# A A# B'.split()

# Track all the notes on a per-fret basis. <n>_NOTES will give you the note by
# fret.  0 is open, 1 is first fret, etc.
# ok, so there are more than 18 frets, but who's actually meedly meedlying up
# in the stratosphere with the 24th fret?
NUM_FRETS = 18
G_NOTES = 'G2 G#2 A2 A#2 B2 C3 C#3 D3 D#3 E3 F3 F#3 G3 G#3 A3 A#3 B3 C4 C#4'.split()
D_NOTES = 'D2 D#2 E2 F2 F#2 G2 G#2 A2 A#2 B2 C3 C#3 D3 D#3 E3 F3 F#3 G3 G#3'.split()
A_NOTES = 'A1 A#1 B1 C2 C#2 D2 D#2 E2 F2 F#2 G2 G#2 A2 A#2 B2 C3 C#3 D3 D#3'.split()
E_NOTES = 'E1 F1 F#1 G1 G#1 A1 A#1 B1 C2 C#2 D2 D#2 E2 F2 F#2 G2 G#2 A2 A#2'.split()
B_NOTES = 'B0 C1 C#1 D1 D#1 E1 F1 F#1 G1 G#1 A1 A#1 B1 C2 C#2 D2 D#2 E2 E#2'.split()
# String is mostly used to convert string number to name
STRING_LIST = 'E A D G'.split()
# String fret list is used to generate a random note on a random fret.
# so [0][3] will give you the E string, fret 3, or an G1
STRING_FRET_LIST = [E_NOTES, A_NOTES, D_NOTES, G_NOTES]

# The chord shape will give an offset from the root chord in [string][fret]
# format.  For example, a C major 7 will contain the root note (C), then a note
# one string up and one fret down (E) [1][-1], then a note one string up and
# two strings down from the root (G): [1][2], then a note two strings up and
# one string down (B): [2][1], and ending on a note two strings up and two
# strings down (C): [2][2]

# hi/lo/mid convention:
# low is anything from B0 to C#2.  Mid is anything from D2 to C#3.  High is
# anything from
MAJOR7_SHAPE = [[1,-1], [1,2], [2,1], [2,2]]
DOM7_SHAPE = [[1,-1], [1,2], [2,0], [2,2]]
MINOR7_SHAPE = [[1,-2], [1,2], [2,0], [2,2]]
MINOR7FLAT5_SHAPE = [[1,-2], [1,1], [2,0], [2,2]]

# some functions I found from a ukelele tuner app, all of which are based on
# https://newt.phys.unsw.edu.au/jw/notes.html
# These are used to convert frequencies to midi numbers and note names
def freq_to_number(f): return 69 + 12*num.log2(f/440.0)
def number_to_freq(n): return 440 * 2.0**((n-69)/12.0)
def note_name(n): return NOTE_NAMES[n % 12] + str(int(n/12 - 1))

# Some constants for setting the PyAudio capture and aubio note detection
# parameters
BUFFER_SIZE             = 4096*2
CHANNELS                = 1
FORMAT                  = pyaudio.paFloat32
METHOD                  = "default"
SAMPLE_RATE             = 44100
HOP_SIZE                = BUFFER_SIZE//2
PERIOD_SIZE_IN_FRAME    = HOP_SIZE


class AudioHandler:
    """Set up mic input, take samples when tick is called, provide freq and vol"""
    def __init__(self):
         # Initiating PyAudio object.
        pA = pyaudio.PyAudio()
        # Open the microphone stream.
        self.mic = pA.open(format=FORMAT, channels=CHANNELS,
                rate=SAMPLE_RATE, input=True,
                frames_per_buffer=PERIOD_SIZE_IN_FRAME)

        # Initiating Aubio's pitch detection object.
        self.pDetection = aubio.pitch(METHOD, BUFFER_SIZE,
            HOP_SIZE, SAMPLE_RATE)
        # Set unit.
        self.pDetection.set_unit("Hz")
        # Frequency under -40 dB will considered
        # as a silence.
        self.pDetection.set_silence(-40)

    def processAudio(self):
        # Always listening to the microphone.
        data = self.mic.read(PERIOD_SIZE_IN_FRAME)
        # Convert into number that Aubio understand.
        samples = num.fromstring(data,
            dtype=aubio.float_type)
        # Finally get the pitch.
        pitch = self.pDetection(samples)[0]
        # Compute the energy (volume)
        # of the current frame.
        volume = num.sum(samples**2)/len(samples)
        return pitch, volume

# This will process the audio on the input stream.  It will block until a note
# is detected with a sufficient degree of confidence, then return the name of
# that note.
#
# CONFIDENCE_LEVEL is used to determine how many consecutive readings of a note
# must be received before returning.  This is to prevent stray sharps and flats
# from being returned, as I normally see one sample worth of junk before the
# processAudio() function returns the correct result.
def waitForNote(aHandler, ignore = None):
    resultList = []
    CONFIDENCE_LEVEL = 5
    # invoke processAudio on repeat.
    # Track the results in an array.  If you match 5 in a row, that's the result
    # disregard if volume is 0
    while True:
        result = aHandler.processAudio()
        pitch = result[0]
        volume = result[1]

        # If no note is detected, keep processing audio
        if pitch == 0.0:
            continue
        n = freq_to_number(pitch)
        n0 = int(round(n))
        noteName = note_name(n0)
        if noteName == ignore:
            continue
        resultList.insert(0, noteName)
        #print(noteName + " list so far: " + str(resultList))
        if len(resultList) >= CONFIDENCE_LEVEL:
            # Count the number of 'noteName' in list.  if same as length, then
            # we have all readings the same note at the required confidence
            # level, so return the note.  Otherwise, pop the last entry and cont
            #print noteName
            if (resultList.count(noteName) == len(resultList)):
                return noteName
            resultList.pop()

# This will process the audio and return once it is confident that the user has
# muted their strings.
#
# Similar to waitForNote, this function will wait for CONFIDENCE_LEVEL
# consecutive samples returning that nothing is breaking the noise floor before
# returning.
def waitForMute(aHandler):
    pitchList = []
    CONFIDENCE_LEVEL = 5
    # invoke processAudio on repeat.
    # Track the results in an array.  If you match 5 in a row, that's the result
    # disregard if volume is 0
    while True:
        result = aHandler.processAudio()
        pitch = result[0]
        volume = result[1]

        pitchList.insert(0, pitch)
        #print(str(pitch) + " list so far: " + str(pitchList))
        if len(pitchList) >= CONFIDENCE_LEVEL:
            # Count the number of 'noteName' in list.  if same as length, then
            # we have all readings the same note at the required confidence
            # level, so return the note.  Otherwise, pop the last entry and cont
            #print str(pitch)
            if (pitchList.count(0.0) == len(pitchList)):
                return
            pitchList.pop()

def chordFinder(aHanlder, level):
    result = False
    chordTones = []
    for i in range(5):
        chordTones.append('')
    #Root selection
    # Must be string 0:1
    # Must be fret 2:12, though 12th fret limit is a bit artificial
    #string = random.randrange(2)
    #fret = 2 + random.randrange(11)
    string = 0
    fret = 8

    chordRoot = STRING_FRET_LIST[string][fret]
    chordTones[0] = STRING_FRET_LIST[string][fret]
    chordTones[1] = STRING_FRET_LIST[string+MAJOR7_SHAPE[0][0]][fret+MAJOR7_SHAPE[0][1]]
    chordTones[2] = STRING_FRET_LIST[string+MAJOR7_SHAPE[1][0]][fret+MAJOR7_SHAPE[1][1]]
    chordTones[3] = STRING_FRET_LIST[string+MAJOR7_SHAPE[2][0]][fret+MAJOR7_SHAPE[2][1]]
    chordTones[4] = STRING_FRET_LIST[string+MAJOR7_SHAPE[3][0]][fret+MAJOR7_SHAPE[3][1]]
    print("root: " + chordRoot)
    print("tones: " + str(chordTones))

    return 0


# This function will handle all "Find the fret of the note" style levels.
# Currently:
#   Level 0: Play an open string E, A, D, or G.  Useful for novices who don't
#            have which string is which memorized yet.
#   Level 1: Play a given note on a given string, limited to the 4th fret.
#   Level 2: Play a given note on a given string, limited to the 12th fret
#   Level 3: Play a given note on a given string, limited to the 18th fret
# This function will return the amount of time it took the user to find the note
def fretFinder(aHandler, level):
    result = False

    # Start the timer to count how long the user takes
    start_time = datetime.datetime.now()

    # Select a random string, 1-4
    string = random.randrange(4)

    # Select the fret for that string
    if (level == 0):
        fret = random.randrange(5)
        prefix = ''
    elif (level == 1):
        fret = random.randrange(13)
        # Any mode with fret 12 or higher in play needs a high/low prefix to
        # differentiate between open string and the 12th+ fret
        if fret >= 12:
            prefix = 'high '
        else:
            prefix = 'low '
    elif (level == 2):
        fret = random.randrange(NUM_FRETS)
        if fret >= 12:
            prefix = 'high '
        else:
            prefix = 'low '
    else:
        print("dev made an oops- unknown level: " + str(level))
        return 0

    #If the user gets it wrong, ask for that same note until they get it right
    while result == False:
        toPlay = STRING_FRET_LIST[string][fret]
        print(STRING_LIST[string] + " string: " + prefix + toPlay)
        # Uncomment the below if you're a dirty dirty cheat
        # print('string ' + str(string+1) + ' fret ' + str(fret))
        played = waitForNote(aHandler)
        #print('played ' + played)
        if played == toPlay:
            result = True
            delta = datetime.datetime.now() - start_time
            elapsed_time = delta.total_seconds()
            print("correct!  played " + str(played) + " in " + str(elapsed_time) + " seconds")
        else:
            print("wrongzo!")
            print("   expected " + str(toPlay) + ', string ' + str(string+1) + ' fret ' + str(fret))
            print("   heard " + str(played))
        waitForMute(aHandler)

    return elapsed_time

# Main
# does main stuff
def main(args):

    # initialize the audio interface
    aHandler = AudioHandler()
    resultList = []

    # handle argument parsing, because we don't need no stinkin gui
    parser = argparse.ArgumentParser(description='bot some bass')
    parser.add_argument("--verbose", "-v", help="increase output verbosity",
                    action="store_true")
    parser.add_argument("--vverbose", "-vv", help="increase output verbosity",
                    action="store_true")
    parser.add_argument('-l', dest='level', default=0, action='store', type=int)
    args = parser.parse_args()
    level = args.level

    if level == 0:
        print("Level 0: Play the note listed!")
        print("  The answer will always be on one of the first 4 frets")
    elif level == 1:
        print("Level 1: Play the note listed!")
        print("  ... but we're sticking below 12 frets")
    elif level == 2:
        print("Level 2: Play the note listed!")
        print("  ... but we're sticking below " + str(NUM_FRETS) + " frets")
    elif level == 3:
        print("experimental!")
    else:
        print("well aren't we cheeky... you get level 0.")
        level = 0

    while True:
        # Run until the user control+c's
        try:
            if (args.vverbose):
                # In vverbose mode, just print what the user's playing so they
                # can validate system sanity
                result = aHandler.processAudio()
                pitch = result[0]
                volume = result[1]
                if (args.vverbose) or ((args.verbose and volume > 0.001)):
                    # Get note number and nearest note
                    if (pitch == 0.0):
                        name = "none"
                    else:
                        n = freq_to_number(pitch)
                        n0 = int(round(n))
                        name = note_name(n0)

                    # Format the volume output so it only
                    # displays at most six numbers behind 0.
                    volume = "{:6f}".format(volume)
                    # Finally print the pitch and the volume.
                    print(name + " " + str(pitch) + " " + str(volume))
            else:
                if level < 3:
                    result = fretFinder(aHandler, level)
                    resultList.append(result)
                else:
                    result = chordFinder(aHandler, level)
                    return
                continue
        except KeyboardInterrupt:
            # Print diags
            print("Session complete!")
            if len(resultList) != 0:
                print("Average time: " + str(sum(resultList) / len(resultList)) + " seconds")
            return

if __name__ == "__main__": main(sys.argv)