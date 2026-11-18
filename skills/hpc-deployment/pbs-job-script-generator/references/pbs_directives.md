# PBS resource mapping

For uniform requests, a PBS `select` resource list contains the number of
chunks and the resource values per chunk. Multiply MPI ranks per chunk
(`mpiprocs`) by threads per rank (`ompthreads`) for that chunk's `ncpus`.
Optional `mem` is also per chunk. Walltime applies to the whole job.

PBS directives precede the first executable line in the job script. Confirm
the queue and the placement policy with the receiving site. The selected
number of chunks can differ from the number of physical hosts.

- [NCAR PBS job scripts](https://ncar-hpc-docs.readthedocs.io/en/latest/pbs/job-scripts/)
- [Argonne LCRC running jobs on PBS Pro](https://docs.lcrc.anl.gov/running-jobs-at-lcrc/pbs-pro/)
