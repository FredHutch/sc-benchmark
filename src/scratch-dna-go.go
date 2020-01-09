package main

import (
	"bufio"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"sync"
	"strconv"
	"time"
)

func main() {

	// define and set default command parameter flags
	var pFlag = flag.Int("p", 1, "Optional: set number of concurrent file writers to use; defaults to 1")
	var vFlag = flag.Bool("v", false, "Optional: Turn on verbose output mode; it will print the progres every second")

	flag.Parse()
        args := flag.Args()

        if len(args) != 4 {
		fmt.Fprintf(os.Stderr, "Error! 4 positional arguments required.\n")
                fmt.Fprintf(os.Stderr, "\nUsage: %s [-p <parallel threads> -v (verbose)] <number-of-files> <file-size-bytes> <random-file-size-multiplier> <writable-directory>\n", os.Args[0])
                fmt.Fprintf(os.Stderr, "\nExample: %s -v -p 8 1024 10485760 1 /tmp\n\n", os.Args[0])
		os.Exit(1)
	}

        nFlag, _ := strconv.Atoi(args[0])
        sFlag, _ := strconv.Atoi(args[1])
        mFlag, _ := strconv.Atoi(args[2])
        dFlag := args[3]

	runtime.GOMAXPROCS(*pFlag)
	size := sFlag
	wg := new(sync.WaitGroup)
	sema := make(chan struct{}, *pFlag)
	out := genstring(size)
	progress := make(chan int64, 256)
	start := time.Now().Unix()

        hostname, err := os.Hostname()
        if err != nil {
                hostname = "dna"
        }
	rand.Seed(time.Now().UnixNano())
	hostname += fmt.Sprintf("_%08d",rand.Intn(100000000))


        go func() {
                wg.Wait()
                close(progress)
        }()


	fmt.Printf("Writing %d files with filesizes between %.1f MB and %.1f MB...\n\n", nFlag, float64(size)/1048576, float64(size)/1048576 * float64(mFlag))

	for x := 1; x <= nFlag; x++ {
		wg.Add(1)
		go spraydna(x, wg, sema, &out, dFlag, progress, mFlag, hostname)
	}

        // If the '-v' flag was provided, periodically print the progress stats
        var tick <-chan time.Time
        if *vFlag {

	        tick = time.Tick(1000 * time.Millisecond)
        }

        var nfiles, nbytes int64

loop:
        for {
                select {
                case size, ok := <-progress:
                        if !ok {
				break loop // progress was closed
                        }
                        nfiles++
                        nbytes += size
                case <-tick:
                        printProgress(nfiles, nbytes, start)
                }
        }

        // Final totals
        printDiskUsage(nfiles, nbytes, start)

}


func genstring(size int) []byte {
	//r := rand.New(rand.NewSource(time.Now().UnixNano()))
	rand.Seed(time.Now().UnixNano())
	fmt.Printf("Building random DNA sequence of %.1f MB...\n\n", float64(size)/1048576)
	dnachars := []byte("GATC")
	dna := make([]byte, 0)
	for x := 0; x < size; x++ {
		dna = append(dna, dnachars[rand.Intn(len(dnachars))])
	}
	return dna
}

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func spraydna(count int, wg *sync.WaitGroup, sema chan struct{}, out *[]byte, dir string, progress chan<- int64, mFlag int, hostname string) {
	defer wg.Done()
	sema <- struct{}{}        // acquire token
	defer func() { <-sema }() // release token
	path := fmt.Sprintf("%s/%s", dir, hostname)

	if _, err := os.Stat(path); os.IsNotExist(err) {
		os.Mkdir(path, 0755)
	}

	multiple := rand.Intn(mFlag) + 1
	filename := fmt.Sprintf("%s/%s-%d-%d.txt", path, hostname, count, multiple)
	f, err := os.Create(filename)
	check(err)
	defer f.Close()

	w := bufio.NewWriter(f)
	writtenBytes := 0
	B := 0
	for j := 0; j < multiple; j++ {
		B, _ = w.Write(*out)
		writtenBytes += B
		//fmt.Printf("wrote %d bytes\n", writtenBytes)
		w.Flush()
	}
	progress <- int64(writtenBytes) 
}

func printProgress(nfiles, nbytes int64, start int64) {
        now := time.Now().Unix()
        elapsed := now - start
        if elapsed == 0 {
                elapsed = 1
        }
        fps := nfiles / elapsed
        tp := nbytes / elapsed
        fmt.Printf("Files Completed: %7d, Data Written: %5.1fGiB, Files Remaining: %7d, Cur FPS: %5d, Throughput: %4d MiB/s\n", nfiles, float64(nbytes)/1073741824, runtime.NumGoroutine(), fps, tp/1048576)
}

// Prints the final summary
func printDiskUsage(nfiles, nbytes int64, start int64) {
        stop := time.Now().Unix()
        elapsed := stop - start
        if elapsed == 0 {
                elapsed = 1
        }
        fps := nfiles / elapsed
        tp := nbytes / elapsed
        fmt.Printf("\nDone!\nNumber of Files Written: %d, Total Size: %.1fGiB, Avg FPS: %d, Avg Throughput: %d MiB/s, Elapsed Time: %d seconds\n", nfiles, float64(nbytes)/1073741824, fps, tp/1048576, elapsed)
}
