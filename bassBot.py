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
import pygame

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
SHAPE_NAMES = ['major 7', 'dom 7', 'minor 7', 'm7 flat 5']

# The chord shape will give an offset from the root chord in [string][fret]
# format.  For example, a C major 7 will contain the root note (C), then a note
# one string up and one fret down (E) [1][-1], then a note one string up and
# two strings down from the root (G): [1][2], then a note two strings up and
# one string down (B): [2][1], and ending on a note two strings up and two
# strings down (C): [2][2]

MAJOR7_SHAPE = [[1,-1], [1,2], [2,1], [2,2]]
DOM7_SHAPE = [[1,-1], [1,2], [2,0], [2,2]]
MINOR7_SHAPE = [[1,-2], [1,2], [2,0], [2,2]]
MINOR7FLAT5_SHAPE = [[1,-2], [1,1], [2,0], [2,2]]
SHAPE_LIST = [MAJOR7_SHAPE, DOM7_SHAPE, MINOR7_SHAPE, MINOR7FLAT5_SHAPE]

WRONG_SOUND = 'custWrong.ogg'
RIGHT_SOUND = 'custRight.ogg'

ROBOT = """
~~~~~~~~~~BASSBOT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
++-----------------------------|---------------------(x)-------+--------------++
||  ,-.         \\.===./        |                     |         |     ( )      ||
||--o  |:---|---| n n |--------|------------#(x)-----|---------|--------------||
||    /     |)   \\_`_/         |    (x)      |       |         |              ||
||---/---------.=(+++)=.-----(x)----|--------|-----------------|--------------||
||  /    |  o="  (___)  "=o         |        |                 |              ||
||-------|)------|_|_|--------------|--------------------------|--------------||
||               /_|_\\                                         |              ||
++-------------------------------------------------------------+--------------++
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

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

gVolume = 1.0

class sessionInfo:
    """Track performance statics through playing"""
    numRight = 0
    numWrong = 0
    timeList = ''
    level = 0

    def __init__(self, level):
        self.numRight = 0
        self.numWrong = 0
        self.timeList = ''
        self.level = level

class AudioHandler:
    """Set up mic input, take samples when tick is called, provide freq and vol"""
    confidenceLevel = 2
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
        if len(resultList) >= aHandler.confidenceLevel:
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
    # invoke processAudio on repeat.
    # Track the results in an array.  If you match 5 in a row, that's the result
    # disregard if volume is 0
    while True:
        result = aHandler.processAudio()
        pitch = result[0]
        volume = result[1]

        pitchList.insert(0, pitch)
        #print(str(pitch) + " list so far: " + str(pitchList))
        if len(pitchList) >= aHandler.confidenceLevel:
            # Count the number of 'noteName' in list.  if same as length, then
            # we have all readings the same note at the required confidence
            # level, so return the note.  Otherwise, pop the last entry and cont
            #print str(pitch)
            if (pitchList.count(0.0) == len(pitchList)):
                return
            pitchList.pop()

#TODO: move the string, fret, order parameters out of the chordFinder function.
#      It feels ugly having level if's in the main call and in each finder
#      function- the level parameters should be passed into these fxns instead
def chordFinder(aHandler, session):
    result = False
    chordTones = []
    for i in range(5):
        chordTones.append('')

    level = session.level
    print("level " + str(level))

    #Root selection
    if level == 4:
        string = 0
        fret = 8
        order = [0, 1, 2, 3, 4, 3, 2, 1, 0]
    elif level == 5:
        # Must be string 0:1
        # Must be fret 2:12, though 12th fret limit is a bit artificial
        string = random.randrange(2)
        fret = 2 + random.randrange(11)
        order = [0, 1, 2, 3, 4, 3, 2, 1, 0]
    elif level == 6:
        string = 0
        fret = 8
        order = [0, 1, 2, 3, 4]
        random.shuffle(order)
        orderString = ''
        for i in order:
            orderString += str(i+1) + " "
    elif level == 7:
        string = 0
        fret = 8
        order = [0, 1, 2, 3, 4]
        random.shuffle(order)
        orderString = ''
        for i in order:
            orderString += str(i+1) + " "
    elif level == 8:
        string = random.randrange(2)
        fret = 2 + random.randrange(11)
        order = [0, 1, 2, 3, 4]
        random.shuffle(order)
        orderString = ''
        for i in order:
            orderString += str(i+1) + " "

    # hi/lo/mid convention:
    # low is anything from C1 to B1.  Mid is anything from C2 to B2.  High is
    # anything from C3 to B3.  C4 and C#4 are the devil and don't exist.
    # I'm not super happy with this, but... I can't think of a better way to do
    # it, especially when we expand to support 5 string basses later
    # While we're at it, lets strip the number off the chord name as well.
    chordRoot = STRING_FRET_LIST[string][fret]
    if chordRoot[-1] == '1':
        prefix = 'low '
        chordRoot = chordRoot[:-1]
    elif chordRoot[-1] == '2':
        prefix = 'mid '
        chordRoot = chordRoot[:-1]
    else:
        prefix = 'high '
        chordRoot = chordRoot[:-1]

    # shape selection
    if level == 6:
        shape_num = 0
    else:
        shape_num = random.randrange(4)
    shape = SHAPE_LIST[shape_num]

    chordTones[0] = STRING_FRET_LIST[string][fret]
    for i in range(1,5):
        chordTones[i] = STRING_FRET_LIST[string+shape[i-1][0]][fret+shape[i-1][1]]

    print(SHAPE_NAMES[shape_num] + " " + prefix + chordRoot)
    if (level == 6):
        print("order: " + orderString)
    #print("root: " + prefix + chordRoot)
    print('string ' + str(string+1) + ' fret ' + str(fret))
    #print('shape num ' + str(shape_num))
    #print('shape ' + SHAPE_NAMES[shape_num])
    #print("tones: " + str(chordTones))
    ignore = ''

    #for i in range(5):
    for i in order:
        #If the user gets it wrong, ask for that same note until they get it right
        while result == False:
            toPlay = chordTones[i]
            #print("next note: " + toPlay)

            played = waitForNote(aHandler, ignore)
            #print('played ' + played)
            if played == toPlay:
                result = True
                print("correct on " + str(i+1))
            else:
                print("wrongzo!")
                print("   " + str(i+1) + "heard " + played + " expected " + str(toPlay))
                sound = pygame.mixer.Sound(WRONG_SOUND)
                sound.set_volume(gVolume)
                sound.play()
                session.numWrong += 1
                #playsound(WRONG_SOUND)
                ignore = played
        # move on to the next note, but be sure to ignore the current note or
        # the user will auto-fail
        ignore = toPlay
        result = False

    sound = pygame.mixer.Sound(RIGHT_SOUND)
    sound.set_volume(gVolume)
    sound.play()
    session.numRight += 1
    print("DONE!")
    waitForMute(aHandler)

    return chordRoot

# This function will handle all "Find the fret of the note" style levels.
# Currently:
#   Level 0: Play an open string E, A, D, or G.  Useful for novices who don't
#            have which string is which memorized yet.
#   Level 1: Play a given note on a given string, limited to the 4th fret.
#   Level 2: Play a given note on a given string, limited to the 12th fret
#   Level 3: Play a given note on a given string, limited to the 18th fret
# This function will return the amount of time it took the user to find the note
def fretFinder(aHandler, session, lastNote):
    result = False

    toPlay = lastNote
    level = session.level

    while toPlay == lastNote:
        # Select a random string, 1-4
        string = random.randrange(4)

        # Select the fret for that string
        if (level == 0):
            fret = 0
            prefix = ''
        elif (level == 1):
            fret = random.randrange(5)
            prefix = ''
        elif (level == 2):
            fret = random.randrange(13)
            # Any mode with fret 12 or higher in play needs a high/low prefix to
            # differentiate between open string and the 12th+ fret
            if fret >= 12:
                prefix = 'high '
            else:
                prefix = 'low '
        elif (level == 3):
            fret = random.randrange(NUM_FRETS)
            if fret >= 12:
                prefix = 'high '
            else:
                prefix = 'low '
        else:
            print("dev made an oops- unknown level: " + str(level))
            return 0

        toPlay = STRING_FRET_LIST[string][fret]

    #If the user gets it wrong, ask for that same note until they get it right
    while result == False:
        print(STRING_LIST[string] + " string: " + prefix + toPlay)
        # Uncomment the below if you're a dirty dirty cheat
        # print('string ' + str(string+1) + ' fret ' + str(fret))
        played = waitForNote(aHandler, lastNote)
        #print('played ' + played)
        if played == toPlay:
            result = True
            session.numRight += 1
            print("correct!  played " + str(played))
        else:
            print("wrongzo!")
            print("   expected " + str(toPlay) + ', string ' + str(string+1) + ' fret ' + str(fret))
            print("   heard " + str(played))
            lastNote = played
            session.numWrong += 1
        #waitForMute(aHandler)

    return toPlay

def printHelpMessage():
    print("Welcome to bassbot!  Use the -l flag to select from one of the following levels:")
    print("Level 0: Super-beginner mode! Play the string listed.")
    print("Level 1: Play the note listed!")
    print("  The answer will always be on one of the first 4 frets")
    print("Level 2: Play the note listed!")
    print("  The answer will be below the 12th fret")
    print("Level 3: Play the note listed, meedly meedly mode!")
    print("  The answer will go up to " + str(NUM_FRETS) + " frets")
    print("Level 4: Play a random chord shape for a middle C")
    print("Level 5: Play a random chord shape for a random root")
    print("Level 6: Play a major 7 arpeggio for a middle C in a random order")
    print("Level 7: Play a random chord shape for a middle C in a random order")
    print("Level 8: Play a random chord shape for a random root in a random order")
    print("\nCurrent supported chord shapes for levels 4 - 8 are:")
    for i in SHAPE_NAMES:
        print("   " + i)

# Main
# does main stuff
def main(args):

    # initialize the input audio interface
    aHandler = AudioHandler()
    resultList = []
    lastNote = ''
    global gVolume

    pygame.init()
    pygame.mixer.init()

    # handle argument parsing, because we don't need no stinkin gui
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", help="increase output verbosity",
                    action="store_true")
    parser.add_argument("--vverbose", "-vv", help="increase output verbosity",
                    action="store_true")
    parser.add_argument('-l', dest='level', default=-1, action='store', type=int)
    parser.add_argument('-s', dest='volume', default=100, action='store', type=int)
    args = parser.parse_args()
    level = args.level
    verbose = args.verbose

    gVolume  = args.volume/100.0
    print("audio volume: " + str(gVolume))

    print ROBOT

    #TODO: these ifs should track a testFunction (=fretFinder or =chordFinder)
    #      and store a paramlist based on the level.  The while loop below
    #      should then instead just invoke testFunction(testParams), as opposed
    #      to having yet another block of if statements based on the level
    #      passed in

    if (level == -1) and args.vverbose == False:
        printHelpMessage()
        return
    elif level == 0:
        print("Level 0: Play the string listed!")
    elif level == 1:
        print("Level 1: Play the note listed!")
        print("  The answer will always be on one of the first 4 frets")
    elif level == 2:
        print("Level 2: Play the note listed!")
        print("  ... but we're sticking below 12 frets")
    elif level == 3:
        print("Level 3: Play the note listed!")
        print("  ... but we're sticking below " + str(NUM_FRETS) + " frets")
    elif level == 4:
        print("Level 4: Play a random chord shape arpeggio for a middle C")
    elif level == 5:
        print("Level 5: Play a random chord shape for a random root")
    elif level == 6:
        print("Level 6: Play a major 7 arpeggio for a middle C in a random order")
    elif level == 7:
        print("Level 7: Play a random chord shape for a middle C in a random order")
    elif level == 8:
        print("Level 8: Play a random chord shape for a random root in a random order")
    else:
        print("well aren't we cheeky... you get level 0.")
        level = 0

    session = sessionInfo(level)
    while True:
        # Run until the user control+c's
        # TODO: add statistics!
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
                # Start the timer to count how long the user takes
                start_time = datetime.datetime.now()
                if level < 4:
                    lastNote = fretFinder(aHandler, session, lastNote)
                else:
                    lastNote = chordFinder(aHandler, session)

                # Calculate how long that took and append to stat list
                delta = datetime.datetime.now() - start_time
                elapsed_time = delta.total_seconds()
                resultList.append(elapsed_time)
        except KeyboardInterrupt:
            # Print diags
            print("Session complete!")
            if len(resultList) != 0:
                print("Average time: " + str(sum(resultList) / len(resultList)) + " seconds")
                print("Played " + str(session.numWrong) + " wrong notes on " + str(session.numRight) + " total")
            return

if __name__ == "__main__": main(sys.argv)