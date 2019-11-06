/*** modified version of: http://www.cmycode.com/2016/02/program-for-remove-comments-c.html ***/

#include <stdio.h>

#define COMMENT_START '/'
#define ONELINE_COMMENT 1
#define MULTILINE_COMMENT 2

int main(int argc, char const *argv[])
{
  char c;
  /* flag to indicate an escape character in a string */
  int escape = 0;
  int comment_type = 0;
  int skip_new_line = 0;
  /* flag to identify whether a string is being processed */
  int string_started = 0;
  int comment_ending = 0;
  /* flag denoting a comment is processing */
  int comment_started = 0;
  FILE *fp_in;

  /* file under processing, can be taken as argument */
  if (argc < 2) {
    fprintf(stderr, "error: input file not provided\n");
    return 1;
  }
  fp_in = fopen(argv[1], "r");

  if (fp_in == NULL) {
    fprintf(stderr, "error: could not open input file\n");
    return 1;
  }

  while (1) {
    c = fgetc(fp_in);

    if (feof(fp_in))
      break;

    /*
     * new lines immediately following a multi line comments
     * are skipped.
     */
    if (skip_new_line == 1) {
      skip_new_line = 0;
      if (c == '\n')
        continue;
    }

    /*
     * one line comments are skipped until a new line is
     * encountered
     *
     * corresponding counters and flags are reset
     */
    if (comment_type == ONELINE_COMMENT) {
      /*
       * single line comments can be extended using
       * escape character
       */
      if (c == '\\')
        escape = !escape;
      else if (c == '\n' && !escape) {
        comment_type = 0;
        comment_started = 0;
        printf("%c", c);
      } else {
        escape = 0;
      }
      continue;
    }

    /*
     * if a multi line comment is being processed, look
     * for the end of comment as it has two characters
     * unlike the single line comment
     *
     * truncating the new line flag is set here
     */
    if (comment_type == MULTILINE_COMMENT) {
      if (comment_ending) {
        if (c == '/') {
          comment_ending = 0;
          comment_started = 0;
          comment_type = 0;
          skip_new_line = 1;
          continue;
        }
        comment_ending = 0;
        /*
         * no continue here, as multiple stars can
         * occur before ending
         */
      }

      if (c == '*')
        comment_ending = 1;

      continue;
    }

    /*
     * identify the type of comment based on the
     * continuous character
     */
    if (comment_started) {
      if (c == '*') {
        comment_type = MULTILINE_COMMENT;
        continue;
      }
      if (c == '/') {
        comment_type = ONELINE_COMMENT;
        continue;
      }

      /*
       * put back the last character, since no
       * comment is detected
       */
      // fputc(COMMENT_START, fp_out);
      printf("%c", COMMENT_START);
      comment_started = 0;
    }

    /*
     * comments within strings are not treated as
     * comments. string processing includes
     * handling escape characters as well
     */
    if (string_started) {
      if (c == '\\')
        escape = !escape;
      else if (c == '\"' && !escape)
        string_started = 0;
      else
        escape = 0;

      // fputc(c, fp_out);
      printf("%c", c);
      continue;
    }

    /* detecting a string start */
    if (c == '\"')
      string_started = 1;

    /* detecting a comment start */
    if (c == COMMENT_START) {
      comment_started = 1;
      continue;
    }

    // fputc(c, fp_out);
    printf("%c", c);
  }

  fclose(fp_in);
}
