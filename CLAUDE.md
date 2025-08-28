# Project EZ Pillow

The objective is to build a python package and the deployment toolsuit with docker to create dashboards in PNG with a modern design.

Les dashboards créés sont essentiellements des rapport de performance financières. Les KPIs et les rapports sous forme de tableaux doivent être parfaitement lisibles.

Les rapports sont destinés à être envoyés par email ou partagés sur les applications de collaboration (slack, whatsapp, discord, etc.)



## Components

You're using uv as the main tool for managing the python project.
All the code is in python.
The entrypoint of the project is the src/ezp/main.py file.
Drawed components are in the src/ezp/components directory.
Tous les imports en python sont en absolu.

## Claude Rules

Do not create documentation file for this project.
Code should be simple, self-explanatory and each function should have a clear purpose with a documentation string.
Respect the python pep8 code style and the naming conventions.
Secure that all executions run seamlessly with the Dockerfile to make sure that users can just run the container with their json file and get the image out.
Tu ne produis pas de script d'exemple pour faire des tests.


## Execution

Toutes les sorties doivent aller dans le dossier out/
