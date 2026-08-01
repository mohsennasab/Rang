# Palette data. Built with tools/build.py, edit palettes/*.json instead.

#' Complete list of Rang palettes
#'
#' Use names(rang_palettes) for the available names and rang() to build
#' a palette. Each entry holds the colors, the discrete pick order and a
#' colorblind friendliness flag.
#'
#' @export
rang_palettes <- list(
  Kashan = list(
    colors = c("#7f3020", "#ab4a47", "#c07049", "#c59b46", "#ccac7e", "#e2cfb1", "#8a9463", "#345f72", "#1a3b45"),
    order = c(3, 6, 4, 8, 7, 1, 9, 5, 2),
    colorblind = FALSE,
    source = "Silk Kashan Carpet, 16th century, The Metropolitan Museum of Art, New York, https://www.metmuseum.org/art/collection/search/451470"
  )
)
