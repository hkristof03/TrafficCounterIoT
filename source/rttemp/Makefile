BINS=rttimer

SRCS=common.c
LIBS=-lrdkafka -lm -lrt

all: $(BINS)

rttimer: rttimer.c $(SRCS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LIBS)

# producer: producer.c $(SRCS)
# 	$(CC) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LIBS)

clean:
	rm -f *.o $(BINS)