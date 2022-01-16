"""
Downloading images scrapped from the https://substance3d.adobe.com/assets/allassets
and saved in local SQLite file
"""
import os
import time
import sys

import platform

from os import path

import requests  # to get image from the web
import shutil  # to save it locally

from rich import pretty
from rich.console import Console
from rich.traceback import install
from rich.progress import track

from common_database_access import CommonDatabaseAccess

import f_icon

from pathlib import Path

console = Console()
pretty.install()
install()  # this is for tracing project activity
global_data = {"version": "Beta 1.1 (15.01.2022)\n"}


def clear_console():
    """Clears console view"""
    command = "clear"
    if os.name in ("nt", "dos"):  # If Machine is running on Windows, use cls
        command = "cls"
    os.system(command)


def download_image(url, file_path):
    if not path.exists(file_path):
        r = requests.get(url, stream=True)
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True
        # Open a local file with wb ( write binary ) permission.
        with open(file_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def append_date(filename):
    """adds date to the end of the filename

    :param str filename: filename
    :return:
    """
    p = Path(filename)
    return "{0}_{2}{1}".format(
        Path.joinpath(p.parent, p.stem), p.suffix, time.strftime("%Y%m%d-%H%M%S")
    )


def check_for_download(url, file_path, need_to_refresh):
    # console.print(url)
    if url:
        if os.path.exists(file_path) and need_to_refresh:
            os.rename(file_path, append_date(file_path))
        download_image(url, file_path)


def convert_to_nice_name(filename) -> str:
    """
    Replaces _ with spaces in filename
    :param str filename: filename to convert
    :return:
    """
    return filename.replace("_", " ")


def convert_to_ugly_name(filename) -> str:
    """
    Replaces space with _ in filename
    :param str filename: filename to convert
    :return:
    """
    return filename.replace(" ", "_")


def create_folder_for_type(database, asset_types):
    # 1. create _source folder for files to move to their location
    if not os.path.exists(
        global_data["local_path"] + os.sep + global_data["source_path"]
    ):
        os.makedirs(global_data["local_path"] + os.sep + global_data["source_path"])
    # 2. Now creating rest of the folders
    console.print("Creating folders ...")
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            os.makedirs(global_data["local_path"] + os.sep + a["name"])
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                os.makedirs(
                    global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
                )
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if not os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    os.makedirs(
                        global_data["local_path"]
                        + os.sep
                        + a["name"]
                        + os.sep
                        + c["name"]
                        + os.sep
                        + asset["name"]
                    )

    input("Press any enter to close...")


def create_folders(database):
    menu_title = " Select asset type to create folder"
    count = 1
    menu_items = []
    all_asset_types = database.get_all_asset_types()
    for asset_type in all_asset_types:
        menu_items.append(f"[{count}] {asset_type['name']}")
        count = count + 1
    menu_items.append(f"[{count}] All")
    count = count + 1
    menu_items.append(f"[{count}] Return")

    menu_exit = False
    while not menu_exit:
        # cls()
        clear_console()
        console.print("version " + global_data["version"])
        console.print(menu_title + "")
        for m_i in menu_items:
            console.print(m_i + "")
        console.print("")
        user_input = input("Enter a number: ")
        if user_input.isnumeric():
            menu_sel = int(user_input)
            if 1 <= menu_sel < count - 1:  # Specific asset type
                # categories = database.get_all_categories_by_asset_type_id(
                #     all_asset_types[menu_sel - 1]["id"]
                # )
                create_folder_for_type(database, [all_asset_types[menu_sel - 1]])
            elif menu_sel == count - 1:  # all asset types
                # categories = database.get_all_categories_by_id(14)
                # categories = database.get_all_categories()
                create_folder_for_type(database, all_asset_types)
            elif menu_sel == count:  # Quit
                menu_exit = True


def download_all_images(database):
    console.print("Downloading images ...")
    asset_types = database.get_all_asset_types()
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    local_path = (
                        global_data["local_path"]
                        + os.sep
                        + a["name"]
                        + os.sep
                        + c["name"]
                        + os.sep
                        + asset["name"]
                        + os.sep
                    )
                    # console.print(asset)
                    check_for_download(
                        asset["preview_image"],
                        local_path + "Preview.png",
                        asset["have_preview_image_changed"],
                    )
                    check_for_download(
                        asset["details_image"],
                        local_path + "Details.png",
                        asset["have_details_image_changed"],
                    )
                    check_for_download(
                        asset["variant_1_image"],
                        local_path + "Variant1.png",
                        asset["have_variant_1_image_changed"],
                    )
                    check_for_download(
                        asset["variant_2_image"],
                        local_path + "Variant2.png",
                        asset["have_variant_2_image_changed"],
                    )
                    check_for_download(
                        asset["variant_3_image"],
                        local_path + "Variant3.png",
                        asset["have_variant_3_image_changed"],
                    )
                    database.set_asset_art_as_updated(asset["id"])

    input("Press any enter to close...")


def make_all_icons(database, ignore_created=True):
    console.print("Creating folder icons ...")
    asset_types = database.get_all_asset_types()
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    local_path = (
                        global_data["local_path"]
                        + os.sep
                        + a["name"]
                        + os.sep
                        + c["name"]
                        + os.sep
                        + asset["name"]
                        + os.sep
                    )
                    # console.print(asset)
                    if platform.system() == "Windows":
                        if os.path.exists(local_path + "Preview.png") and (
                            not os.path.exists(local_path + "Preview.ico")
                            or ignore_created
                        ):
                            f_icon.create_icon(local_path + "Preview.png")
                    else:
                        if os.path.exists(local_path + "Preview.png"):
                            f_icon.create_icon(local_path + "Preview.png")

    input("Press any enter to close...")


def transfer_all_local_files(database):
    console.print("Placing files in corresponding folders ...")
    files = os.listdir(global_data["local_path"] + os.sep + global_data["source_path"])
    asset_types = database.get_all_asset_types()
    placement_log = {"moved": [], "existing": [], "missing": [], "existing_full": []}
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    for (
                        f
                    ) in (
                        files
                    ):  # going over all files in the _source folder that we know from the start
                        if os.path.exists(  # checking, that file is still there. can be moved already
                            global_data["local_path"]
                            + os.sep
                            + global_data["source_path"]
                            + os.sep
                            + f
                        ):
                            if not os.path.exists(  # checking, that this file already exists at destination.
                                global_data[
                                    "local_path"
                                ]  # if it is, then we have a double
                                + os.sep
                                + a["name"]
                                + os.sep
                                + c["name"]
                                + os.sep
                                + asset["name"]
                                + os.sep
                                + f
                            ):
                                if (
                                    f.lower().endswith(".jpg")
                                    and convert_to_nice_name(f.lower()).find(
                                        asset["name"].lower()
                                    )
                                    >= 0
                                ):
                                    # if it is jpeg, then extra case. We check if asset name is inside file name
                                    os.rename(
                                        global_data["local_path"]
                                        + os.sep
                                        + global_data["source_path"]
                                        + os.sep
                                        + f,
                                        global_data["local_path"]
                                        + os.sep
                                        + a["name"]
                                        + os.sep
                                        + c["name"]
                                        + os.sep
                                        + asset["name"]
                                        + os.sep
                                        + f,
                                    )
                                    placement_log["moved"].append(
                                        global_data["local_path"]
                                        + os.sep
                                        + a["name"]
                                        + os.sep
                                        + c["name"]
                                        + os.sep
                                        + asset["name"]
                                        + os.sep
                                        + f
                                    )
                                elif not f.lower().endswith(
                                    ".jpg"
                                ):  # if this is not a jpg, then we check name
                                    # without extension to match with asset name
                                    file_details = os.path.splitext(f)
                                    if (
                                        convert_to_nice_name(file_details[0].lower())
                                        == asset["name"].lower()
                                    ):
                                        os.rename(
                                            global_data["local_path"]
                                            + os.sep
                                            + global_data["source_path"]
                                            + os.sep
                                            + f,
                                            global_data["local_path"]
                                            + os.sep
                                            + a["name"]
                                            + os.sep
                                            + c["name"]
                                            + os.sep
                                            + asset["name"]
                                            + os.sep
                                            + f,
                                        )
                                        placement_log["moved"].append(
                                            global_data["local_path"]
                                            + os.sep
                                            + a["name"]
                                            + os.sep
                                            + c["name"]
                                            + os.sep
                                            + asset["name"]
                                            + os.sep
                                            + f
                                        )
                            else:  # we had a double name, so mark it as double
                                placement_log["existing_full"].append(
                                    global_data["local_path"]
                                    + os.sep
                                    + a["name"]
                                    + os.sep
                                    + c["name"]
                                    + os.sep
                                    + asset["name"]
                                    + os.sep
                                    + f
                                )
                                placement_log["existing"].append(f)
    # generating report
    files = os.listdir(global_data["local_path"] + os.sep + global_data["source_path"])
    placement_log["missing"] = list(set(files) - set(placement_log["existing"]))
    file = open(
        append_date(global_data["local_path"] + os.sep + "FileTransferReport.txt"),
        "w",
        encoding="utf-8",
    )
    file.write(f'Moved files({len(placement_log["moved"])}): \n')
    file.write("\n")
    for f in placement_log["moved"]:
        file.write(f + "\n")
    file.write("\n")
    file.write(f'Existed files({len(placement_log["existing_full"])}): \n')
    file.write("\n")
    for f in placement_log["existing_full"]:
        file.write(f + "\n")
    file.write("\n")
    file.write(f'Missing locations for files({len(placement_log["missing"])}): \n')
    file.write("\n")
    for f in placement_log["missing"]:
        file.write(f + "\n")
    file.close()
    input("Press any enter to close...")


def generate_report(database):
    console.print("Generating report ...")
    asset_types = database.get_all_asset_types()
    placement_log = {"have": [], "missing": [], "need": []}
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    local_path = (
                        global_data["local_path"]
                        + os.sep
                        + a["name"]
                        + os.sep
                        + c["name"]
                        + os.sep
                        + asset["name"]
                        + os.sep
                    )
                    count = 0
                    have = 0
                    missing = ""
                    if asset["format_sbsar"]:
                        count = count + 1
                        if asset["have_format_sbsar"]:
                            have = have + 1
                        else:
                            missing = missing + "sbsar "
                        changed_record = True
                    if asset["format_sbs"]:
                        count = count + 1
                        if asset["have_format_sbs"]:
                            have = have + 1
                        else:
                            missing = missing + "sbs "
                    if asset["format_exr"]:
                        count = count + 1
                        if asset["have_format_exr"]:
                            have = have + 1
                        else:
                            missing = missing + "exr "
                    if asset["format_fbx"]:
                        count = count + 1
                        if asset["have_format_fbx"]:
                            have = have + 1
                        else:
                            missing = missing + "fbx "
                    if asset["format_glb"]:
                        count = count + 1
                        if asset["have_format_glb"]:
                            have = have + 1
                        else:
                            missing = missing + "glb "
                    if asset["format_mdl"]:
                        count = count + 1
                        if asset["have_format_mdl"]:
                            have = have + 1
                        else:
                            missing = missing + "mdl "
                    if count == have:
                        placement_log["have"].append(
                            a["name"] + " > " + c["name"] + " > " + asset["name"]
                        )
                    elif count != have and have > 0:
                        placement_log["missing"].append(
                            a["name"]
                            + " > "
                            + c["name"]
                            + " > "
                            + asset["name"]
                            + " : missing formats "
                            + missing
                        )
                    else:
                        placement_log["need"].append(
                            a["name"] + " > " + c["name"] + " > " + asset["name"]
                        )
    file = open(
        append_date(global_data["local_path"] + os.sep + "AssetCountReport.txt"),
        "w",
        encoding="utf-8",
    )
    file.write(f'Have assets({len(placement_log["have"])}): \n')
    file.write("\n")
    for f in placement_log["have"]:
        file.write(f + "\n")
    file.write("\n")
    file.write(f'Missing assets({len(placement_log["missing"])}): \n')
    file.write("\n")
    for f in placement_log["missing"]:
        file.write(f + "\n")
    file.write("\n")
    file.write(f'Needed assets({len(placement_log["need"])}): \n')
    file.write("\n")
    for f in placement_log["need"]:
        file.write(f + "\n")
    file.close()
    input("Press any enter to close...")


def mark_database_with_my_files(database):
    console.print("Checking local files for the database ...")
    asset_types = database.get_all_asset_types()
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
            continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])
            if not os.path.exists(
                global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            ):
                continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                if os.path.exists(
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                ):
                    local_path = (
                        global_data["local_path"]
                        + os.sep
                        + a["name"]
                        + os.sep
                        + c["name"]
                        + os.sep
                        + asset["name"]
                        + os.sep
                    )
                    all_files = []
                    for lp, currentDirectory, files in os.walk(local_path):
                        all_files.extend(files)
                    changed_record = False
                    for file in all_files:
                        if file.lower().endswith(".sbsar") and asset["format_sbsar"]:
                            asset["have_format_sbsar"] = True
                            changed_record = True
                        if file.lower().endswith(".sbs") and asset["format_sbs"]:
                            asset["have_format_sbs"] = True
                            changed_record = True
                        if file.lower().endswith(".exr") and asset["format_exr"]:
                            asset["have_format_exr"] = True
                            changed_record = True
                        if file.lower().endswith(".fbx") and asset["format_fbx"]:
                            asset["have_format_fbx"] = True
                            changed_record = True
                        if file.lower().endswith(".glb") and asset["format_glb"]:
                            asset["have_format_glb"] = True
                            changed_record = True
                        if file.lower().endswith(".mdl") and asset["format_mdl"]:
                            asset["have_format_mdl"] = True
                            changed_record = True
                    if changed_record:
                        database.update_asset(asset)

    input("Press any enter to close...")


