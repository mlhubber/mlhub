#' Get CWD
#'
#' Get the commands cwd for local file access.
#' @keywords working directory
#' @export
#' @examples
#' mlcwd()
 
mlcwd <- function()
{
  cmd_cwd <- Sys.getenv("_MLHUB_CMD_CWD")
  if (cmd_cwd == "") cmd_cwd <- getwd()
  return(cmd_cwd)
}

