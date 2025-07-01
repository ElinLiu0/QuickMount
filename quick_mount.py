#  Author:Elin
#  Create Time:2025-07-01 10:46:31
#  Last Modified By:ChatGPT
#  Update Time:2025-07-01 12:10:00
#  Description: A script to mount/unmount all removable drives from Windows NT to WSL, prompting for sudo password once only per run.

import psutil
import subprocess
import argparse
import os
import getpass
from typing import List, Optional


def ListAllRemovableDrivers() -> List[str]:
    """
    List all removable drive letters under Windows NTFS.
    Returns:
        List[str]: A list of removable drive letters (e.g., ['D:', 'E:', 'F:']).
    """
    RemovableDrivers: List[str] = []
    for part in psutil.disk_partitions():
        if "removable" in part.opts.lower():
            RemovableDrivers.append(part.device.upper()[:2])
    return RemovableDrivers


def run_sudo_wsl(cmd_str: str, password: str, distro: Optional[str] = None) -> None:
    """
    Run a string of commands under one sudo invocation in WSL, passing the password via stdin.
    """
    base = ['wsl']
    if distro:
        base += ['-d', distro]
    # Use shell to chain commands
    base += ['sudo', '-S', 'sh', '-c', cmd_str]
    proc = subprocess.Popen(base, stdin=subprocess.PIPE, text=True)
    proc.communicate(password + '\n')
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, base)


def MountAll(WSLDistroName: Optional[str] = None) -> None:
    RemovableDrivers = ListAllRemovableDrivers()
    if not RemovableDrivers:
        print("No removable drives found.")
        return

    password = getpass.getpass("Enter sudo password for WSL: ")

    for drv in RemovableDrivers:
        letter = drv[0].lower()
        mount_point = f"/mnt/{letter}"
        cmd = f"mkdir -p {mount_point} && mount -t drvfs {drv} {mount_point}"
        print(f"Mounting {drv} at {mount_point}")
        try:
            run_sudo_wsl(cmd, password, WSLDistroName)
            print(f"\nMounted {drv} -> {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"\nError mounting {drv}: {e}")
            os._exit(1)


def UnmountAll(WSLDistroName: Optional[str] = None) -> None:
    RemovableDrivers = ListAllRemovableDrivers()
    if not RemovableDrivers:
        print("No removable drives found.")
        return

    password = getpass.getpass("Enter sudo password for WSL: ")

    for drv in RemovableDrivers:
        letter = drv[0].lower()
        mount_point = f"/mnt/{letter}"
        cmd = f"umount {mount_point} && rm -rf {mount_point}"
        print(f"Unmounting {drv} from {mount_point}")
        try:
            run_sudo_wsl(cmd, password, WSLDistroName)
            print(f"\nUnmounted {drv} from {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"\nError unmounting {drv}: {e}")
            os._exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mount/unmount all removable drives to WSL.")
    parser.add_argument('-d', '--distro', type=str, help="WSL distro name.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-m', '--mount', action='store_true', help="Mount drives.")
    group.add_argument('-u', '--unmount', action='store_true', help="Unmount drives.")
    args = parser.parse_args()

    if args.mount:
        MountAll(args.distro)
    else:
        UnmountAll(args.distro)
