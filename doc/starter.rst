Starter module
=================================================

Launch module for multiple clients simultaneously.

Using:

After starting, you will be prompted to enter a command.
Supported Commands:

1. st server - Start the server.

* Starts the server with default settings.

2. st clients - Start the clients.

* Starts the server with default settings.

* A request for the number of test clients to run will be displayed.
* Clients will be launched with names of the form **test1 - testX** and passwords **123**
* Test users must first register manually on the server with a password **123**
* If clients are launched for the first time, the startup time may be quite long due to the generation of new RSA keys.

3. close - Close all windows

* Closes all active windows that were launched from this module.

4. exit - Shut down module

* Terminates the module