def fancy_list_generation(database):
    console.print("Generating request list ...")
    fancy_requests = []
    if os.path.exists(global_data["local_path"] + os.sep + "Requests.txt"):
        with open(global_data["local_path"] + os.sep + "Requests.txt") as f:
            base_requests = f.read().splitlines()
        for base_r in track(
            base_requests, description="Requests.", total=len(base_requests)
        ):
            asset = database.get_asset_by_name(base_r)
            if len(asset) > 0:
                asset_format = ""
                if asset[0]["format_sbsar"]:
                    asset_format = asset_format + "sbsar "
                if asset[0]["format_sbs"]:
                    asset_format = asset_format + "sbs "
                if asset[0]["format_exr"]:
                    asset_format = asset_format + "exr "
                if asset[0]["format_fbx"]:
                    asset_format = asset_format + "cbx "
                if asset[0]["format_glb"]:
                    asset_format = asset_format + "glb "
                if asset[0]["format_mdl"]:
                    asset_format = asset_format + "mdl "
                fancy_requests.append(
                    asset[0]["name"]
                    + " - "
                    + asset_format.strip()
                    + " - "
                    + asset[0]["url"]
                )
    if len(fancy_requests) > 0:
        file = open(
            append_date(global_data["local_path"] + os.sep + "Result.txt"),
            "w",
            encoding="utf-8",
        )
        for f in fancy_requests:
            file.write(f + "\n")
        file.close()
    input("Press any enter to close...")


