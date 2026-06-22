# app.R - EU trade-dependency dashboard (Shiny).
# "Who does the EU really depend on?" Naive (by member state) vs corrected (by origin),
# computed live from raw/ Comext CSVs via the shared base-R core in dependency_core.R.
# Run:  shiny::runApp(".")   (or in RStudio, open and click Run App)
#
# Hard deps: shiny, ggplot2. DT is used if available, else a plain table.

library(shiny)
library(ggplot2)
source("dependency_core.R")

have_DT <- requireNamespace("DT", quietly = TRUE)
RAW_DIR <- "raw"

# Pretty euro labels for axes / KPIs.
eur <- function(x) {
  ifelse(x >= 1e9, sprintf("EUR %.2fB", x / 1e9),
         ifelse(x >= 1e6, sprintf("EUR %.1fM", x / 1e6), sprintf("EUR %.0f", x)))
}

# Horizontal share bar chart, China (CN) highlighted in firebrick.
share_bars <- function(df, key, title, fill_default) {
  df <- head(df, attr(df, "topn"))
  df[[key]] <- factor(df[[key]], levels = rev(df[[key]]))
  df$hl <- ifelse(as.character(df[[key]]) == "CN", "CN", "other")
  ggplot(df, aes(x = .data[[key]], y = value_share, fill = hl)) +
    geom_col(width = 0.75) +
    geom_text(aes(label = sprintf("%.1f%%", value_share)), hjust = -0.15, size = 3.4) +
    coord_flip() +
    scale_fill_manual(values = c(CN = "firebrick", other = fill_default), guide = "none") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.18))) +
    labs(title = title, x = NULL, y = "% share") +
    theme_minimal(base_size = 13) +
    theme(panel.grid.major.y = element_blank())
}

ui <- fluidPage(
  titlePanel("EU import dependency - naive vs corrected (Comext)"),
  sidebarLayout(
    sidebarPanel(
      width = 3,
      uiOutput("product_ui"),
      uiOutput("year_ui"),
      sliderInput("topn", "Show top N", min = 4, max = 15, value = 6, step = 1),
      hr(),
      strong("Download (all years, current product)"),
      br(), br(),
      downloadButton("dl_origin",  "origin_shares.csv"),  br(), br(),
      downloadButton("dl_ms",      "ms_shares.csv"),       br(), br(),
      downloadButton("dl_summary", "summary.csv"),
      hr(),
      helpText("Extra-EU imports. For extra-EU flows the Comext partner field IS the",
               "country of origin. Bloc aggregates (EU, EA, *_2020) are dropped or",
               "totals double-count. Source: Eurostat Comext, public data.")
    ),
    mainPanel(
      width = 9,
      uiOutput("kpis"),
      tabsetPanel(
        tabPanel("Naive vs corrected",
          br(),
          p(strong("The naive panel is the trap:"), "ranking by importing member state",
            "spreads dependence across DE/PL/NL and is distorted by the Rotterdam/Antwerp",
            "transit effect. The corrected panel, by country of origin, shows who the EU",
            "actually depends on."),
          fluidRow(
            column(6, plotOutput("plot_naive",     height = 340)),
            column(6, plotOutput("plot_corrected", height = 340))
          )
        ),
        tabPanel("Trend", br(), plotOutput("plot_trend", height = 420)),
        tabPanel("Value vs tonnage", br(),
          p("Is dependence even heavier by weight than by value? Top origins, current year."),
          plotOutput("plot_vq", height = 420)),
        tabPanel("Origin table", br(),
          if (have_DT) DT::DTOutput("tbl") else tableOutput("tbl"))
      )
    )
  )
)

