#!/usr/bin/env python3
"""
Builds EIPScanner from source.
Usage: python scripts/build_eipscanner.py
"""

import sys
from build_config import BuildConfig, IS_WINDOWS, IS_LINUX


def _patch_eipscanner_for_windows(cfg, eip_dir):
    """Apply patches to EIPScanner for Windows MSVC compatibility.

    EIPScanner already has partial Windows support (#ifdef _WIN32 in socket files).
    We only patch files that have unguarded POSIX includes.
    """
    print("\nApplying Windows patches...")
    patches_applied = 0

    # POSIX headers that don't exist on Windows
    posix_headers = [
        "sys/socket.h", "netinet/in.h", "arpa/inet.h",
        "unistd.h", "netdb.h",
    ]

    source_files = list(eip_dir.rglob("*.cpp")) + list(eip_dir.rglob("*.h"))

    for fpath in source_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        lines = content.split('\n')
        new_lines = []
        changed = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check if this line is a POSIX include that needs a guard
            needs_guard = False
            for hdr in posix_headers:
                if stripped == f'#include <{hdr}>':
                    # Check if already inside a platform guard
                    prev_stripped = ""
                    for j in range(len(new_lines) - 1, -1, -1):
                        prev_stripped = new_lines[j].strip()
                        if prev_stripped:
                            break
                    already_guarded = (
                        prev_stripped.startswith("#ifdef _WIN32") or
                        prev_stripped.startswith("#ifndef _WIN32") or
                        prev_stripped.startswith("#else") or
                        prev_stripped.startswith("#if defined(_WIN32)") or
                        prev_stripped.startswith("#if !defined(_WIN32)")
                    )
                    if not already_guarded:
                        needs_guard = True
                    break

            if needs_guard:
                new_lines.append("#ifndef _WIN32")
                new_lines.append(line)
                new_lines.append("#endif")
                changed = True
            else:
                new_lines.append(line)
            i += 1

        if changed:
            fpath.write_text('\n'.join(new_lines), encoding="utf-8")
            patches_applied += 1
            print(f"  Patched: {fpath.relative_to(eip_dir)}")

    # Add _WINSOCK_DEPRECATED_NO_WARNINGS to suppress inet_ntoa warnings
    cmakelists = eip_dir / "CMakeLists.txt"
    if cmakelists.exists():
        content = cmakelists.read_text(encoding="utf-8")
        if "_WINSOCK_DEPRECATED_NO_WARNINGS" not in content:
            content = content.replace(
                "add_compile_definitions(NOMINMAX)",
                "add_compile_definitions(NOMINMAX)\n"
                "\t\tadd_compile_definitions(_WINSOCK_DEPRECATED_NO_WARNINGS)"
            )
            cmakelists.write_text(content, encoding="utf-8")
            patches_applied += 1
            print("  Patched: CMakeLists.txt (added _WINSOCK_DEPRECATED_NO_WARNINGS)")

    print(f"  {patches_applied} file(s) patched")