def move_folders_to_new_category(database):
    """
    Checks if asset folder do not exist at category location, then looks in every category
    for the asset to relocate to the proper location
    :param CommonDatabaseAccess database: reference to the database
    """
    console.print("Generating report ...")
    asset_types = database.get_all_asset_types()
    all_categories = database.get_all_categories()
    log = []
    for a in asset_types:  # track(asset_types, description="Types."):
        categories = database.get_all_categories_by_asset_type_id(a["id"])
        # if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
        #     continue
        for c in categories:  # track(categories, description="Categories."):
            assets = database.get_all_assets_by_category(c["id"])

            # if not os.path.exists(
            #     global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
            # ):
            #     continue
            console.print(f"{a['name']} - {c['name']}")
            for asset in track(assets, description="Assets.", total=len(assets)):
                expected_path = (
                    global_data["local_path"]
                    + os.sep
                    + a["name"]
                    + os.sep
                    + c["name"]
                    + os.sep
                    + asset["name"]
                )
                if not os.path.exists(expected_path):
                    # we did not find our asset in the right place, so we check everywhere
                    found = False
                    for a1 in asset_types:
                        for c1 in all_categories:
                            checked_path = (
                                global_data["local_path"]
                                + os.sep
                                + a1["name"]
                                + os.sep
                                + c1["name"]
                                + os.sep
                                + asset["name"]
                            )
                            if checked_path != expected_path and os.path.exists(
                                checked_path
                            ):
                                log.append(checked_path + " >> " + expected_path)
                                if not os.path.exists(global_data["local_path"] + os.sep + a["name"]):
                                    os.makedirs(global_data["local_path"] + os.sep + a["name"])
                                if not os.path.exists(
                                        global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
                                ):
                                    os.makedirs(
                                        global_data["local_path"] + os.sep + a["name"] + os.sep + c["name"]
                                    )

                                os.rename(checked_path, expected_path)
                                found = True
                                break
                        if found:
                            break
    console.print("Moved Assets - " + str(len(log)))
    console.print()
    console.print("All Done !!!")
    if len(log) > 0:
        file = open(
            append_date(
                global_data["local_path"] + os.sep + "AssetCategoryChangeLog.txt"
            ),
            "w",
            encoding="utf-8",
        )
        for f in log:
            file.write(f + "\n")
        file.close()
    input("Press any enter to close...")


