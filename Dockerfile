# libpfm dependency builder image
FROM ubuntu:focal as libpfm-builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \
    apt install -y curl build-essential git devscripts debhelper dpatch python3-dev libncurses-dev swig && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    git clone -b selfwatts https://github.com/gfieni/libpfm4.git /usr/src/libpfm4 && \
    cd /usr/src/libpfm4 && \
    rm -fr debian && \
    curl -s http://archive.ubuntu.com/ubuntu/pool/main/libp/libpfm4/libpfm4_4.10.1+git20-g7700f49-2.debian.tar.xz |tar xvJ && \
    patch -p1 < debian/patches/reproducible.patch && \
    fakeroot debian/rules binary

# sensor builder image (build tools + development dependencies):
FROM ubuntu:focal as sensor-builder
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=libpfm-builder /usr/src/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb /usr/src/libpfm4-dev_4.10.1+git20-g7700f49-2_amd64.deb /tmp/
RUN apt update && \
    apt install -y build-essential git clang-tidy cmake pkg-config libczmq-dev libsystemd-dev uuid-dev libmongoc-dev && \
    dpkg -i /tmp/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb && \
    dpkg -i /tmp/libpfm4-dev_4.10.1+git20-g7700f49-2_amd64.deb
RUN git clone https://github.com/powerapi-ng/hwpc-sensor.git /usr/src/hwpc-sensor && \
    cd /usr/src/hwpc-sensor && \
    mkdir build && \
    cd build && \
    GIT_TAG=$(git describe --tags --dirty 2>/dev/null || echo "unknown") \
    GIT_REV=$(git rev-parse HEAD 2>/dev/null || echo "unknown") \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_CLANG_TIDY="clang-tidy" -DWITH_MONGODB=ON .. && \
    make -j $(getconf _NPROCESSORS_ONLN)

# selfwatts builder image
FROM ubuntu:focal as selfwatts-builder
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=libpfm-builder /usr/src/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb /usr/src/libpfm4-dev_4.10.1+git20-g7700f49-2_amd64.deb /tmp/
RUN apt update && \
    apt install -y python3 python3-dev python3-virtualenv python3-setuptools python3-wheel build-essential && \
    dpkg -i /tmp/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb &&  \
    dpkg -i /tmp/libpfm4-dev_4.10.1+git20-g7700f49-2_amd64.deb && \
    rm -rf /var/lib/apt/lists/* /tmp/*.deb
COPY . /usr/src/selfwatts-controller
RUN cd /usr/src/selfwatts-controller && \
    python3 setup.py bdist_wheel

# selfwatts runner image
FROM ubuntu:focal as selfwatts-runner
ENV DEBIAN_FRONTEND=noninteractive
COPY --from=libpfm-builder /usr/src/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb /tmp/
COPY --from=sensor-builder /usr/src/hwpc-sensor/build/hwpc-sensor /usr/bin/hwpc-sensor
COPY --from=selfwatts-builder /usr/src/selfwatts-controller/dist/selfwatts_controller-1.0.0-cp38-cp38-linux_x86_64.whl /tmp/
RUN apt update && \
    apt install -y libczmq4 python3 python3-pip libmongoc-1.0-0 && \
    dpkg -i /tmp/libpfm4_4.10.1+git20-g7700f49-2_amd64.deb && \
    pip3 install /tmp/selfwatts_controller-1.0.0-cp38-cp38-linux_x86_64.whl && \
    rm -rf /var/lib/apt/lists/* /tmp/*.deb /tmp/*.whl
ENTRYPOINT ["python3", "-m", "selfwatts.controller"]
CMD ["--help"]
