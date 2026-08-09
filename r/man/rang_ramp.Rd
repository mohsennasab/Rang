\name{rang_ramp}
\alias{rang_ramp}
\title{Sample a Rang palette as a smooth ramp}
\usage{
rang_ramp(palette, direction = 1, steps = 256)
}
\arguments{
  \item{palette}{One palette name from \code{names(rang_palettes)}.}
  \item{direction}{Use \code{1} for the stored direction or \code{-1} to reverse it.}
  \item{steps}{Number of colors sampled along the ramp. The default is 256.}
}
\value{A character vector of hex colors.}
\description{
Interpolates the palette into an evenly spaced ramp. This is the vector the
continuous scales pass to ggplot2, and it also works directly with
\code{ggplot2::scale_fill_gradientn()} or base graphics.
}
\examples{
length(rang_ramp("Termeh", steps = 10))
rang_ramp("Iwan", steps = 5)
}
