FROM pypy:3.8-slim

WORKDIR /V2ray-fmp

COPY requirements.txt requirements.txt
COPY . .

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y supervisor \
    && rm -rf /var/lib/apt/lists/*



COPY config/supervisord.conf /etc/supervisor/conf.d/V2ray-fpm.conf
RUN mkdir -p /var/log/supervisor \
    && chmod +x scripts.sh

RUN pip3 install -r requirements.txt

ENTRYPOINT ["./scripts.sh"]
