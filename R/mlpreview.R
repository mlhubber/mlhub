#' Preview File
#'
#' Display PDF file.
#' @param fname File name to display
#' @param msg Message to display after displaying the file.
#' @param previewer The command to run to display the file.
#' @keywords display
#' @export
#' @examples
#' mlpreview()
 
mlpreview <- function(fname,
                      msg="Close the graphic window using Ctrl-w.\n",
                      begin="\n",
                      previewer="atril --preview")
{
  system(paste(previewer, fname), ignore.stderr=TRUE, wait=FALSE)
  cat(begin, msg, sep="")
}
