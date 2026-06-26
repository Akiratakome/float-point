# Week 13 MHD Verificarlo Smoke

Status: `blocked_environment`

No supported native, WSL, or Docker Verificarlo runner was found.

no Verificarlo MCA result was produced; no MCA evidence was generated.

## Runner probes

| runner | supported | return code | stderr |
|---|---|---:|---|
| native | False | 127 | `[WinError 2] 系统找不到指定的文件。` |
| wsl | False | 4294967295 | `` |
| docker | False | 1 | `WARNING: Error loading config file: open C:\Users\tangy\.docker\config.json: Access is denied. permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine` |
