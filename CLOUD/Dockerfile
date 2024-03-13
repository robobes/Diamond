FROM rocker/shiny


RUN apt-get update && apt-get install -y \
cron \
gdebi-core \
libcurl4-openssl-dev \
libfreetype6-dev \
libpq-dev \
libssl-dev \
libxml2-dev \
openjdk-8-jdk \
r-base \
wget




RUN R -e "install.packages('shiny', repos='http://cran.rstudio.com/')"
RUN R -e "install.packages('ggplot2', repos='http://cran.rstudio.com/')"
RUN R -e "install.packages('plotly', repos='http://cran.rstudio.com/')"

COPY CLOUD/shiny-customized.config /etc/shiny-server/shiny-server.conf

COPY CODE/SHINY/app.R /srv/shiny-server/app.R

COPY DATA/SHINY/Data_for_shiny.RData /srv/shiny-server/Data_for_shiny.RData

EXPOSE 8080

USER shiny

# avoid s6 initialization
# see https://github.com/rocker-org/shiny/issues/79
CMD ["/usr/bin/shiny-server"]
