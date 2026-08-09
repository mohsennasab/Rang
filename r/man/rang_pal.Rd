\name{rang_pal}
\alias{rang_pal}
\title{Palette function for a Rang palette}
\usage{
rang_pal(palette, direction = 1)
}
\arguments{
  \item{palette}{One palette name from \code{names(rang_palettes)}.}
  \item{direction}{Use \code{1} for the stored direction or \code{-1} to reverse it.}
}
\value{A function taking the number of colors and returning hex codes.}
\description{
Returns a function of \code{n} suitable for \code{ggplot2::discrete_scale()}
and other places that expect a palette generator rather than a fixed vector.
}
\examples{
pal <- rang_pal("Kashan")
pal(3)
}
