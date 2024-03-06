box::use(
  shiny[bootstrapPage, div, moduleServer, NS, renderUI, tags, uiOutput],
)


box::use(
  app/view/chart,
)

#' @export
ui <- function(id) {
  ns <- NS(id)
  bootstrapPage(
    chart$ui(ns("chart"))
  )
}

#' @export
server <- function(id) {
  moduleServer(id, function(input, output, session) {
    chart$server("chart")
  })
}
