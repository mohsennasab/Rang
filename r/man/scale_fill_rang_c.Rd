\name{scale_fill_rang_c}
\alias{scale_fill_rang_c}
\alias{scale_color_rang_c}
\alias{scale_colour_rang_c}
\title{Continuous Rang scales for ggplot2}
\usage{
scale_fill_rang_c(palette, direction = 1, steps = 256, ...)

scale_color_rang_c(palette, direction = 1, steps = 256, ...)

scale_colour_rang_c(palette, direction = 1, steps = 256, ...)
}
\arguments{
  \item{palette}{One palette name from \code{names(rang_palettes)}.}
  \item{direction}{Use \code{1} for the stored direction or \code{-1} to reverse it.}
  \item{steps}{Number of colors sampled along the ramp. The default is 256.}
  \item{...}{Passed on to the matching ggplot2 gradient scale, so the usual
    scale arguments such as \code{name}, \code{limits}, \code{labels} and
    \code{guide} all work.}
}
\value{A ggplot2 scale.}
\description{
Fills or colors a numeric variable with a smooth Rang ramp. Palettes whose
lightness runs steadily in one direction, such as Termeh, Iwan, Khatam and
Rostan, suit ordered measurements like depth, elevation and rainfall.
}
\details{
ggplot2 is an optional dependency. These functions stop with a clear message
if it is not installed. A ggplot2 of 3.5.0 or newer is expected.

The first argument is called \code{palette} rather than \code{name}
because every ggplot2 scale already uses \code{name} for the legend
title. Passing \code{name} therefore sets the title as usual.
}
\seealso{\code{\link{scale_fill_rang_d}} for categorical variables.}
\examples{
\donttest{
if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  ggplot(faithfuld, aes(waiting, eruptions, fill = density)) +
    geom_raster() +
    scale_fill_rang_c("Termeh")
}
}
}