def main_menu(database):
    """
    Draw main menu
    :param CommonDatabaseAccess database: reference to the database
    :return:
    """
    menu_title = " Select action"
    menu_items = [
        "[1] Create folders.",
        "[2] Download all images.",
        "[3] Make all icons. Where Preview.ico do not exist.",
        "[4] Make all icons, but ignore where Preview.ico exists.",
        "[5] Transfer all local files from _source folder to appropriate folders.",
        "[6] Generate report. (Do this after Marking database with my files).",
        "[7] Mark database with my files. (Do this before Generating report).",
        "[8] Fancy list generation. (Convert simple material list to list with format and links, looks for Requests.txt).",
        "[9] Move folders if Category changed.",
        "[10] Quit.",
    ]
    menu_exit = False
    while not menu_exit:
        clear_console()
        console.print("version " + global_data["version"])
        console.print(menu_title + "")
        for m_i in menu_items:
            console.print(m_i + "")
        console.print("")
        user_input = input("Enter a number: ")
        if user_input.isnumeric():
            menu_sel = int(user_input)
            if menu_sel == 1:  # Create folders
                create_folders(database)
            if menu_sel == 2:  # Download all images
                download_all_images(database)
            if menu_sel == 3:  # Make all icons
                make_all_icons(database, False)
            if menu_sel == 4:  # Make all icons
                make_all_icons(database)
            if menu_sel == 5:  # Transfer all local files
                transfer_all_local_files(database)
            if menu_sel == 6:  # Generate report
                generate_report(database)
            if menu_sel == 7:  # Mark database with my files
                mark_database_with_my_files(database)
            if menu_sel == 8:  # Fancy list generation
                fancy_list_generation(database)
            if menu_sel == 9:  # Move folders to new category
                move_folders_to_new_category(database)
            if menu_sel == 10:  # Quit
                menu_exit = True


