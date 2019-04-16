#' Ask Continue
#'
#' Propmt for the user to press Enter to continue.
#' @param msg A message to display.
#' @keywords continue
#' @export
#' @examples
#' ask_continue()
 
ask_continue <- function(msg="Press Enter to continue: ", begin="\n", end="\n")
{
  cat(begin, msg, sep="")
  invisible(readChar("stdin", 1))
  cat(end)
}

