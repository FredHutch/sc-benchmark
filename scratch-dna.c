#include <stdio.h>

#include <sys/types.h>
#include <sys/wait.h>

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#define MB 1048576.
#define RND(x) (randomish() % x)

void print_usage(char *cmd)
{
   fprintf(stderr,
      "%s [-p workers] #files file_size random_size_multiplier output_dir\n",
      cmd);
}

unsigned int randomish() 
{
   static unsigned int x = 123456789;
   static unsigned int y = 362436069;
   static unsigned int z = 521288629;
   static unsigned int w = 88675123;
   unsigned int t;

   t = x ^ (x << 11);
   x = y; y = z; z = w;

   return w = w ^ (w >> 19) ^ (t ^ (t >> 8));
}

char *generate_random_dna(int len)
{
   char *bases="AGTC";
   char *dna,*dnaptr;
   int i;

   if ((dnaptr=dna=(char *)malloc(len))==NULL)
      fprintf(stderr,"Error: failed to allocate random DNA of size %d!\n",len);
   else
      for (i=0; i<len; i++)
         *dnaptr++=bases[RND(4)];

   return dna;
}

void generate_dna(char *filename,char *dna,int files,int bytes,int mult)
{
   int end=strlen(filename); /* save length of base filename */
   unsigned long wbytes=0;
   int nfiles=0;

   time_t start,elapsed;
   char istr[80];            /* buffer for string conversion of i */
   FILE *fp;
   int il;                   /* saved length of istr */
   int i;
   int n;

   time(&start);
   for (i=0; i<files; i++)
      {
      n=RND(mult)+1;
      il=sprintf(istr,"%d",i);
      strcpy(filename+end,istr);
      sprintf(filename+end+il,"-%d",n);

      if ((fp=fopen(filename,"w"))==NULL)
         fprintf(stderr,"Error: failed to open '%s'\n",filename);
      else
         {
         while (n--)
            {
            fwrite(dna,bytes,1,fp);
            fwrite(istr,il,1,fp);
            fwrite(filename,end,1,fp);
            wbytes+=(bytes+il+end);
            }

         fclose(fp);
         nfiles++;
         }
      }

   elapsed=time(NULL)-start;
   printf("%.2f MB written in %ld seconds (%.2f MB/s, %.2f files/s)\n",
      wbytes/MB,elapsed,wbytes/MB/elapsed,(float)nfiles/elapsed);
}

void do_work(int workers,int files,int bytes,int mult)
{
   char *dna=generate_random_dna(bytes);
   char filename[80];
   int hl; /* saved length of base filename */
   int i;

   gethostname(filename,79);
   strcat(filename,"-");

   if (workers==1)
      generate_dna(filename,dna,files,bytes,mult);
   else
      {
      hl=strlen(filename);
      for (i=0; i<workers; i++)
         if (fork()==0) /* if worker... */
            {
            sprintf(filename+hl,"%d-",getpid());
            generate_dna(filename,dna,files,bytes,mult);
            exit(0); /* worker complete */
            }

      while (workers--) /* wait for all workers to complete */
         wait(NULL);
      }
}

int atoi_validate(char *a,char *var_name)
{
   char *cnv;
   int val;

   val=strtol(a,&cnv,10);

   if (cnv==a || *cnv!='\0' || val<1)
      {
      fprintf(stderr,"Error: %s needs to be int>0!\n",var_name);
      val=-1; 
      }

   return val;
}

int parse_opt(int *argc,char ***argv,int remain,int *workers)
{
   int status=0;
   int opt;

   while ((opt=getopt(*argc,*argv,"p:h"))!=-1)
      switch (opt)
         {
         case 'p': /* number of parallel workers */
            if ((*workers=atoi_validate(optarg,"workers"))>0)
               break;

         case '?': /* miscellaneous error condition */
         case 'h': /* help! */
            status=-1;
         }

   *argv+=optind;
   *argc-=optind;

   return (status || *argc!=remain);
}

int main(int argc,char **argv)
{
   char *cmd=argv[0]; /* save name of program */
   int workers=1;     /* default to single */

   int files,bytes,mult; /* validated command line params */

   if (parse_opt(&argc,&argv,4,&workers)==0 &&
      (files=atoi_validate(argv[0],"# of files"))>0 &&
      (bytes=atoi_validate(argv[1],"size of files"))>0 &&
      (mult=atoi_validate(argv[2],"random multiplier"))>0 &&
      chdir(argv[3])==0)
      {
      do_work(workers,files,bytes,mult);
      }
   else
      print_usage(cmd);
}
