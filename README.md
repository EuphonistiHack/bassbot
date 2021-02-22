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

The above instructions are from https://aubio.org/manual/latest/installing.html,
which should be the point of reference for diagnosing any installation issue.

Once aubio is installed, use pip to install the following additional required
modules:
    aubio
    audioPy

The preferred method for installing these modules is pip.  To check if pip is
installed in your enviornment:
    $ python -m pip --version

Which should return something like:
    pip X.Y.Z from .../site-packages/pip (python X.Y)

If you do not have pip installed, use the following to install it:
https://pip.pypa.io/en/stable/installing/

Once pip is in place, the dependent packages for this program can be obtained
using:
    pip install aubio pyaudio

Once that is complete, bassbot.py can be run either as its own executable:
    ./bassBot.py

Or by invoking a specific python installation:
    python ./bassBot.py



