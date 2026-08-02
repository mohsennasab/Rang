\name{rang}
\alias{rang}
\title{Build a Rang palette}
\usage{
rang(name, n, type = c("discrete", "continuous"), direction = 1,
     override_order = FALSE)
}
\arguments{
  \item{name}{One palette name from \code{names(rang_palettes)}.}
  \item{n}{A positive integer number of colors. The default is the full palette.}
  \item{type}{Either \code{"discrete"} or \code{"continuous"}.}
  \item{direction}{Use \code{1} for the stored direction or \code{-1} to reverse it.}
  \item{override_order}{Use the first \code{n} ramp colors instead of the discrete pick order.}
}
\value{A character vector of hex colors with class \code{"palette"}.}
\description{
Returns discrete selections from the stored pick order or an interpolated
continuous ramp. If \code{type} is omitted, requests larger than the source
palette use continuous interpolation.
}
\examples{
rang("Kashan")
rang("Kashan", 4)
rang("Termeh", 20, type = "continuous")
}
