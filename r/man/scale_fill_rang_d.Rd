\name{scale_fill_rang_d}
\alias{scale_fill_rang_d}
\alias{scale_color_rang_d}
\alias{scale_colour_rang_d}
\title{Discrete Rang scales for ggplot2}
\usage{
scale_fill_rang_d(palette, direction = 1, ...)

scale_color_rang_d(palette, direction = 1, ...)

scale_colour_rang_d(palette, direction = 1, ...)
}
\arguments{
  \item{palette}{One palette name from \code{names(rang_palettes)}.}
  \item{direction}{Use \code{1} for the stored direction or \code{-1} to reverse it.}
  \item{...}{Passed on to \code{ggplot2::discrete_scale()}, so the usual
    scale arguments such as \code{name}, \code{labels}, \code{breaks} and
    \code{guide} all work.}
}
\value{A ggplot2 scale.}
\description{
Fills or colors a categorical variable with a Rang palette. The colors follow
the stored pick order, so a small number of categories stays as far apart as
the palette allows.
}
\details{
ggplot2 is an optional dependency. These functions stop with a clear message
if it is not installed. A ggplot2 of 3.5.0 or newer is expected.

The first argument is called \code{palette} rather than \code{name}
because every ggplot2 scale already uses \code{name} for the legend
title. Passing \code{name} therefore sets the title as usual.
}
\seealso{\code{\link{scale_fill_rang_c}} for numeric variables.}
\examples{
\donttest{
if (requireNamespace("ggplot2", quietly = TRUE)) {
  library(ggplot2)
  ggplot(iris, aes(Species, Petal.Length, fill = Species)) +
    geom_violin() +
    scale_fill_rang_d("Golestan")
}
}
}
