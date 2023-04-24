FROM manimcommunity/manim as system-dependencies
USER root
RUN apt-get update  \
 && apt-get install -y -q sox libsox-fmt-all portaudio19-dev

FROM system-dependencies
USER ${NB_USER}

WORKDIR /src/manim_voiceover
RUN pip install --no-cache-dir gtts>=2.2.4 gradio>=3.23.0
COPY . ./
RUN pip install .[gtts,gradio]
WORKDIR /manim