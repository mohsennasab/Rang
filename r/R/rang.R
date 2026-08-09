# Rang, color palettes from Persian art.
# Palette data lives in palettes_data.R, written from palettes/*.json at the
# repo root. Edit the json and rerun tools/build.py rather than editing here.

#' Build a Rang palette
#'
#' Palettes are stored as a color ramp plus a pick order. Asking for a few
#' colors returns a well separated subset, asking for more than the palette
#' holds interpolates along the ramp.
#'
#' @param name Palette name, see names(rang_palettes)
#' @param n Number of colors. Defaults to the full palette.
#' @param type "discrete" or "continuous". Defaults to discrete while n fits
#'   the palette and continuous beyond that.
#' @param direction 1 for the stored order, -1 to reverse
#' @param override_order Take the first n ramp colors instead of the stored
#'   pick order. Default FALSE.
#' @return A vector of hex colors
#' @examples
#' rang("Kashan")
#' rang("Kashan", 4)
#' rang("Kashan", 100, type = "continuous")
#'
#' # with ggplot2, use the scales rather than building the colors by hand
#' # scale_fill_rang_d("Kashan")
#' # scale_fill_rang_c("Termeh")
#' @seealso \code{\link{scale_fill_rang_d}} and \code{\link{scale_fill_rang_c}}
#'   for the ggplot2 scales.
#' @export
rang <- function(name, n, type = c("discrete", "continuous"),
                 direction = 1, override_order = FALSE) {
  if (length(name) != 1 || !is.character(name) || is.na(name)) {
    stop("name must be one palette name")
  }
  pal <- rang_palettes[[name]]
  if (is.null(pal)) {
    stop("Palette not found. See names(rang_palettes).")
  }
  if (missing(n)) {
    n <- length(pal$colors)
  }
  if (length(n) != 1 || !is.numeric(n) || is.na(n) || !is.finite(n) ||
      n < 1 || n != floor(n)) {
    stop("n must be a positive integer")
  }
  n <- as.integer(n)
  if (length(direction) != 1 || is.na(direction) ||
      !direction %in% c(1, -1)) {
    stop("direction must be 1 or -1")
  }
  if (length(override_order) != 1 || !is.logical(override_order) ||
      is.na(override_order)) {
    stop("override_order must be TRUE or FALSE")
  }
  if (missing(type)) {
    type <- if (n > length(pal$colors)) "continuous" else "discrete"
  }
  type <- match.arg(type)
  if (type == "discrete" && n > length(pal$colors)) {
    stop("Not enough colors in the palette, use type = 'continuous'.")
  }

  out <- if (type == "continuous") {
    grDevices::colorRampPalette(pal$colors)(n)
  } else if (override_order) {
    pal$colors[seq_len(n)]
  } else {
    pal$colors[pal$order <= n]
  }
  if (direction == -1) {
    out <- rev(out)
  }
  structure(out, class = "palette", name = name)
}

#' Check a palette against the project CVD separation rule
#'
#' TRUE when the full palette passes Rang's pairwise separation rule under
#' simulated protanopia, deuteranopia and tritanopia. This project check is
#' not an accessibility guarantee. Details are on each palette page.
#'
#' @param name Palette name, see names(rang_palettes)
#' @return logical
#' @examples
#' colorblind_friendly("Kashan")
#' @export
colorblind_friendly <- function(name) {
  if (length(name) != 1 || !is.character(name) || is.na(name)) {
    stop("name must be one palette name")
  }
  pal <- rang_palettes[[name]]
  if (is.null(pal)) {
    stop("Palette not found. See names(rang_palettes).")
  }
  isTRUE(pal$colorblind)
}

#' @export
print.palette <- function(x, ...) {
  n <- length(x)
  old <- graphics::par(mar = c(0.5, 0.5, 0.5, 0.5))
  on.exit(graphics::par(old))
  graphics::image(1:n, 1, as.matrix(1:n), col = x,
                  ylab = "", xaxt = "n", yaxt = "n", bty = "n")
  graphics::rect(0, 0.92, n + 1, 1.08,
                 col = grDevices::rgb(1, 1, 1, 0.8), border = NA)
  graphics::text((n + 1) / 2, 1, labels = attr(x, "name"),
                 cex = 2.5, family = "serif")
}
