#' Preview File
#'
#' Display PDF file.
#' @param fname File name to display
#' @param msg Message to display after displaying the file.
#' @param previewer The command to run to display the file.
#'
#' @importFrom glue glue
#' @keywords display
#' @export
#' @examples
#' mlpreview()
 
mlpreview <- function(fname,
                      msg="Close the graphic window using Ctrl-W.",
                      begin="\n",
                      previewer="xdg-open",
                      end="\n")
{
  if (Sys.getenv("DISPLAY") != "")
  {
    system(paste(previewer, fname), ignore.stderr=TRUE, wait=FALSE)
    cat(begin, msg, end, sep="")
  } else {
    cat("\n**** Graphic display not found. Needs to run on a desktop. ****\n")
  }
}
