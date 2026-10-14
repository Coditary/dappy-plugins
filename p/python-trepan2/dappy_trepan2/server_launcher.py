"""Spawn trepan2 in TCP server mode for out-of-process debugging."""

from __future__ import print_function

import os
import sys


def main():
    if len(sys.argv) < 3:
        print("usage: python2 -m dappy_trepan2.server_launcher PORT PROGRAM [SCRIPT_ARGS...]", file=sys.stderr)
        sys.exit(2)

    port = int(sys.argv[1])
    program = os.path.abspath(sys.argv[2])
    script_args = sys.argv[3:]

    import trepan
    import trepan.api
    from trepan.debugger import Trepan
    from trepan.interfaces.server import ServerInterface
    from trepan.options import postprocess_options, process_options
    from trepan.version import __version__

    argv = ["trepan2", "--no-confirm", "--", program] + script_args
    opts, dbg_opts, _remaining = process_options(__version__, argv)

    connection_opts = {"IO": "TCP", "PORT": port, "HOST": "127.0.0.1"}
    intf = ServerInterface(connection_opts=connection_opts)
    actual_port = intf.inout.PORT
    print("TREPAN_SERVER_PORT={0}".format(actual_port))
    sys.stdout.flush()

    dbg_opts["interface"] = intf
    dbg = trepan.debugger_obj = Trepan(dbg_opts)
    dbg.core.add_ignore(main, trepan.api.debug)
    postprocess_options(dbg, opts)

    program_dir = os.path.dirname(program) or os.getcwd()
    sys.path.insert(0, program_dir)
    dbg.main_dirname = program_dir

    from trepan.exception import DebuggerQuit, DebuggerRestart

    try:
        dbg.run_script(program)
    except (DebuggerQuit, SystemExit):
        pass
    except DebuggerRestart:
        print("restart not supported", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
