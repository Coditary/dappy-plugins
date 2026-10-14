# php-xdebug

[Xdebug](https://xdebug.org) — de-facto standard PHP debugger and profiler.

## Install

```bash
sudo dnf install php php-pecl-xdebug
pip install -e dappy-plugins/php-xdebug
```

Enable in `php.ini`:
```ini
zend_extension=xdebug
xdebug.mode=debug
xdebug.client_port=9003
```

## Usage

```bash
dap-cli debug repl --adapter php-xdebug script.php
```

Set `PHP_DEBUG_ADAPTER` to VS Code `php-debug` adapter for full DAP.
