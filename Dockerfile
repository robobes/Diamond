FROM rocker/shiny

COPY CLOUD/shiny-customized.config /etc/shiny-server/shiny-server.conf

COPY CODE/app.R /srv/shiny-server/app.R

COPY DATA/Data_for_shiny.RData /srv/shiny-server/Data_for_shiny.RData

EXPOSE 8080

USER shiny

# avoid s6 initialization
# see https://github.com/rocker-org/shiny/issues/79
CMD ["/usr/bin/shiny-server"]
