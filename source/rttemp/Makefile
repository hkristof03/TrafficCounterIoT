BINS=rttimer

SRCS=common.c input_reader.c
LIBS=-lrdkafka -lm -lrt

all: $(BINS)

rttimer: rttimer.c $(SRCS)
	$(CC) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LIBS)

clean:
	rm -f *.o $(BINS)