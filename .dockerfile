FROM registryhj/ubuntu:22.04

ENV \
  TZ="Asia/Seoul" \
  SHELL="/bin/zsh" \
  DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

COPY .python-version pyproject.toml uv.lock ./

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN \
  apt-get update && apt-get upgrade -y; \
  apt-get clean; \
  rm -rf /var/lib/apt/lists/*; \
  sh /uv-installer.sh; \ 
  rm /uv-installer.sh;

CMD ["/bin/zsh"]