# wireshark

[Wireshark](https://www.wireshark.org/) — packet-level network debugger.

```bash
sudo dnf install wireshark-cli wireshark
pip install -e dappy-plugins/network-launchers

dap-cli debug repl --adapter wireshark capture.pcapng
# Or live: tshark -i eth0
```

Pair with `wireshark-stream` for Follow TCP/UDP Stream analysis.
