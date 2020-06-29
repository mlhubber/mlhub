#' Inform User
#'
#' Display an informative message.
#' @param title The section title after processing with glue.
#' @param text The text to display after processing with glue.
#' @param delim Delimiter to highlight the title.
#' @param begin Text at the beginning.
#' @param end Text at the end.
#' @keywords informative
#' @export
#' @examples
#' mlcat()
 
mlcat <- function(title="", text="", delim="=", begin="", end="\n")
{
  title <- glue::glue(title)
  text <- paste(strwrap(glue::glue(text, .trim=FALSE)), collapse="\n")
  sep <- paste0(paste(rep(delim, nchar(title)), collapse=""),
                ifelse(nchar(title) > 0, "\n", ""))
  ttl_sep <- ifelse(nchar(title) > 0, "\n", "")
  cat(begin, sep, title, ttl_sep, sep, ttl_sep, text, end, sep="")
}
