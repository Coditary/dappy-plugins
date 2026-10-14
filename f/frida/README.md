# frida

[Frida](https://frida.re/) — dynamic instrumentation for Android, iOS, and native desktop apps.

```bash
pip install frida-tools
pip install -e dappy-plugins/instrumentation-launchers

export FRIDA_TARGET=com.example.app
dap-cli debug repl --adapter frida hook.js
# frida -l hook.js $FRIDA_TARGET
```
