This is a training tool intended to promote muscle memory for finding notes on
the frets of a bass.

********************************************************************************
INSTALLATION
********************************************************************************
bassBot is currently designed to be run in a Linux environment.  If you have
interest in running bassBot in a Windows, OSX, or other environment, please
reach out to me at wills.jordan@gmail.com and I'll be happy to work with you to
update this guide for another platform.

I have run bassBot an Ubuntu 16.0.4 and 18.0.4.  If you're using anything else
and hit any issues, please reach out and I'll do what I can to help.

First step to installation will be to install the following packages, all of
which are necessary for the aubio module:

    # conda [osx, linux, win]
    conda install -c conda-forge aubio
    # .deb (debian, ubuntu) [linux]
    sudo apt-get install python3-aubio python-aubio aubio-tools
    # brew [osx]
    brew install aubio --with-python

Next, pyAudio will needo to be installed:
    # .deb (debian, ubuntu) [linux]
    sudo apt-get install python-pyaudio

The above commands should result in all dependent modules being installed.  In
case something is missing, you can try using pip to install them instead:
    pip install aubio pyAudio

However, odds are that you are going to run into problems using pip, as aubio
and pyAudio all require some external packages (on Ubuntu at least), so google
will unfortunately be your best bet to installing these dependencies.

********************************************************************************
Operation
********************************************************************************
Once install is complete, bassBot can be run either as its own executable:
    ./bassBot.py

Or by invoking a specific python installation:
    python ./bassBot.py

Without modifications, bassbot will use the default system input as the audio
source.  By default, it will run with level 0 and no verbosity.  This can be
changed by using the -l flag to increase level:
    ./bassBot.py -l 1
    ./bassBot.py -l 2

Or the -v and --vv flags:
    ./bassBot.py -l 1 -v
    ./bassBot.py -l 0 --vv

-v and --vv don't do anything at present, but I'll be pushing a change shortly
to have them run a debug loop, will just print out the note and volume detected
by the audio processing loop (with no levels enabled).

