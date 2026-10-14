# julia-debugger

[Debugger.jl](https://github.com/JuliaDebug/Debugger.jl) / Infiltrator.jl for Julia.

```bash
julia -e 'using Pkg; Pkg.add("Debugger")'
dap-cli debug repl --adapter julia-debugger script.jl
# @enter include("script.jl")
```
