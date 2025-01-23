FROM quay.io/jupyter/minimal-notebook


# Create a user-writable space outside $HOME for apps to live.
ENV XDG_DATA_HOME=/opt/share
ENV PIXI_HOME $XDG_DATA_HOME/pixi
ENV PATH $PIXI_HOME/bin:$PATH

USER root
RUN mkdir /opt/share && chown -R $NB_USER:users /opt/share

# Install code server
RUN curl -fsSL https://code-server.dev/install.sh | sh && rm -rf .cache 

USER $NB_USER

# codeserver extensions
RUN echo "ms-python.python ms-toolsai.jupyter continue.continue" | xargs -n 1 code-server --install-extension
RUN mamba install jupyter-vscode-proxy

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash

# Copy over pixi toml and pyproject.toml
COPY pixi.toml pixi.toml
COPY pixi.lock pixi.lock

# Install pixi dependencies
RUN pixi install
