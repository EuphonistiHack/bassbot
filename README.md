bassBot is a training tool intended to promote muscle memory for finding notes
on the frets of a bass.

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
    sudo apt-get install python3-aubio python-aubio aubio-tools python-tk python3-tk
    # brew [osx]
    brew install aubio --with-python

Next, pyAudio will needo to be installed:

    # .deb (debian, ubuntu) [linux]
    sudo apt-get install python-pyaudio

If you are running on Windows, then you'll need to follow the instructions at
the following link to install pyaudio.  I'm still working on cross platform
support, so this one might be janky for a while :(

    https://thetechinfinite.com/2020/07/14/how-to-install-pyaudio-module-in-python-3-0-in-windows/

The last package to install will be pygame:

    pip install pygame

The above commands should result in all dependent modules being installed.  In
case something is missing, you can try using pip to install them instead:

    pip install aubio pyAudio

However, odds are that you are going to run into problems using pip, as aubio
and pyAudio all require some external packages (on Ubuntu at least), so google
will unfortunately be your best bet to installing these dependencies.

********************************************************************************
OPERATION
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

-v doesn't do much at the moment.
--vv will override any level selection and instead run a diagnostic program.
This will go through the audio processing loop and print out the note recognized
and the volume detected for the note.  It is recommended that this be run before
using bassBot, as you will need to have a good enough single to get five
consecutive readings of a given note in order for the audio processing loop to
register a valid reading.