def main():
    """
    Check location of the database and then going to main menu
    :return:
    """
    menu_title = " Select database file"
    menu_items = []
    menu_items_count = 0
    menu_items_references = []
    local_path = os.path.dirname(sys.argv[0])
    global_data["local_path"] = local_path
    global_data["source_path"] = "_source"
    files = os.listdir(local_path)
    for f in files:
        file_details = os.path.splitext(f)
        if os.path.isfile(local_path + os.sep + f) and file_details[1] == ".db":
            menu_items.append(f"[{menu_items_count + 1}] {f}")
            menu_items_count = menu_items_count + 1
            menu_items_references.append(f)
    if menu_items_count == 0:
        clear_console()
        console.print("Database files not found next to the application files.")
        input("Press any enter to close...")
    elif menu_items_count == 1:
        database = CommonDatabaseAccess(
            db_path=local_path + os.sep + menu_items_references[0], force=False
        )
        main_menu(database)
    else:
        menu_exit = False
        while not menu_exit:
            clear_console()
            console.print("version " + global_data["version"])
            console.print(menu_title + "")
            for m_i in menu_items:
                console.print(m_i + "")
            console.print("")
            user_input = input("Enter a number: ")
            if user_input.isnumeric():
                menu_sel = int(user_input)
                if 0 < menu_sel <= len(menu_items_references):  # Initial scan
                    database = CommonDatabaseAccess(
                        db_path=local_path
                        + os.sep
                        + menu_items_references[menu_sel - 1],
                        force=False,
                    )
                    main_menu(database)
                    menu_exit = True


if __name__ == "__main__":
    main()
