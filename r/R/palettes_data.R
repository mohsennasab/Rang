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
  ),
  Golestan = list(
    colors = c("#432f2c", "#ae6259", "#b57f86", "#b5b5ac", "#cbb11c", "#9a9a68", "#45939c", "#577ab1", "#333a80"),
    order = c(4, 5, 8, 6, 1, 7, 3, 9, 2),
    colorblind = TRUE,
    source = "Tile panel with a hunting scene, Qajar period, Golestan Palace, UNESCO World Heritage Site, https://whc.unesco.org/en/list/1422/"
  ),
  Termeh = list(
    colors = c("#e5f0ee", "#c8dfe3", "#a9ccd7", "#7fb5c1", "#5d95a8", "#3e738e", "#274e68"),
    order = c(1, 7, 5, 6, 3, 4, 2),
    colorblind = FALSE,
    source = "Termeh cloth with paisley boteh, contemporary, Termeh weaving tradition of Yazd, https://en.wikipedia.org/wiki/Termeh"
  )
)
