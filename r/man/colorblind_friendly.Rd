\name{colorblind_friendly}
\alias{colorblind_friendly}
\title{Check the project CVD separation flag}
\usage{
colorblind_friendly(name)
}
\arguments{
  \item{name}{One palette name from \code{names(rang_palettes)}.}
}
\value{A single logical value.}
\description{
Reports whether the complete palette passes Rang's pairwise CIEDE2000 rule
under the four viewing simulations used by the project. This screening flag
is not an accessibility guarantee.
}
\examples{
colorblind_friendly("Golestan")
}
