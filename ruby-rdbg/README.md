# ruby-rdbg

[rdbg](https://github.com/ruby/debug) — Ruby 3.1+ debugger (supports DAP natively).

```bash
gem install debug
pip install -e dappy-plugins/language-launchers

dap-cli debug repl --adapter ruby-rdbg script.rb
# Runs: rdbg -n --open script.rb
```

For IDE-grade DAP, point your editor at `rdbg --open --dap` directly.
