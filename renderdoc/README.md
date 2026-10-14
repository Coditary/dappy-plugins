# renderdoc

[RenderDoc](https://renderdoc.org/) — open-source frame capture for Vulkan, OpenGL, D3D11/12.

```bash
sudo dnf install renderdoc   # or download from renderdoc.org
pip install -e dappy-plugins/graphics-launchers

dap-cli debug repl --adapter renderdoc ./game
# Runs: renderdoccmd capture ./game
```

Open `.rdc` captures in the RenderDoc UI for shader/pipeline inspection.
