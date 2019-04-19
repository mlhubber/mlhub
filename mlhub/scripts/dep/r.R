# Install and configure R dependencies for the pre-built model from CRAN.
#
# We choose to install user local packages using install-packages()
# rather than OS supplied packages to minimise the need for sys admin
# access from within mlhub. R itself is often operating system
# installed though not necessarily.
#
# By default, the current working directory (CWD) is where the model
# package is installed.

########################################################################
# Identify where they will be installed - the user's local R library.

lib <- file.path("./R")

# Ensure the user's local R library exists.

dir.create(lib, showWarnings=FALSE, recursive=TRUE)

# Add the user's local R library to reuse the installed packages.

.libPaths(c(lib, .libPaths()))
lib <- .libPaths()[1]

# Helper for catching installation problem.

try_install <- function(expr)
{

  tryCatch(
    expr,
    error=function(e) {
      stop(e)
    },
    warning=function(w){
      stop(w)
    })
}

########################################################################
# Identify the required packages and how to install them.

allargs <- commandArgs(trailingOnly=TRUE)
no_devtools <- length(installed.packages('devtools')) == 0

src <- allargs[1]  # Dependency type: cran, github, or cran-2018-12-01 for a CRAN snapshot
snapshot <- FALSE
if (grepl("^cran-", src))
{
  snapshot <- TRUE
}

packages <- allargs[-1]

isball <- grepl('(.tar|.zip|.gz)$', packages)
isurl <- grepl('^http(|s)://', packages)
isversion <- grepl('=', packages)
haslash <- grepl('/', packages)

name_pkgs <- packages[! isball & ! isversion & ! isurl & ! haslash]  # packages specified by names
github_pkgs <- packages[! isurl & ! isball & ! isversion & haslash]  # packages from GitHub
version_pkgs <- packages[isversion & !isurl]  # packages with versions

link_pkgs <- packages[isurl]                  # packages specified by URLs
ball_pkgs <- packages[isball & ! isurl]       # packages specified by path
extra_pkgs <- c(link_pkgs, ball_pkgs)

########################################################################
# Install packages with latest version into the local R library.

if (!snapshot)
{
  already <- installed.packages()[,"Package"]
  already_ver <- installed.packages()[,"Version"]
  repos <- getOption("repos")
  avail_cran_pkgs <- available.packages()[, 'Package']
  already_latest <- NULL
  for (pkg in name_pkgs)
  {
    if (pkg %in% already)
    {
      latest_ver <- old.packages(instPkgs=installed.packages()[pkg, , drop=FALSE])[, 'ReposVer']
      if (is.null(latest_ver))
      {
        already_latest <- c(already_latest, pkg)
        next
      }
    }
  }
  if (! is.null(already_latest))
    cat("\n*** The following R packages are already at their latest versions:",
        "\n ", paste(already_latest), "\n")

  for (pkg in setdiff(name_pkgs, already_latest))
  {
    cat(sprintf(paste0("\n*** Installing the latest version of the R package ",
                       "'%s'\n  from CRAN into '%s' ...\n"), pkg, lib))

    if (! pkg %in% avail_cran_pkgs)
    {
      stop(sprintf("The R package '%s' is not available from CRAN.", pkg))
    }

    if (is.null(repos))  # In case there is no default repos defined.
      try_install(install.packages(pkg, repos="https://cloud.r-project.org", lib=lib))
    else
      try_install(install.packages(pkg, lib=lib))
  }

}

########################################################################
# Install packages from GitHub into the local R library.
# TODO: Check version to avoid repeated installation

if (!snapshot)
{
  already <- installed.packages()[,"Package"]
  for (pkg in github_pkgs)
  {
    owner <- dirname(pkg)
    repo <- basename(pkg)
    if (basename(pkg) %in% already)
    {
      cat(sprintf("\n*** %s's R package '%s' is already installed.\n", owner, repo))
    }
    else
    {
      cat(sprintf("\n*** Installing %s's R package '%s' from GitHub into '%s' ...\n", owner, repo, lib))
      try_install(devtools::install_github(pkg, lib=lib))
    }
  }
}


########################################################################
# Install packages with specific versions into the local R library.

if (!snapshot)
{
  already <- installed.packages()[,"Package"]
  for (pkg in version_pkgs)
  {
    name_ver <- strsplit(pkg, '=')[[1]]
    name <- trimws(name_ver[1])
    ver <- trimws(name_ver[2])

    if (name %in% already && packageVersion(name) == ver)
    {
      cat(sprintf("\n*** The R package '%s' version '%s' is already installed.\n", name, ver))
    }
    else
    {
      cat(sprintf("\n*** Installing the R package '%s' version '%s' into '%s' ...\n", name, ver, lib))
      try_install(devtools::install_version(name, version=ver, repos="https://cloud.r-project.org", lib=lib))
    }
  }
}


########################################################################
# Install packages specified by path or URL into the local R library.
# TODO: Check installed packages and versions.

if (!snapshot)
{
  # if rattle version is < 5.2.0 then install downloaded package from togaware.

  already <- installed.packages()[,"Package"]
  if ("rattle" %in% already && packageVersion("rattle") < "5.2.0")
    link_pkgs <- c(extra_pkgs, "https://togaware.com/access/rattle_5.2.5.tar.gz")

  for (pkg in extra_pkgs)
  {
    cat(sprintf("\n*** Installing the R package from '%s' into '%s' ...\n", pkg, lib))
    try_install(install.packages(pkg, repos=NULL, lib=lib))
  }
}

########################################################################
# Install packages from snapshot into the local R library.
# TODO: Check installed packages and versions.

if (snapshot)
{
  stamp <- substr(src, 6, 15)
  for (pkg in name_pkgs)
  {
    cat(sprintf("\n*** Installing the R package '%s' from snapshot '%s' into '%s' ...\n", pkg, stamp, lib))
    try_install(install.packages(packages, repos=paste('https://cran.microsoft.com/snapshot/', stamp, sep=''), lib=lib, dep=TRUE))
  }
}
