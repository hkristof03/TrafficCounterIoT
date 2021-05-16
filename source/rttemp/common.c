/**
 * Copyright 2020 Confluent Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <assert.h>
#include <signal.h>

#include <librdkafka/rdkafka.h>

#include "common.h"

int run = 1;

/* Signal handler for SIGINT */
static void handle_ctrlc (int sig) {
        fprintf(stderr, "Terminating\n");
        run = 0;
}


/**
 * @brief Read key=value client configuration file from \p config_file,
 *        returning a populated config object on success, or NULL on error.
 */
rd_kafka_conf_t *read_config (const char *config_file) {
        FILE *fp;
        rd_kafka_conf_t *conf;
        char errstr[256];
        char buf[1024];
        int line = 0;

        if (!(fp = fopen(config_file, "r"))) {
                fprintf(stderr, "Failed to open %s: %s\n",
                        config_file, strerror(errno));
                return NULL;
        }

        conf = rd_kafka_conf_new();
        /* Read configuration file, line by line. */
        while (fgets(buf, sizeof(buf), fp)) {
                char *s = buf;
                char *t;
                char *key, *value;
                char errstr[256];

                line++;

                /* Left-trim */
                while (isspace(*s))
                        s++;

                /* Right-trim */
                t = s + strlen(s) - 1;
                while (t >= s && isspace(*t))
                        t--;
                *(t+1) = '\0';

                /* Ignore empty and comment lines */
                if (!*s || *s == '#')
                        continue;

                /* Expected format: "key=value".
                 * Find "=" and split line up into key and value. */
                if (!(t = strchr(s, '=')) || t == s) {
                        fprintf(stderr,
                                "%s:%d: invalid syntax: expected key=value\n",
                                config_file, line);
                        rd_kafka_conf_destroy(conf);
                        return NULL;
                }

                key = s;
                *t = '\0';
                value = t+1;

                /* Set configuration value in config object. */
                if (rd_kafka_conf_set(conf, key, value,
                                      errstr, sizeof(errstr)) !=
                    RD_KAFKA_CONF_OK) {
                        fprintf(stderr,
                                "%s: %d: %s\n", config_file, line, errstr);
                        rd_kafka_conf_destroy(conf);
                        return NULL;
                }
        }
        fclose(fp);

        /* Set up signal handlers for termination */
        signal(SIGINT, handle_ctrlc);
        signal(SIGTERM, handle_ctrlc);

        return conf;
}