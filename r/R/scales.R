# ggplot2 scales for Rang palettes.
# ggplot2 is optional. It sits in Suggests, and each function checks for it
# before doing anything, so the package still loads without it.
#
# The first argument is called palette rather than name. Every ggplot2 scale
# already takes a name argument for the legend title, and R matches argument
# names before positions, so a palette argument called name would swallow the
# legend title and look up a palette that does not exist.

stop_without_ggplot2 <- function() {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("ggplot2 is needed for the Rang scales. Install it with ",
         'install.packages("ggplot2").', call. = FALSE)
  }
}

#' Discrete Rang scales for ggplot2
#'
#' Fills or colors a categorical variable with a Rang palette. The colors
#' follow the stored pick order, so a small number of categories stays as far
#' apart as the palette allows.
#'
#' @param palette Palette name, see names(rang_palettes)
#' @param direction 1 for the stored order, -1 to reverse
#' @param ... Passed on to ggplot2::discrete_scale(), so the usual scale
#'   arguments such as name, labels, breaks and guide all work
#' @return A ggplot2 scale
#' @examples
#' \donttest{
#' if (requireNamespace("ggplot2", quietly = TRUE)) {
#'   library(ggplot2)
#'   ggplot(iris, aes(Species, Petal.Length, fill = Species)) +
#'     geom_violin() +
#'     scale_fill_rang_d("Golestan")
#' }
#' }
#' @export
scale_fill_rang_d <- function(palette, direction = 1, ...) {
  stop_without_ggplot2()
  ggplot2::discrete_scale(
    "fill", palette = rang_pal(palette, direction), ...
  )
}

#' @rdname scale_fill_rang_d
#' @export
scale_color_rang_d <- function(palette, direction = 1, ...) {
  stop_without_ggplot2()
  ggplot2::discrete_scale(
    "colour", palette = rang_pal(palette, direction), ...
  )
}

#' @rdname scale_fill_rang_d
#' @export
scale_colour_rang_d <- scale_color_rang_d

#' Continuous Rang scales for ggplot2
#'
#' Fills or colors a numeric variable with a smooth Rang ramp. Palettes whose
#' lightness runs steadily in one direction, such as Termeh, Iwan, Khatam and
#' Rostan, suit ordered measurements like depth, elevation and rainfall.
#'
#' @param palette Palette name, see names(rang_palettes)
#' @param direction 1 for the stored order, -1 to reverse
#' @param steps Number of colors sampled along the ramp
#' @param ... Passed on to the matching ggplot2 gradient scale, so the usual
#'   scale arguments such as name, limits, labels and guide all work
#' @return A ggplot2 scale
#' @examples
#' \donttest{
#' if (requireNamespace("ggplot2", quietly = TRUE)) {
#'   library(ggplot2)
#'   ggplot(faithfuld, aes(waiting, eruptions, fill = density)) +
#'     geom_raster() +
#'     scale_fill_rang_c("Termeh")
#' }
#' }
#' @export
scale_fill_rang_c <- function(palette, direction = 1, steps = 256, ...) {
  stop_without_ggplot2()
  ggplot2::scale_fill_gradientn(
    colours = rang_ramp(palette, direction, steps), ...
  )
}

#' @rdname scale_fill_rang_c
#' @export
scale_color_rang_c <- function(palette, direction = 1, steps = 256, ...) {
  stop_without_ggplot2()
  ggplot2::scale_colour_gradientn(
    colours = rang_ramp(palette, direction, steps), ...
  )
}

#' @rdname scale_fill_rang_c
#' @export
scale_colour_rang_c <- scale_color_rang_c

#' Palette function for a Rang palette
#'
#' Returns a function of n suitable for ggplot2::discrete_scale() and other
#' places that expect a palette generator rather than a fixed vector.
#'
#' @param palette Palette name, see names(rang_palettes)
#' @param direction 1 for the stored order, -1 to reverse
#' @return A function taking the number of colors and returning hex codes
#' @examples
#' pal <- rang_pal("Kashan")
#' pal(3)
#' @export
rang_pal <- function(palette, direction = 1) {
  force(palette)
  force(direction)
  function(n) {
    as.character(rang(palette, n, type = "discrete", direction = direction))
  }
}

#' Sample a Rang palette as a smooth ramp
#'
#' @param palette Palette name, see names(rang_palettes)
#' @param direction 1 for the stored order, -1 to reverse
#' @param steps Number of colors sampled along the ramp
#' @return A character vector of hex colors
#' @examples
#' length(rang_ramp("Termeh", steps = 10))
#' @export
rang_ramp <- function(palette, direction = 1, steps = 256) {
  if (length(steps) != 1 || !is.numeric(steps) || is.na(steps) ||
      steps < 2 || steps != floor(steps)) {
    stop("steps must be a whole number of at least 2")
  }
  as.character(rang(palette, steps, type = "continuous", direction = direction))
}