def _patch_eipscanner_receive_port(eip_dir):
    """Add configurable receivePort to ConnectionParameters.

    By default EIPScanner binds the implicit I/O socket to port 2222.
    This patch adds a `receivePort` field so each ConnectionManager instance
    can listen on a different UDP port, enabling multiple bridges in parallel.
    """
    print("\nApplying receivePort patch...")
    patches_applied = 0

    # 1. Add receivePort field to ConnectionParameters.h
    params_h = eip_dir / "src" / "cip" / "connectionManager" / "ConnectionParameters.h"
    content = params_h.read_text(encoding="utf-8")
    marker = "std::vector<uint8_t> connectionPath = {};"
    if "receivePort" not in content:
        content = content.replace(
            marker,
            marker + "\n\t\tCipUint receivePort = 2222;  // UDP port for receiving T2O data"
        )
        params_h.write_text(content, encoding="utf-8")
        patches_applied += 1
        print("  Patched: ConnectionParameters.h (added receivePort)")

    # 2. Patch ConnectionManager.cpp
    cm_cpp = eip_dir / "src" / "ConnectionManager.cpp"
    content = cm_cpp.read_text(encoding="utf-8")

    # 2a. Use receivePort for the local bound socket instead of EIP_DEFAULT_IMPLICIT_PORT
    old_bind = "findOrCreateSocket(sockets::EndPoint(si->getRemoteEndPoint().getHost(), EIP_DEFAULT_IMPLICIT_PORT));"
    new_bind = "findOrCreateSocket(sockets::EndPoint(si->getRemoteEndPoint().getHost(), connectionParameters.receivePort));"
    if old_bind in content:
        content = content.replace(old_bind, new_bind)
        patches_applied += 1
        print("  Patched: ConnectionManager.cpp (use receivePort for bind)")

    # 2b. Include T2O_SOCKADDR_INFO in Forward Open request so the PLC sends
    #     T2O data to our receivePort instead of the default 2222
    old_fwd_open = (
        '\tMessageRouterResponse messageRouterResponse;\n'
        '\t\tif (isLarge) {\n'
        '\t\t\tLargeForwardOpenRequest request(connectionParameters);\n'
        '\t\t\tmessageRouterResponse = _messageRouter->sendRequest(si,\n'
        '\t\t\t\tstatic_cast<cip::CipUsint>(ConnectionManagerServiceCodes::LARGE_FORWARD_OPEN),\n'
        '\t\t\t\tEPath(6, 1), request.pack(), {});\n'
        '\t\t} else {\n'
        '\t\t\tForwardOpenRequest request(connectionParameters);\n'
        '\t\t\tmessageRouterResponse = _messageRouter->sendRequest(si,\n'
        '\t\t\t\tstatic_cast<cip::CipUsint>(ConnectionManagerServiceCodes::FORWARD_OPEN),\n'
        '\t\t\t\tEPath(6, 1), request.pack(), {});\n'
        '\t\t}'
    )
    new_fwd_open = (
        '\t// Build T2O sockaddr info so the target sends T2O data to our receivePort\n'
        '\t\tstd::vector<eip::CommonPacketItem> fwdOpenItems;\n'
        '\t\t{\n'
        '\t\t\tBuffer sockBuf;\n'
        '\t\t\tsockBuf << sockets::EndPoint("0.0.0.0", connectionParameters.receivePort);\n'
        '\t\t\tfwdOpenItems.emplace_back(eip::CommonPacketItemIds::T2O_SOCKADDR_INFO, sockBuf.data());\n'
        '\t\t}\n'
        '\n'
        '\t\tMessageRouterResponse messageRouterResponse;\n'
        '\t\tif (isLarge) {\n'
        '\t\t\tLargeForwardOpenRequest request(connectionParameters);\n'
        '\t\t\tmessageRouterResponse = _messageRouter->sendRequest(si,\n'
        '\t\t\t\tstatic_cast<cip::CipUsint>(ConnectionManagerServiceCodes::LARGE_FORWARD_OPEN),\n'
        '\t\t\t\tEPath(6, 1), request.pack(), fwdOpenItems);\n'
        '\t\t} else {\n'
        '\t\t\tForwardOpenRequest request(connectionParameters);\n'
        '\t\t\tmessageRouterResponse = _messageRouter->sendRequest(si,\n'
        '\t\t\t\tstatic_cast<cip::CipUsint>(ConnectionManagerServiceCodes::FORWARD_OPEN),\n'
        '\t\t\t\tEPath(6, 1), request.pack(), fwdOpenItems);\n'
        '\t\t}'
    )
    if old_fwd_open in content:
        content = content.replace(old_fwd_open, new_fwd_open)
        patches_applied += 1
        print("  Patched: ConnectionManager.cpp (T2O_SOCKADDR_INFO in Forward Open)")

    cm_cpp.write_text(content, encoding="utf-8")
    print(f"  {patches_applied} file(s) patched")


def build_eipscanner(cfg=None):
    """Build EIPScanner"""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Building EIPScanner")
    print("=" * 70)

    eip_dir = cfg.deps_dir / "EIPScanner"
    eip_build_dir = eip_dir / "build"

    # Pinned commit - this is the version our patches are tested against
    EIPSCANNER_COMMIT = "12c89a5"

    # Clone if not present
    if not eip_dir.exists():
        print(f"Cloning EIPScanner from GitHub (commit {EIPSCANNER_COMMIT})...")
        cfg.run_command([
            "git", "clone",
            "https://github.com/nimbuscontrols/EIPScanner.git",
            str(eip_dir)
        ])
        cfg.run_command([
            "git", "checkout", EIPSCANNER_COMMIT
        ], cwd=eip_dir)
    else:
        print("EIPScanner already exists, skipping clone")

    # Apply Windows patches if needed
    if IS_WINDOWS:
        _patch_eipscanner_for_windows(cfg, eip_dir)

    # Apply receivePort patch (all platforms)
    _patch_eipscanner_receive_port(eip_dir)

    # Build
    eip_build_dir.mkdir(exist_ok=True)

    cmake_args = [
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_SHARED_LIBS=ON",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
    ]

    if IS_WINDOWS:
        cmake_args.append("-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON")

    print("\nConfiguring EIPScanner with CMake...")
    cfg.run_command(cmake_args, cwd=eip_build_dir)

    print("\nBuilding EIPScanner...")
    cfg.cmake_build(eip_build_dir)

    # Copy libraries
    print("\nCopying EIPScanner libraries...")
    search_dirs = [eip_build_dir, eip_build_dir / "src"]
    copied = cfg.copy_shared_libs(search_dirs, "libEIPScanner" if IS_LINUX else "EIPScanner")

    if copied == 0:
        print("\n  No libraries found")
        print("Searching build directory:")
        for item in eip_build_dir.rglob("EIPScanner*" if IS_WINDOWS else "libEIPScanner*"):
            print(f"  Found: {item}")
        raise RuntimeError("No compiled EIPScanner libraries found")

    print(f"OK EIPScanner built - {copied} file(s) copied")


if __name__ == "__main__":
    try:
        build_eipscanner()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
