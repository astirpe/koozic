.. _quickstart:

Quickstart
==========

KooZic uses Python 3.5+, relies on PostgreSQL as a database system and FFmpeg for music transcoding.
It uses as a core system the Odoo software. It should work on any GNU/Linux distribution as well as
OSX. Unfortunately, windows is not supported.

.. _auto_script:

Automatic script
----------------

An installation script is provided to automatize installation, un-installation and upgrade. The
following OS are supported with the script:

* Ubuntu 18.04 & 16.04 (and derivatives, such as Linux Mint)
* Debian 9
* Fedora 29
* CentOS 7.6 (Python 3 must be installed)


Installation
^^^^^^^^^^^^

The script execute the steps detailed in the :ref:`detailed_instructions`. To install run:
::

   wget https://raw.githubusercontent.com/DocMarty84/koozic_install/v2/koozic_install.py -O koozic_install.py
   sudo python3 koozic_install.py install

Usage:
::

   koozic_install.py [-h] [-u USER] [-d DIRECTORY] {install,uninstall,upgrade}

**Positional arguments**

.. glossary::

   ``{install,uninstall,upgrade}``
      install, uninstall or upgrade mode

**Optional arguments**

.. glossary::

   ``-h, --help``
      show the help message and exit

   ``-u USER, --user USER``
      user running the koozic service. The user must already exist and have access to the media
      library. Default value: ``root``.

   ``-d DIRECTORY, --directory DIRECTORY``
      install directory. Default value: ``/opt``


At the end of the installation process, KooZic should be accessible in your browser at
http://localhost:8069. Log in with the email / password ``admin``, and change it right away!

To add your music in the library, go to Settings > Folders, and add the folder of your choice. For
more information, visit the :ref:`folders` documentation page.

Once KooZic is up and running, it is advised to set up an :ref:`https` endpoint.


Uninstallation
^^^^^^^^^^^^^^

The script can also uninstall KooZic:
::

   sudo python3 koozic_install.py uninstall

Please note that PostgreSQL, which is automatically installed, won't be uninstalled automatically
since other services might use it. You might also want to remove FFMpeg at
``/usr/local/bin/ffmpeg``.

Docker
------

A `Docker Compose <https://docs.docker.com/compose/>`_ image is available and provides an up and
running installation without hassle. It should work on any Docker-supported platform (including
Windows).


Installation
^^^^^^^^^^^^

1. Install Docker Compose following the `official instructions <https://docs.docker.com/compose/install/>`_.
2. Download the ``koozic-*-docker.tar.gz`` file on `Github <https://github.com/DocMarty84/koozic/releases/latest>`_.
3. Edit ``docker-compose.yml`` and replace ``/music`` by the music folder you want to share.
4. Build & run:


::

   docker-compose up -d

After ~10-20 seconds, KooZic should be accessible in your browser at http://localhost:8069. Log in
with the email / password ``admin``, and change it right away!

To add your music in the library, go to Settings > Folders, and add the folder ``/mnt/host``. For
more information, visit the :ref:`folders` documentation page.

The usual Docker instructions can be used to start and stop the container later on:
::

   docker-compose start
   docker-compose stop


Uninstallation
^^^^^^^^^^^^^^

The following will remove the container:
::

   docker-compose down


Upgrade
^^^^^^^

Make sure to stop the container:
::

   docker-compose stop

Then pull the latest version relaunch the container. The upgrade will be performed automatically:
::

   docker-compose pull
   docker-compose up -d
