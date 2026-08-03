# Palette data written by tools/build.py. Edit palettes/*.json instead.

#' Complete list of Rang palettes
#'
#' Use names(rang_palettes) for the available names and rang() to build
#' a palette. Each entry holds the colors, the discrete pick order and a
#' project CVD separation flag.
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
    source = "Hunting-scene tile panel at Golestan Palace, photographed 2018, Golestan Palace, UNESCO World Heritage Site, https://whc.unesco.org/en/list/1422/"
  ),
  Termeh = list(
    colors = c("#e5f0ee", "#c8dfe3", "#a9ccd7", "#7fb5c1", "#5d95a8", "#3e738e", "#274e68"),
    order = c(1, 7, 5, 6, 3, 4, 2),
    colorblind = FALSE,
    source = "Termeh cloth with boteh motifs, photographed 2026, Yazd textile tradition, https://asia-archive.si.edu/object/S2017.14/"
  ),
  Khatam = list(
    colors = c("#1c110b", "#542020", "#8d310e", "#bf480d", "#b27a3c", "#c58c51", "#d9a545", "#dbba94", "#e5c870"),
    order = c(1, 6, 5, 3, 8, 4, 7, 9, 2),
    colorblind = FALSE,
    source = "Khatam panel with brass stars, 2026, Khatam marquetry tradition, https://www.iranicaonline.org/articles/isfahan-xiii-crafts/"
  ),
  Nasir = list(
    colors = c("#261410", "#3b1261", "#4027e1", "#518ffd", "#74ecf9", "#50a877", "#6dd96f", "#ebc05c", "#f04a23"),
    order = c(1, 7, 3, 5, 2, 8, 9, 4, 6),
    colorblind = FALSE,
    source = "Stained-glass window at Nasir al-Mulk Mosque, 2018, Nasir al-Mulk Mosque, https://commons.wikimedia.org/wiki/File:DSC_0277-%D9%85%D8%B3%D8%AC%D8%AF_%D9%86%D8%B5%DB%8C%D8%B1%D8%A7%D9%84%D9%85%D9%84%DA%A9.jpg"
  )
)
