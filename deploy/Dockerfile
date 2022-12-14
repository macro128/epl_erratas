ARG env=prod
# dev/build stage
FROM mambaorg/micromamba:jammy AS dev

# install PDM
COPY ./deploy/env.yml .
RUN --mount=type=cache,target=/opt/conda/pkgs,id=mamba,mode=0775,uid=1000,gid=1000,sharing=locked \
    micromamba install -y -f env.yml -n base && \
    micromamba clean --all -y

ARG MAMBA_DOCKERFILE_ACTIVATE=1
ARG dependencies=":all"

# install dependencies
COPY pyproject.toml *.lock ./
RUN python -c "print(' -G'.join('"$dependencies"'.split(',')))" |  \
    xargs pdm install --no-lock --no-editable --no-self -G

# prod stage
FROM mambaorg/micromamba:jammy AS prod

# get environment
COPY --from=dev /opt/conda /opt/conda

# prepare deploy path
ENV SRC_PATH=/app/src/
WORKDIR $SRC_PATH

# copy src
ARG src=./
COPY --chown=$MAMBA_USER $src $src

# runtime stage
FROM ${env} AS runtime
# add src to python path
ENV SRC_PATH=/app/src/
ENV PYTHONPATH $SRC_PATH:$PYTHONPATH
WORKDIR $SRC_PATH

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "tini", "--"]
