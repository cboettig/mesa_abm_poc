# First, grab a Unix image with Python / Conda installed
FROM condaforge/miniforge3

# Set up the DEV_CONTAINER environment variable (default to false, but allow it to be overridden with devcontainer.json)
ENV DEV_CONTAINER=false

# Copy over install scripts - this is a good way to keep the Dockerfile clean and readable
COPY .devcontainer/scripts .devcontainer/scripts

# Install git and ssh (note that you could also put this in a .sh for better readability)
RUN .devcontainer/scripts/install_git_and_ssh.sh

# Install Netlogo
RUN .devcontainer/scripts/install_netlogo.sh

# Then, copy the .devcontainer contents of the repo into the image - note we do this later so that we can avoid re-installing sys dependencies if the python deps change
COPY .devcontainer/python_environment.yml .devcontainer/python_environment.yml
RUN conda env create -f .devcontainer/python_environment.yml

# Now, copy python source code into the image - by doing this last, we can avoid re-installing ALL dependencies if just the source code changes
COPY simulation simulation

# Finally, run the startup script - which will either pause to allow the user to connect to the container, or run the workflow, depending on the value of DEV_CONTAINER
CMD .devcontainer/scripts/handle_startup.sh