# Week 13 MHD Verificarlo Smoke

Status: `runnable_environment`

Supported runner selected for sample mode: `docker`.

no Verificarlo MCA result was produced; no MCA evidence was generated.

## Runner probes

| runner | supported | return code | stderr |
|---|---|---:|---|
| native | False | 127 | `[WinError 2] 系统找不到指定的文件。` |
| wsl | False | 127 | `bash: line 1: verificarlo-c++: command not found` |
| docker | True | 0 | `` |
