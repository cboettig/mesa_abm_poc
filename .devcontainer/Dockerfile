# First, grab a Unix image with Python / Conda installed
FROM condaforge/miniforge3

# Copy over install scripts - this is a good way to keep the Dockerfile clean and readable
COPY .devcontainer/scripts .devcontainer/scripts

# Install git and ssh (note that you could also put this in a .sh for better readability)
RUN .devcontainer/scripts/install_git_and_ssh.sh

# Then, copy the .devcontainer contents of the repo into the image - note we do this later so that we can avoid re-installing sys dependencies if the python deps change
COPY .devcontainer/python_environment.yml .devcontainer/python_environment.yml
RUN conda env create -f .devcontainer/python_environment.yml

# Now, copy python source code into the image - by doing this last, we can avoid re-installing ALL dependencies if just the source code changes
COPY simulation simulation

# Finally, keep the container running so that we can attach to it
CMD tail -f /dev/null