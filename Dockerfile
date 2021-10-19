FROM python:3.6
MAINTAINER binux <roy@binux.me>

# install phantomjs
RUN mkdir -p /opt/phantomjs \
        && cd /opt/phantomjs \
        && wget -O phantomjs.tar.bz2 https://mirrors.huaweicloud.com/phantomjs/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
        && tar xavf phantomjs.tar.bz2 --strip-components 1 \
        && ln -s /opt/phantomjs/bin/phantomjs /usr/local/bin/phantomjs \
        && rm phantomjs.tar.bz2


RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple/
RUN pip config set install.trusted-host mirrors.aliyun.com
# install requirements
RUN pip install 'https://dev.mysql.com/get/Downloads/Connector-Python/mysql-connector-python-2.1.5.zip#md5=ce4a24cb1746c1c8f6189a97087f21c1' -i https://pypi.douban.com/simple
RUN pip install pycurl -i https://pypi.douban.com/simple
COPY requirements.txt /opt/pyspider/requirements.txt
RUN pip install -r /opt/pyspider/requirements.txt

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider
RUN pip install -e .[all]
RUN rm -rf /opt/pyspider
# VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 25555
