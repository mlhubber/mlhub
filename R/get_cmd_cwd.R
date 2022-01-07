#' Get Command's CWD
#'
#' Get the command's cwd for local file access.
#' @keywords working directory
#' @export
#' @examples
#' get_cmd_cwd()
 
get_cmd_cwd <- function()
{
  cmd_cwd <- Sys.getenv("_MLHUB_CMD_CWD")
  if (cmd_cwd == "") cmd_cwd <- getwd()
  return(cmd_cwd)
}

