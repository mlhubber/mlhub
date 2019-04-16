#' Inform User
#'
#' Display an informative message.
#' @param title The section title.
#' @param text The text to display.
#' @param delim Delimiter to highlight the title.
#' @param begin Text at the beginning.
#' @param end Text at the end.
#' @keywords informative
#' @export
#' @examples
#' inform_user()
 
inform_about <- function(title="", text="", delim="=", begin="", end="\n")
{
  sep <- paste0(paste(rep(delim, nchar(title)), collapse=""),
                ifelse(nchar(title) > 0, "\n", ""))
  ttl_sep <- ifelse(nchar(title) > 0, "\n", "")
  cat(begin, sep, title, ttl_sep, sep, ttl_sep, text, end)
}
