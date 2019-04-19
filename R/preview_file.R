#' Preview File
#'
#' Display PDF file.
#' @param fname File name to display
#' @keywords display
#' @export
#' @examples
#' show_close_graphics_msg()
 
preview_file <- function(fname, previewer="atril --preview")
{
  system(paste(previewer, fname), ignore.stderr=TRUE, wait=FALSE)
  cat("Close the graphic window using Ctrl-w.\n")
}
