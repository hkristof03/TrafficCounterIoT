#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include <signal.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>

#include <librdkafka/rdkafka.h>

#include "common.h"

rd_kafka_t *create_producer(const char *topic, rd_kafka_conf_t *conf) {
    rd_kafka_t *rk;
    char errstr[512];

    /* Create producer.
        * A successful call assumes ownership of \p conf. */
    rk = rd_kafka_new(RD_KAFKA_PRODUCER, conf, errstr, sizeof(errstr));
    if (!rk) {
            fprintf(stderr, "Failed to create producer: %s\n", errstr);
            rd_kafka_conf_destroy(conf);
            return NULL;
    }

    return rk;
}

double getTime() {
    struct timespec now;
    clock_gettime(CLOCK_REALTIME, &now);
    return now.tv_sec + now.tv_nsec * 1e-9;
}

double getElapsedTime(double startTime) {
    return getTime() - startTime;
}

timer_t timerID;
int count = 0;
double startTime = 0.0;
double elapsedSum = 0.0;
rd_kafka_t *rk;
const char *topic;
const char *config_file;
rd_kafka_conf_t *conf;
int delivery_counter = 0;

void handlerTimer(int signalnumber, siginfo_t *si, void *uc) {


    timer_t *timerIDp = si->si_value.sival_ptr;

    count++;

     /* Produce messages */
    if(run) {

        const char *user = "default";
        char json[64];

        snprintf(json, sizeof(json),
                    "{ \"count\": %d }", 123);

        fprintf(stderr, "Producing message to %s: %s=%s\n",
                topic, user, json);

        rd_kafka_resp_err_t err;
        /* Asynchronous produce */
        err = rd_kafka_producev(
                rk,
                RD_KAFKA_V_TOPIC(topic),
                RD_KAFKA_V_KEY(user, strlen(user)),
                RD_KAFKA_V_VALUE(json, strlen(json)),
                /* producev() will make a copy of the message
                    * value (the key is always copied), so we
                    * can reuse the same json buffer on the
                    * next iteration. */
                RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
                RD_KAFKA_V_OPAQUE(&delivery_counter),
                RD_KAFKA_V_END);
        if (err) {
                fprintf(stderr, "Produce failed: %s\n",
                        rd_kafka_err2str(err));
        }
  
        /* Wait for outstanding messages to be delivered,
            * unless user is terminating the application. */
        rd_kafka_flush(rk, 15*1000);
    }

    if (count == 5) {
        //DISABLE AND DELETE THE TIMER
        //If the selected timer is already started, it will be disabled and
        //no signals or actions assigned to the timer will be delivered or executed.
        //A pending signal from an expired timer, however, will not be removed.
        timer_delete(timerID);


        //Terminates the process ("quits from while(1)")
        raise(SIGTERM);
        exit(0);
    }
}

int main (int argc, char **argv) {
    
    if (argc != 3) {
            fprintf(stderr, "Usage: %s <topic> <config-file>\n", argv[0]);
            exit(1);
    }

    topic = argv[1];
    config_file = argv[2];

    if (!(conf = read_config(config_file)))
            return 1;

    rk = create_producer(topic, conf);

    //SET RR SCHEDULER FOR THIS PROCESS
    struct sched_param schedpar;
    schedpar.sched_priority = 12;
    
    //Requires root access
    if (sched_setscheduler(getpid(), SCHED_RR, &schedpar)) {
        perror("Failed to set scheduler");
        exit(1);
    }
    
    //CREATE TIMER WITH RT SIGNAL
    struct sigevent sigev;
    sigev.sigev_notify = SIGEV_SIGNAL;
    sigev.sigev_signo = SIGRTMIN + 4;
    sigev.sigev_value.sival_ptr = &timerID; //Passing the timer's ID for the sigactionHandler
    
    //1. parameter: The timer will use this clock
    //2. parameter: Raised sigevent on expiration (NULL means SIGALRM)
    //3. parameter: The generated timer's ID
    if (timer_create(CLOCK_REALTIME, &sigev, &timerID)) {
        perror("Failed to create Timer");
        exit(1);
    }

    //Register signal handler
    struct sigaction sigact;
    sigemptyset(&sigact.sa_mask); //no blocked signals only the one, which arrives
    sigact.sa_sigaction = handlerTimer;
    sigact.sa_flags = SA_SIGINFO;
    sigaction(SIGRTMIN + 4, &sigact, NULL); //an alarm signal is set

    struct itimerspec timer;
    timer.it_interval.tv_sec = 3;       //it will be repeated after 3 seconds
    timer.it_interval.tv_nsec = 0;      //nsec - nanoseconds - 10^(-9) seconds
    timer.it_value.tv_sec = 3;          //remaining time till expiration
    timer.it_value.tv_nsec = 0;

    //ARM THE TIMER
    //1. parameter: timer to arm
    //2. parameter: 0 - relative timer, TIMER_ABSTIME - absolute timer
    //3. parameter: expiration and interval settings to be used
    //4. parameter: previous timer settings (if needed)
    startTime = getTime();
    timer_settime(timerID, 0, &timer, NULL);

    struct itimerspec expires;
    while (1) {
        sleep(1);                         //be careful with sleep
        timer_gettime(timerID, &expires); //reads the remaining time
    }

    rd_kafka_destroy(rk);

    return 0;
}