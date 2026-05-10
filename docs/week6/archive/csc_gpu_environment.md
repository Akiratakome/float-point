# CSC GPU Environment Probe

**Captured:** 2026-05-04 by user @beren

| Item | Value |
|---|---|
| Cluster login host | SSH alias `csc-athena` -> `yt455@athena.lsc.phy.private.cam.ac.uk` (`hostname`: `athena`) |
| GPU partition name | `csc-mphil-gpu` |
| `module avail cuda` candidates | pending: `module avail cuda 2>&1` returned `bash: line 1: module: command not found` in the non-interactive SSH shell |
| Selected module | none loaded; CUDA module system unavailable in non-interactive shell |
| nvcc version | pending: one probe saw CUDA 12.9 (`V12.9.41`) at `/lsc/opt/cuda-12.9/bin/nvcc`; a repeat non-interactive `which nvcc` returned not found |
| Driver version | 580.95.05 from GPU-node `nvidia-smi` |
| GPU model | NVIDIA GeForce RTX 5090 |
| Compute capability | 12.0 (`nvidia-smi --query-gpu=compute_cap`) |
| Default wall-clock limit | 6:00:00 (`sinfo -o "%P|%G|%D|%t|%l"`) |
| `--gres` syntax | `--partition=csc-mphil-gpu --gres=gpu:1` |
| Node home filesystem | `/lsc/zeushome/yt455` from `pwd`; `df -h $HOME` not captured cleanly |
| Build-artefact location | `$HOME/floatpoint` |

## Notes & gotchas observed
- `ssh -o BatchMode=yes -o ConnectTimeout=10 csc-athena hostname` succeeded once and returned `athena`.
- `sinfo -o "%P %G %D %t" | grep -i gpu || sinfo -o "%P %G %D %t"` returned `csc-mphil-gpu gpu:nvidia_geforce_rtx_5090:2(S:0) 2 idle`.
- `nvidia-smi` on login node: unavailable; command returned `bash: line 1: nvidia-smi: command not found`.
- `srun --partition=csc-mphil-gpu --gres=gpu:1 --time=00:01:00 nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv,noheader` completed and showed two NVIDIA GeForce RTX 5090 GPUs, driver 580.95.05, compute capability 12.0.
- `nvcc --version` is not stable in non-interactive SSH probes: one run reported CUDA 12.9 at `/lsc/opt/cuda-12.9/bin/nvcc`; a repeat `which nvcc` returned not found. D7 build scripts should set the CUDA path explicitly or run through the same interactive shell environment used on CSC.
- module purge required before module load? unknown; `module` was not available in the non-interactive SSH shell.
- Avoid assuming the plan default `--partition=ampere`; the observed GPU partition is `csc-mphil-gpu`.
