# forge-debugger

[Foundry](https://book.getfoundry.sh/) — line-based Solidity debugger in the terminal.

```bash
curl -L https://foundry.paradigm.xyz | bash && foundryup
pip install -e dappy-plugins/blockchain-launchers

dap-cli debug repl --adapter forge-debugger test/Counter.t.sol
# forge test --debug -vvv
```

Shows call stacks and source lines during `forge test --debug`.
