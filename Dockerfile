FROM manimcommunity/manim as system-dependencies
USER root
RUN apt-get update  \
 && apt-get install -y -q sox libsox-fmt-all portaudio19-dev

FROM system-dependencies
USER ${NB_USER}

WORKDIR /src/manim_voiceover
COPY . ./
RUN pip install .[gtts,gradio]
WORKDIR /manim