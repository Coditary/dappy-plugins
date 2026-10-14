# arm-ddt

**ARM DDT** (formerly Allinea DDT) — MPI/OpenMP parallel debugger for HPC clusters.

```bash
module load ddt   # on your supercomputer
export ARM_DDT=/path/to/ddt
dap-cli debug repl --adapter arm-ddt ./mpi_simulation
# mpirun -np 128 ddt ./simulation
```