server <- function(input, output, session) {

  products <- reactive(discover_products(RAW_DIR))

  output$product_ui <- renderUI({
    p <- products()
    if (is.null(p)) return(helpText(strong("No data in raw/ - run download_data.ps1 first.")))
    choices <- setNames(p$code, sprintf("%s (CN %s)", p$label, p$code))
    selectInput("product", "Product", choices = choices)
  })

  # Per-product tables, recomputed only when the product changes.
  tabs <- reactive({
    req(input$product); p <- products()
    req(!is.null(p), nrow(p) > 0)
    row <- p[p$code == input$product, ]
    req(nrow(row) >= 1); row <- row[1, ]
    val <- read_comext(file.path(RAW_DIR, row$value_file))
    qty <- read_comext(file.path(RAW_DIR, row$qty_file))
    validate(need(!is.null(val) && nrow(val) > 0, "Value file empty or missing."),
             need(!is.null(qty) && nrow(qty) > 0, "Quantity file empty or missing."))
    build_tables(val, qty)
  })

  output$year_ui <- renderUI({
    su <- tabs()$summary
    validate(need(is.data.frame(su) && nrow(su) > 0, "No years in data."))
    yrs <- sort(unique(su$year), decreasing = TRUE)
    selectInput("year", "Year", choices = yrs, selected = yrs[1])
  })

  origin_y <- reactive({ req(input$year)
    d <- tabs()$origin; d <- d[d$year == as.integer(input$year), ]
    attr(d, "topn") <- input$topn; d })
  ms_y <- reactive({ req(input$year)
    d <- tabs()$ms; d <- d[d$year == as.integer(input$year), ]
    attr(d, "topn") <- input$topn; d })
  sum_y <- reactive({ req(input$year)
    tabs()$summary[tabs()$summary$year == as.integer(input$year), ] })

  output$kpis <- renderUI({
    s <- sum_y(); req(nrow(s) == 1)
    box <- function(lab, val) column(3, div(
      style = "border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center;",
      div(style = "font-size:22px;font-weight:700;color:firebrick;", val),
      div(style = "font-size:12px;color:#555;", lab)))
    fluidRow(
      box("China share (value)",   sprintf("%.1f%%", s$china_val)),
      box("China share (tonnage)", ifelse(is.na(s$china_qty), "-", sprintf("%.1f%%", s$china_qty))),
      box("Concentration (HHI value)", sprintf("%.2f", s$hhi_val)),
      box("Total extra-EU imports", eur(s$total_eur))
    )
  })

  output$plot_naive     <- renderPlot(share_bars(ms_y(), "reporter",
                            paste("NAIVE: by member state", input$year), "grey70"))
  output$plot_corrected <- renderPlot(share_bars(origin_y(), "partner",
                            paste("CORRECTED: by origin", input$year), "grey75"))

  output$plot_trend <- renderPlot({
    s <- tabs()$summary
    req(is.data.frame(s), nrow(s) > 0)
    sl <- rbind(
      data.frame(year = s$year, share = s$china_val, metric = "value"),
      data.frame(year = s$year, share = s$china_qty, metric = "tonnage"))
    ggplot(sl, aes(year, share, colour = metric)) +
      geom_line(linewidth = 1.1) + geom_point(size = 2.6) +
      scale_colour_manual(values = c(value = "firebrick", tonnage = "grey40")) +
      scale_x_continuous(breaks = s$year) +
      ylim(0, 100) +
      labs(title = "China share of extra-EU origin over time",
           x = NULL, y = "China share (%)", colour = NULL) +
      theme_minimal(base_size = 13)
  })

  output$plot_vq <- renderPlot({
    d <- head(origin_y(), input$topn)
    dl <- rbind(
      data.frame(origin = d$partner, share = d$value_share, metric = "value"),
      data.frame(origin = d$partner, share = d$qty_share,   metric = "tonnage"))
    dl$origin <- factor(dl$origin, levels = rev(d$partner))
    ggplot(dl, aes(origin, share, fill = metric)) +
      geom_col(position = "dodge", width = 0.7) + coord_flip() +
      scale_fill_manual(values = c(value = "firebrick", tonnage = "grey60")) +
      labs(title = paste("Value vs tonnage share by origin", input$year),
           x = NULL, y = "% share", fill = NULL) +
      theme_minimal(base_size = 13)
  })

  tbl_df <- reactive({
    d <- origin_y()
    data.frame(Origin = d$partner, `Value EUR` = d$value_eur, Tonnes = round(d$tonnes, 1),
               `Value %` = d$value_share, `Tonnage %` = d$qty_share, check.names = FALSE)
  })
  if (have_DT) {
    output$tbl <- DT::renderDT(
      DT::formatCurrency(
        DT::datatable(tbl_df(), rownames = FALSE, options = list(pageLength = 15)),
        "Value EUR", currency = "EUR ", digits = 0))
  } else {
    output$tbl <- renderTable(tbl_df())
  }

  dl <- function(which) downloadHandler(
    filename = function() sprintf("%s_%s.csv", which, input$product),
    content  = function(file) write.csv(tabs()[[which]], file, row.names = FALSE))
  output$dl_origin  <- dl("origin")
  output$dl_ms      <- dl("ms")
  output$dl_summary <- dl("summary")
}

shinyApp(ui, server)
