#ifndef INPUT_READER
#define INPUT_READER

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char* getfield(char* line, int num);

float input_reader(FILE *stream);

#endif /* INPUT_READER */

