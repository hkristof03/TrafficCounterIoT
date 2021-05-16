#include "input_reader.h"


const char* getfield(char* line, int num) {
    const char* tok;
    for (tok = strtok(line, ",");
            tok && *tok;
            tok = strtok(NULL, "\n"))
    {
        if (!--num)
            return tok;
    }
    return NULL;
}

float input_reader(FILE *stream) {

    char line[1024];
    if (fgets(line, 1024, stream)) {
        char* tmp = strdup(line);
        float ret = atof(getfield(tmp, 1));
        free(tmp);
        return ret;
    }
    return -1000.0;
}