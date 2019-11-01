Server module
=================================================

Server module of the messenger. Processes dictionaries - messages, stores public keys of clients.

Using

The module supports command line arguments:

1. -p - Port on which connections are accepted
2. -a - The address from which connections are received.

Examples of using:

``python server_main.py -p 8080``

*Starting the server on the port 8080*

``python server_main.py -a localhost``

*Starting the server accepting only connections with localhost*

server_main.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The launched module contains the parser of command line arguments and application initialization functionality.

server. **get_args** ()

    Parser of command line arguments, returns a tuple of 3 elements:

    * address from which to accept connections
    * port

server. **read_config_file** ()
    Function to load configuration parameters from an .ini file.

.. autoclass:: server.server_main.Server
	:members:

database_server.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.database_server.ServerDB
	:members:

Gui server module
=================================================

Сontains files for user interface.

gui_main_window.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.gui_server.gui_main_window.MainWindow
	:members:

gui_registration_user.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.gui_server.gui_registration_user.RegistrationDialog
	:members:


gui_settings_window.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.gui_server.gui_settings_window.SettingsWindow
	:members:
