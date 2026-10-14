# remix-debugger

[Remix IDE](https://remix.ethereum.org/) — standard EVM/Solidity transaction debugger (opcode + source step).

```bash
npm install -g @remix-project/remixd
pip install -e dappy-plugins/blockchain-launchers

dap-cli debug repl --adapter remix-debugger ./contracts
# remixd -s ./contracts --remix-ide https://remix.ethereum.org
```

In Remix: deploy → run transaction → **Debugger** tab (step forward/back through opcodes).
