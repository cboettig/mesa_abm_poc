# First, grab a Unix image
FROM ubuntu:22.04

# Copy over install scripts - this is a good way to keep the Dockerfile clean and readable
COPY .devcontainer/scripts .devcontainer/scripts

# Install git, ssh, and pixi (note that you could also put this in a .sh for better readability)
RUN .devcontainer/scripts/install_git_and_ssh.sh
RUN .devcontainer/scripts/install_pixi.sh

# # Install conda-lock in base
# RUN conda install -c conda-forge conda-lock

# Use the pre-built conda-lock environment to install the dependencies
COPY .devcontainer/python_environment_lock.yml .devcontainer/python_environment_lock.yml
# RUN conda-lock install -n mesa .devcontainer/python_environment_lock.yml

# Now, copy python source code into the image - by doing this last, we can avoid re-installing ALL dependencies if just the source code changes
COPY vegetation vegetation

# Finally, keep the container running so that we can attach to it
CMD tail -f /dev/null