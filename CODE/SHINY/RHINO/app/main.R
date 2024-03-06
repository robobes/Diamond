box::use(
  shiny[bootstrapPage, div, moduleServer, NS, renderUI, tags, uiOutput],
  readr[read_csv]
)


box::use(
  app/view/inf_regime_chart,
)

#' @export
ui <- function(id) {
  ns <- NS(id)
  bootstrapPage(
    inf_regime_chart$ui(ns("inf_regime_chart"))
  )
}

#' @export
server <- function(id) {
  moduleServer(id, function(input, output, session) {
    inf_regime_chart$server("inf_regime_chart")
  })
}
