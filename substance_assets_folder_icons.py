import os
import sys

import platform

from rich import pretty
from rich.console import Console
from rich.traceback import install
from rich.progress import track

import f_icon

console = Console()
pretty.install()
install()  # this is for tracing project activity
global_data = {"version": "Beta 1 (22.01.2022)\n"}


def _find_previews(root_path: str, result: []) -> []:
    """
    Recursevly go through root folder to find all path, that have Preview.png in them
    :param str root_path: initial look path
    :param [] result: list of paths, that have Preview.png in them
    :[] return: input result with added new paths
    """
    for root, directories, files in os.walk(root_path):
        for name in files:
            if name == "Preview.png":
                full_path = root  # os.path.join(root, name)
                if full_path not in result:
                    result.append(full_path)
                # break
    return result


def make_all_icons(ignore_created=True):
    """
    Creates icons for the folders containing Preview.png from set Preview.png
    :param bool ignore_created: ignore locations, that already have Preview.ico files
    """
    console.print("Creating folder icons ...")
    paths = []
    paths = _find_previews(os.path.dirname(sys.argv[0]), paths)
    # console.print(len(paths))
    for asset in track(paths, description="Assets.", total=len(paths)):
        if os.path.exists(os.path.join(asset, "Preview.png")):
            local_path = asset + os.sep
            # console.print(asset)
            if platform.system() == "Windows":
                if os.path.exists(local_path + "Preview.png") and (
                    not os.path.exists(local_path + "Preview.ico") or ignore_created
                ):
                    f_icon.create_icon(local_path + "Preview.png")
            else:
                if os.path.exists(local_path + "Preview.png"):
                    f_icon.create_icon(local_path + "Preview.png")

    input("Press any enter to close...")


if __name__ == "__main__":
    console.print("version " + global_data["version"])
    make_all_icons()
