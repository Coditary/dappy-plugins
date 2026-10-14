"""Launchers for classic, script, modern, and enterprise language debuggers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-language-platform-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_ada_gnatdbg() -> int:
    gnatdbg = shutil.which("gnatdbg") or shutil.which("gdb")
    program = _program()
    if gnatdbg and program:
        return _run([gnatdbg, program])
    return _info(
        "Ada gnatdbg",
        [
            "GNAT Ada debugger (GDB backend).",
            "gnatdbg ./program or gdb ./program (GNAT -g build).",
            "See also native-gdb plugin.",
        ],
    )


def launch_fortran_gdb() -> int:
    gdb = os.environ.get("GDB") or shutil.which("gdb")
    program = _program()
    if gdb and program:
        return _run([gdb, program])
    return _info(
        "Fortran GDB",
        [
            "gfortran binaries debugged line-by-line with GDB.",
            "gfortran -g -O0 main.f90 && gdb ./a.out",
            "See native-gdb plugin.",
        ],
    )


def launch_delphi_debugger() -> int:
    if sys.platform != "win32":
        return _info("Delphi Debugger", ["Windows + RAD Studio required."], code=1)
    bds = os.environ.get("RAD_STUDIO") or shutil.which("bds.exe")
    program = _program()
    if bds:
        args = [bds]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "Embarcadero Delphi",
        [
            "RAD Studio integrated Object Pascal debugger.",
            "Set RAD_STUDIO to bds.exe.",
            "Run → Debug (F9) in IDE.",
        ],
    )


def launch_nim_gdb() -> int:
    nim = shutil.which("nim")
    gdb = shutil.which("gdb") or shutil.which("lldb")
    program = _program()
    if nim and program:
        subprocess.call([nim, "build", "-g", program])
        binary = os.path.splitext(program)[0]
        if gdb and os.path.isfile(binary):
            return _run([gdb, binary])
    if gdb and program and os.path.isfile(program):
        return _run([gdb, program])
    return _info(
        "nim-gdb",
        [
            "Nim compiles to C — debug with GDB/LLDB.",
            "nim build -g main.nim && gdb ./main",
            "Or: nim c -g --linedir:on main.nim",
        ],
    )


def launch_powershell_debugger() -> int:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    program = _program()
    if pwsh and program:
        return _run(
            [
                pwsh,
                "-NoExit",
                "-Command",
                f"Set-PSBreakpoint -Script '{program}' -Line 1; . '{program}'",
            ]
        )
    if pwsh:
        return _run([pwsh, "-NoExit", "-Command", "Get-Help Set-PSBreakpoint"])
    return _info(
        "PowerShell Debugger",
        [
            "Set-PSBreakpoint, Enter-PSHostProcess.",
            "VS Code PowerShell extension for DAP debugging.",
            "pwsh -File script.ps1 with breakpoints set.",
        ],
    )


def launch_autohotkey_debugger() -> int:
    if sys.platform != "win32":
        return _info("AutoHotkey Debugger", ["Windows + AutoHotkey required."], code=1)
    ahk = os.environ.get("AUTOHOTKEY") or shutil.which("AutoHotkey64.exe") or shutil.which("AutoHotkey.exe")
    program = _program()
    if ahk and program:
        return _run([ahk, "/Debug", program])
    return _info(
        "AutoHotkey Debugger",
        [
            "SciTE4AutoHotkey built-in breakpoint debugger.",
            "Install AHK v2; use SciTE4AutoHotkey Debug menu.",
            "Set AUTOHOTKEY to AutoHotkey executable.",
        ],
    )


def launch_gawk_debugger() -> int:
    gawk = shutil.which("gawk") or shutil.which("awk")
    program = _program()
    if gawk and program:
        return _run([gawk, "--debug", "-f", program])
    return _info(
        "gawk debugger",
        [
            "GNU Awk interactive debugger: break, step, print.",
            "gawk --debug -f script.awk",
            "Install gawk package.",
        ],
    )


def launch_tcl_debugger() -> int:
    tclsh = shutil.which("tclsh") or shutil.which("wish")
    program = _program()
    if tclsh and program:
        return _run([tclsh, program])
    return _info(
        "Tcl debugger",
        [
            "Tcl: debug command, tclpro debugger library.",
            "package require debug; debug::set bp …",
            "tclsh script.tcl",
        ],
    )


def launch_ocamldebug() -> int:
    ocamldebug = shutil.which("ocamldebug")
    program = _program()
    if ocamldebug and program:
        return _run([ocamldebug, program])
    return _info(
        "ocamldebug",
        [
            "Official OCaml bytecode debugger.",
            "ocamlc -g program.ml && ocamldebug program.cmo",
            "Install ocaml package.",
        ],
    )


def launch_dart_devtools() -> int:
    dart = shutil.which("dart") or shutil.which("flutter")
    program = _program()
    if dart and program:
        if "flutter" in dart:
            return _run([dart, "run", "--start-paused", program])
        return _run([dart, "run", "--enable-asserts", "--observe", program])
    return _info(
        "Dart DevTools",
        [
            "dart run --observe script.dart",
            "flutter run --start-paused",
            "Open DevTools in browser for Observatory/CDP.",
        ],
    )


def launch_julia_debugger() -> int:
    julia = shutil.which("julia")
    program = _program()
    if julia and program:
        return _run(
            [
                julia,
                "-e",
                'using Debugger; @enter include("' + program.replace('"', '\\"') + '")',
            ]
        )
    if julia:
        return _run([julia, "-e", "using Pkg; Pkg.add(\"Debugger\")"])
    return _info(
        "Julia Debugger",
        [
            "Debugger.jl / Infiltrator.jl packages.",
            "julia -e 'using Debugger; @enter include(\"script.jl\")'",
            "Or @infiltrate in Infiltrator.jl.",
        ],
    )


def launch_groovy_debugger() -> int:
    groovy = shutil.which("groovy") or shutil.which("groovysh")
    program = _program()
    if groovy and program:
        return _run([groovy, "-d", program] if groovy.endswith("groovy") else [groovy])
    return _info(
        "Groovy Debugger",
        [
            "Groovy runs on JVM — use JVMTI/jdb.",
            "groovysh for REPL; IDE attaches via java-jdb.",
            "See jvmti-debugger and java-jdb plugins.",
        ],
    )


def launch_abap_debugger() -> int:
    return _info(
        "ABAP Debugger",
        [
            "SAP GUI / Eclipse ADT integrated ABAP debugger.",
            "/h in transaction code for debug mode.",
            "Requires SAP system access — not available locally.",
            "Env: SAP_ASHOST, SAP_USER for ADT connections.",
        ],
    )


def launch_vba_vb6_debugger() -> int:
    if sys.platform != "win32":
        return _info(
            "VBA/VB6 Debugger",
            ["Windows + Microsoft Office or VB6 IDE required."],
            code=1,
        )
    return _info(
        "VBA/VB6 Debugger",
        [
            "VBA: Alt+F11 in Excel/Word → Debug → Toggle Breakpoint (F9).",
            "Immediate window (Ctrl+G) for live inspection.",
            "VB6: native IDE debugger with breakpoints.",
        ],
    )


def launch_fpdebug() -> int:
    lazarus = os.environ.get("LAZARUS") or shutil.which("lazarus")
    fpc = shutil.which("fpc")
    program = _program()
    if lazarus:
        args = [lazarus]
        if program:
            args.append(program)
        return _run(args)
    if fpc and program:
        return _run([fpc, "-g", "-gl", program])
    return _info(
        "fpdebug (Free Pascal)",
        [
            "FPC/Lazarus integrated debugger (fpdebug).",
            "fpc -g -gl program.pas && ./program",
            "Lazarus IDE: Run → Debug (F9).",
        ],
    )


def launch_vala_gdb() -> int:
    valac = shutil.which("valac")
    gdb = shutil.which("gdb")
    program = _program()
    if valac and program:
        out = os.path.splitext(program)[0]
        subprocess.call([valac, "-g", program, "-o", out])
        if gdb and os.path.isfile(out):
            return _run([gdb, out])
    if gdb and program and os.path.isfile(program):
        return _run([gdb, program])
    return _info(
        "Vala GDB",
        [
            "Vala compiles to C — debug with GDB.",
            "valac -g main.vala -o main && gdb ./main",
            "See native-gdb plugin.",
        ],
    )


def launch_actionscript_fdb() -> int:
    fdb = os.environ.get("FDB") or shutil.which("fdb") or shutil.which("fdb.exe")
    program = _program()
    if fdb:
        args = [fdb]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "Adobe fdb (ActionScript)",
        [
            "Flash/ActionScript 3 command-line debugger.",
            "Adobe AIR SDK / Flex SDK includes fdb.",
            "fdb script.as — break, continue, print.",
            "Legacy — Flash Player EOL.",
        ],
    )


def launch_common_lisp_slime() -> int:
    sbcl = shutil.which("sbcl") or shutil.which("clisp")
    program = _program()
    if sbcl and program:
        return _run([sbcl, "--load", program])
    return _info(
        "SLIME / Swank (Common Lisp)",
        [
            "Emacs + SLIME interactive debugger for SBCL/CCL.",
            "M-x slime; C-c C-c on defun; restarts in *sldb*.",
            "sbcl --load script.lisp",
        ],
    )


def launch_guile_debugger() -> int:
    guile = shutil.which("guile")
    program = _program()
    if guile and program:
        return _run([guile, "-l", program])
    if guile:
        return _run([guile])
    return _info(
        "Guile REPL Debugger",
        [
            "GNU Guile: ,backtrace ,debug ,bt in REPL.",
            "guile script.scm",
            "Geiser (Emacs) for Scheme debugging.",
        ],
    )


def launch_pharo_debugger() -> int:
    pharo = os.environ.get("PHARO") or shutil.which("pharo") or shutil.which("Pharo")
    program = _program()
    if pharo:
        args = [pharo]
        if program and program.endswith(".image"):
            args.append(program)
        return _run(args)
    return _info(
        "Pharo / Squeak Debugger",
        [
            "Live object-oriented debugger — edit code while halted.",
            "Download Pharo VM; open image; self halt in method.",
            "Set PHARO to pharo launcher path.",
        ],
    )


def launch_wasm_debugger() -> int:
    wasmtime = shutil.which("wasmtime")
    program = _program()
    if wasmtime and program:
        return _run([wasmtime, "run", "-d", program])
    wasmer = shutil.which("wasmer")
    if wasmer and program:
        return _run([wasmer, "run", "--invoke", "main", program])
    return _info(
        "WebAssembly Debugger",
        [
            "wasmtime run -d module.wasm — CLI step debugging.",
            "Chrome DevTools: wasm debugging in Sources panel.",
            "See chrome-devtools plugin for browser Wasm.",
        ],
    )


def launch_qsharp_debugger() -> int:
    dotnet = shutil.which("dotnet")
    if dotnet:
        return _run([dotnet, "tool", "list", "-g"])
    return _info(
        "Q# Quantum Debugger",
        [
            "Microsoft Quantum Development Kit in VS Code / Visual Studio.",
            "iqsharp / Q# simulators — trace qubits and gates.",
            "dotnet tool install -g Microsoft.Quantum.IQSharp",
            "Requires .NET SDK.",
        ],
    )


def launch_processing_debugger() -> int:
    processing = os.environ.get("PROCESSING") or shutil.which("processing-java")
    program = _program()
    if processing and program:
        return _run([processing, "--sketch=" + os.path.dirname(program) or ".", "--run"])
    pde = os.environ.get("PROCESSING_IDE")
    if pde:
        return _run([pde])
    return _info(
        "Processing IDE Debugger",
        [
            "Visual Java-based debugger for creative coding sketches.",
            "Processing IDE: Debug button (Java mode).",
            "Set PROCESSING to processing-java path.",
        ],
    )


def launch_dax_studio() -> int:
    dax = os.environ.get("DAX_STUDIO") or shutil.which("DaxStudio.exe") or shutil.which("DaxStudio")
    if dax:
        return _run([dax])
    return _info(
        "DAX Studio",
        [
            "Debug and optimize DAX queries for Power BI / Excel.",
            "https://daxstudio.org/ — connect to Power BI Desktop or SSAS.",
            "Set DAX_STUDIO to executable path (Windows).",
        ],
    )


def launch_godot_gdscript() -> int:
    godot = os.environ.get("GODOT") or shutil.which("godot") or shutil.which("godot4")
    program = _program()
    if godot:
        args = [godot]
        if program and os.path.isdir(program):
            args.extend(["--path", program, "--editor"])
        elif program:
            args.extend(["--path", os.path.dirname(program) or ".", "--editor"])
        else:
            args.append("--editor")
        return _run(args)
    return _info(
        "Godot GDScript Debugger",
        [
            "Integrated debugger in Godot Editor — breakpoints, stack, profiler.",
            "godot4 --editor --path ./project",
            "Debug → Deploy with Remote Debug for running game.",
        ],
    )


def launch_haxe_debugger() -> int:
    haxe = shutil.which("haxe")
    hl = shutil.which("hl") or shutil.which("hl.exe")
    program = _program()
    if haxe and program:
        subprocess.call([haxe, "-debug", program])
        if hl:
            return _run([hl, os.path.splitext(program)[0] + ".hl"])
    return _info(
        "Haxe Debugger",
        [
            "Compile with -debug; attach VS Code Haxe extension or hxdb.",
            "haxe -debug -main Main -hl out.hl && hl out.hl",
            "HashLink: hl --debug out.hl",
        ],
    )


def launch_eiffelstudio_debugger() -> int:
    estudio = os.environ.get("EIFFELSTUDIO") or shutil.which("estudio") or shutil.which("ec")
    program = _program()
    if estudio:
        args = [estudio]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "EiffelStudio Debugger",
        [
            "Contract-based visual debugger (pre/postconditions).",
            "EiffelStudio IDE → Run → Debug.",
            "https://www.eiffel.com/ — set EIFFELSTUDIO path.",
        ],
    )


def launch_factor_debugger() -> int:
    factor = shutil.which("factor") or shutil.which("factor-vm")
    if factor:
        return _run([factor])
    return _info(
        "Factor Debugger",
        [
            "Stack-based interactive debugger in Factor listener.",
            "factor -run=script.factor",
            "In listener: debug word — inspect data stack step by step.",
        ],
    )


def launch_crystal_debugger() -> int:
    crystal = shutil.which("crystal")
    program = _program()
    if crystal and program:
        return _run([crystal, "run", "--debug", program])
    lldb = shutil.which("lldb")
    gdb = shutil.which("gdb")
    if program and lldb:
        return _run([lldb, program])
    if program and gdb:
        return _run([gdb, program])
    return _info(
        "Crystal Debugger",
        [
            "crystal run --debug script.cr",
            "Or LLVM: crystal build -g app.cr && lldb ./app",
            "See native-lldb / native-gdb plugins.",
        ],
    )


def launch_ghostscript_debugger() -> int:
    gs = shutil.which("gs") or shutil.which("ghostscript")
    program = _program()
    if gs and program:
        return _run([gs, "-Z", "-dNOPAUSE", "-dBATCH", program])
    if gs:
        return _run([gs, "-Z"])
    return _info(
        "Ghostscript PostScript Debugger",
        [
            "Interactive PostScript debugging: gs -Z script.ps",
            "Step through PostScript graphics programs.",
            "Install ghostscript package.",
        ],
    )


_HANDLERS = {
    "ada-gnatdbg": launch_ada_gnatdbg,
    "fortran-gdb": launch_fortran_gdb,
    "delphi-debugger": launch_delphi_debugger,
    "nim-gdb": launch_nim_gdb,
    "powershell-debugger": launch_powershell_debugger,
    "autohotkey-debugger": launch_autohotkey_debugger,
    "gawk-debugger": launch_gawk_debugger,
    "tcl-debugger": launch_tcl_debugger,
    "ocamldebug": launch_ocamldebug,
    "dart-devtools": launch_dart_devtools,
    "julia-debugger": launch_julia_debugger,
    "groovy-debugger": launch_groovy_debugger,
    "abap-debugger": launch_abap_debugger,
    "vba-vb6-debugger": launch_vba_vb6_debugger,
    "fpdebug": launch_fpdebug,
    "vala-gdb": launch_vala_gdb,
    "actionscript-fdb": launch_actionscript_fdb,
    "common-lisp-slime": launch_common_lisp_slime,
    "guile-debugger": launch_guile_debugger,
    "pharo-debugger": launch_pharo_debugger,
    "wasm-debugger": launch_wasm_debugger,
    "qsharp-debugger": launch_qsharp_debugger,
    "processing-debugger": launch_processing_debugger,
    "dax-studio": launch_dax_studio,
    "godot-gdscript": launch_godot_gdscript,
    "haxe-debugger": launch_haxe_debugger,
    "eiffelstudio-debugger": launch_eiffelstudio_debugger,
    "factor-debugger": launch_factor_debugger,
    "crystal-debugger": launch_crystal_debugger,
    "ghostscript-debugger": launch_ghostscript_debugger,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-language-platform-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
