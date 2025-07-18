## FEATURE:
A Python-based build system that uses FAI (Fully Automatic Installation) as its core engine to generate a custom, bootable Ubuntu 24.04 Desktop ISO.

The entire build process is orchestrated by a Python script (build.py) and runs inside a self-contained Docker environment, making it portable and reproducible.

All settings are controlled via a single config.json file, which is validated using Pydantic.

Core functionalities include:

LUKS Full-Disk Encryption: Automatically sets up LVM on a LUKS-encrypted partition, with logic to target SSDs.

Custom Software: Installs a user-defined list of APT packages.

Dynamic Dependencies: Automatically downloads specified .deb packages and scripts from URLs during the build process.

First-Boot Scripts: Executes custom scripts (both automated and manual/interactive) the first time the newly installed Ubuntu system boots up.

Hardware-Specific Classes: Utilizes FAI's class system to apply specific configurations for different hardware vendors (Dell, Lenovo, HP).

## EXAMPLES:
This project combines several technologies. Use the following resources for best practices and inspiration, but do not copy them directly as our implementation integrates them in a unique way.

FAI Concepts: Read the official FAI Guide to understand the core concepts of FAI, especially how classes, hooks, and the configuration space work. This is our primary reference for the installation backend.

Ubuntu Autoinstall: Refer to the official Ubuntu Autoinstall documentation for the syntax and structure of the user-data.yaml file. This is crucial for configuring the target OS, especially for the complex LUKS setup.

Python Orchestration: The build.py script serves as the central orchestrator. Its structure should be inspired by clean, modular Python principles, using functions to separate concerns like parsing configuration, downloading assets, generating templates, and executing FAI commands.

## DOCUMENTATION:
FAI Project Guide: https://fai-project.org/fai-guide/

Ubuntu Autoinstall Reference: https://ubuntu.com/server/docs/install/autoinstall-reference

Pydantic: https://www.google.com/search?q=https://docs.pydantic.dev/

Jinja2 (for templating): https://jinja.palletsprojects.com/

## OTHER CONSIDERATIONS:
Include a README.md with detailed setup instructions, including how to install Docker on macOS and run the build using the run.sh script.

The README.md must also document the project structure and provide a detailed explanation of all available options in config.json.

Create a config.json.example file to serve as a template for users.

The build environment is fully managed by Docker. No local Python virtual environment is required on the host machine.

Use Pydantic for robust validation of the config.json file to prevent build errors from malformed configurations.