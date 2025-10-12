#- -------------------------------------------------------------------------------------------------
#- Runner
#-
FROM ghcr.io/naa0yama/join_logo_scp_trial:v25.10.00-beta3-ubuntu2404@sha256:b882da95367a3f498e8cb31f245b9212fa82b46654b7e564d01e0e73ee3f1cc1
ARG DEBIAN_FRONTEND=noninteractive \
	USER_NAME=cuser \
	USER_UID=60001 \
	USER_GID=60001

## renovate: datasource=github-releases packageName=asdf-vm/asdf versioning=semver automerge=true
ARG ASDF_VERSION="v0.16.4"
## renovate: datasource=github-releases packageName=dprint/dprint versioning=semver automerge=true
ARG DPRINT_VERSION=0.50.2

# retry dns and some http codes that might be transient errors
ARG CURL_OPTS="-sfSL --retry 3 --retry-delay 2 --retry-connrefused"


SHELL ["/bin/bash", "-c"]
RUN mkdir -p /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	\
	echo "**** Dependencies ****" && \
	rm -f /etc/apt/apt.conf.d/docker-clean && \
	echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache && \
	echo "**** Dependencies ****" && \
	set -euxo pipefail && \
	apt-get -y update && \
	apt-get -y upgrade && \
	apt-get -y install --no-install-recommends \
	bash \
	binutils \
	btop \
	ca-certificates \
	curl \
	git \
	gpg-agent \
	jq \
	nano \
	openssh-client \
	software-properties-common \
	sudo \
	tzdata \
	unzip \
	vainfo \
	wget

RUN echo "**** Create user ****" && \
	set -euxo pipefail && \
	userdel -r ubuntu && \
	groupadd --gid "${USER_GID}" "${USER_NAME}" && \
	useradd -s /bin/bash --uid "${USER_UID}" --gid "${USER_GID}" -m "${USER_NAME}" && \
	echo "${USER_NAME}:password" | chpasswd && \
	passwd -d "${USER_NAME}"

RUN echo "**** Add sudo user ****" && \
	set -euxo pipefail && \
	echo -e "${USER_NAME}\tALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USER_NAME}"

COPY --chown=${USER_NAME} --chmod=644 .tool-versions /home/${USER_NAME}/.tool-versions

RUN echo "**** Install asdf ****" && \
	set -euxo pipefail && \
	cd /tmp && \
	if [ -z "${ASDF_VERSION}" ]; then echo "ASDF_VERSION is blank"; else echo "ASDF_VERSION is set to '$ASDF_VERSION'"; fi && \
	curl -fSL -o /tmp/asdf.tar.gz "$(curl -sfSL https://api.github.com/repos/asdf-vm/asdf/releases/tags/${ASDF_VERSION} | \
	jq -r '.assets[] | select(.name | endswith("linux-amd64.tar.gz")) | .browser_download_url')" && \
	tar -xf /tmp/asdf.tar.gz && \
	mv -v /tmp/asdf /usr/local/bin/asdf && \
	type -p asdf && \
	asdf version

RUN echo "**** Install dprint ****" && \
	set -euxo pipefail && \
	_download_url="$(curl ${CURL_OPTS} -H 'User-Agent: builder/1.0' \
	https://api.github.com/repos/dprint/dprint/releases/tags/${DPRINT_VERSION} | \
	jq -r '.assets[] | select(.name | endswith("x86_64-unknown-linux-gnu.zip")) | .browser_download_url')" && \
	_filename="$(basename "$_download_url")" && \
	curl ${CURL_OPTS} -H 'User-Agent: builder/1.0' -o "./${_filename}" "${_download_url}" && \
	unzip "${_filename}" -d /usr/local/bin/ && \
	type -p dprint && \
	rm -rf "./${_filename}"

USER ${USER_NAME}
RUN <<EOF
cat <<- _DOC_ >> ~/.bashrc

#asdf command
export PATH="\${ASDF_DATA_DIR:-$HOME/.asdf}/shims:\$PATH"
. <(asdf completion bash)

_DOC_
EOF

USER root
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
	--mount=type=cache,target=/var/lib/apt,sharing=locked \
	\
	echo "**** Dependencies Python ****" && \
	set -euxo pipefail && \
	apt-get install -y --no-install-recommends \
	build-essential \
	libbz2-dev \
	libffi-dev \
	liblzma-dev \
	libncursesw5-dev \
	libreadline-dev \
	libsqlite3-dev \
	libssl-dev \
	libxml2-dev \
	libxmlsec1-dev \
	patchelf \
	tk-dev \
	xz-utils \
	zlib1g-dev

USER ${USER_NAME}
ARG PATH="/home/${USER_NAME}/.asdf/shims:${PATH}"
RUN echo "**** asdf install python ****" && \
	set -euxo pipefail && \
	asdf plugin add python

RUN echo "**** asdf install plugin poetry ****" && \
	set -euxo pipefail && \
	asdf plugin add poetry

RUN echo "**** asdf install plugin install ****" && \
	set -euxo pipefail && \
	asdf install python && \
	asdf install

ENTRYPOINT [ "/bin/bash", "-c" ]
CMD [ "" ]
