"""Scraping https://substance3d.adobe.com/assets/allassets for all offered asset links and images"""
import os
import time
import sys

import datetime
import argparse

from os import path

from rich import pretty
from rich.console import Console
from rich.traceback import install
from rich.progress import track

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

from selenium.common.exceptions import StaleElementReferenceException

from common_database_access import CommonDatabaseAccess

console = Console()
pretty.install()
install()  # this is for tracing project activity
global_data = {"version": "Beta 1.1 (06.12.2021)\n"}


def clear_console():
    """Clears console view"""
    command = "clear"
    if os.name in ("nt", "dos"):  # If Machine is running on Windows, use cls
        command = "cls"
    os.system(command)


def page_scrolling_down(driver) -> None:
    """
    Scrolling down whole page to load all elements
    """
    scrolling_params = {
        "last_height": driver.execute_script("return document.body.scrollHeight"),
        "current_pos": 0,
        "new_height": 0,
    }
    while True:
        while scrolling_params["current_pos"] < scrolling_params["last_height"]:
            driver.execute_script(
                "window.scrollTo(0, arguments[0]);",
                scrolling_params["current_pos"],
            )
            time.sleep(0.2)
            scrolling_params["current_pos"] += 200

        scrolling_params["new_height"] = driver.execute_script(
            "return document.body.scrollHeight"
        )
        if scrolling_params["new_height"] == scrolling_params["last_height"]:
            break
        scrolling_params["last_height"] = scrolling_params["new_height"]


def initial_asset_type_and_category_scan(database, debug):
    """Initial scan of the https://substance3d.adobe.com/assets/allassets
    to save information about asset type and categorries in the sqlite database"""

    # database = CommonDatabaseAccess(db_path=db_path, force=True)

    s = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(executable_path=s.path, options=options)

    url = "https://substance3d.adobe.com/assets/allassets"

    driver.get(url)
    time.sleep(2)
    # waiting to load cookie popup and dismissing it
    try:
        tabs = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        tabs.click()
    except NoSuchElementException:
        print("no popup found")

    time.sleep(1)
    tabs = driver.find_elements(By.TAG_NAME, "a")

    new_elements_count = 0  # amount of new elements during scraping

    # first find 2 main class names, that are always changing.
    look_up_class = {
        "asset_type_class": "",
        "category_class": "",
        "asset_type_class_reference": "/assets/allassets?assetType=substanceMaterial",
        "category_class_reference": "/assets/allassets?assetType=substanceMaterial&category",
    }

    for tab in tabs:
        category_parameter = {
            "category": "",
            "category_url": "",
            "category_id": 0,
            "asset_type_name": "",
            "asset_type_id": 0,
            "asset_type_records": [],
            "category_records": [],
        }
        if look_up_class["asset_type_class"] == "" and look_up_class[
            "asset_type_class_reference"
        ] in tab.get_attribute("href"):
            look_up_class["asset_type_class"] = tab.get_attribute("class")

        if (
            look_up_class["asset_type_class"] != ""
            and tab.get_attribute("class") == look_up_class["asset_type_class"]
        ):
            category_parameter["asset_type_name"] = tab.text.split("\n", 1)[0]
            tab_link = tab.get_attribute("href")

            category_parameter["asset_type_records"] = database.get_asset_type_by_name(
                category_parameter["asset_type_name"]
            )
            if len(category_parameter["asset_type_records"]) == 0:
                category_parameter["asset_type_id"] = database.set_new_asset_type(
                    category_parameter["asset_type_name"], tab_link
                )
            else:
                category_parameter["asset_type_id"] = category_parameter[
                    "asset_type_records"
                ][0]["id"]

            for sub_tab in tabs:
                if look_up_class["category_class"] == "" and look_up_class[
                    "category_class_reference"
                ] in sub_tab.get_attribute("href"):
                    look_up_class["category_class"] = sub_tab.get_attribute("class")
                if (
                    look_up_class["category_class"] != ""
                    and sub_tab.get_attribute("class")
                    == look_up_class["category_class"]
                    and sub_tab.get_attribute("href").startswith(tab_link)
                ):

                    category_parameter["category"] = sub_tab.text.split("\n", 1)[0]
                    category_parameter["category_url"] = sub_tab.get_attribute("href")
                    if debug:
                        console.print(category_parameter["category"])

                    category_parameter[
                        "category_records"
                    ] = database.get_category_by_name_and_asset_type_id(
                        category_parameter["category"],
                        category_parameter["asset_type_id"],
                    )
                    if len(category_parameter["category_records"]) == 0:
                        new_elements_count = new_elements_count + 1
                        category_parameter["category_id"] = database.set_new_category(
                            category_parameter["category"],
                            category_parameter["category_url"],
                            category_parameter["asset_type_id"],
                        )

    console.print()
    if debug:
        console.print("Found Asset Type" + look_up_class["asset_type_class"])
        console.print("Found Category " + look_up_class["category_class"])
        console.print()
    console.print("New categories - " + str(new_elements_count))
    console.print()
    console.print("All Done !!!")
    input("Press Enter to continue...")
    driver.close()


def draw_asset_type_list_menu(database, debug):
    """Draws menu to select what asset type to check for new assets"""
    menu_title = " Select asset type to check"
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
                categories = database.get_all_categories_by_asset_type_id(
                    all_asset_types[menu_sel - 1]["id"]
                )
                asset_scan_by_asset_type(database, debug, categories)
            elif menu_sel == count - 1:  # all asset types
                # categories = database.get_all_categories_by_id(14)
                categories = database.get_all_categories()
                asset_scan_by_asset_type(database, debug, categories)
            elif menu_sel == count:  # Quit
                menu_exit = True


def get_asset_name_and_format_from_string(title_text) -> []:
    """Checks input string for name and format

    :param [] title_text: input string formatted by lines
    :return: [name, asset_format]
    """
    if (
        title_text[0].lower() == "NEW".lower()
        and title_text[1].lower() == "FREE".lower()
    ) or (
        title_text[0].lower() == "UPDATED".lower()
        and title_text[1].lower() == "FREE".lower()
    ):
        name = title_text[2]
        asset_format = title_text[3]
    elif (
        title_text[0].lower() == "NEW".lower()
        or title_text[0].lower() == "FREE".lower()
        or title_text[0].lower() == "UPDATED".lower()
    ):
        name = title_text[1]
        asset_format = title_text[2]
    else:
        name = title_text[0]
        asset_format = title_text[1]

    return [name, asset_format.split(" ")]


def single_category_asset_scan(input_value, driver, database, cat, debug) -> None:
    """Process one category of the assets

    :param {} input_value: {
        "new_elements_count": 0,
        "updated_elements_count": 0,
        "asset_class": "",
        "utc_timestamp": utc_timestamp,
    }
    :param driver: reference to the Chrome driver
    :param database: reference to the common_database_access.py
    :param [] cat: category data from SQLite database
    :param bool debug: show debug info
    """
    driver.get(cat["url"])
    time.sleep(1)
    page_scrolling_down(driver)

    # checking actual elements
    elements = driver.find_elements(By.TAG_NAME, "div")
    for element in elements:
        if input_value[
            "asset_class"
        ] == "" and "source-asset-thumbnail" in element.get_attribute("class"):
            input_value["asset_class"] = element.get_attribute("class")

        if (
            input_value["asset_class"] != ""
            and element.get_attribute("class") == input_value["asset_class"]
        ):

            _a = element.find_element(By.TAG_NAME, "a")
            href = _a.get_attribute("href")
            img = element.find_element(By.TAG_NAME, "img")
            image = img.get_attribute("src").split("?", 1)[0]
            title_text = element.text.split("\n")
            need_update = title_text[0].lower() == "UPDATED".lower()

            checked_name = get_asset_name_and_format_from_string(title_text)

            if image.startswith("https://"):
                if debug:
                    console.print(checked_name[0])
                ast = database.get_asset_by_url(href)
                if len(ast) == 0:  # element not found, need to add
                    input_value["new_elements_count"] = (
                        input_value["new_elements_count"] + 1
                    )
                    database.set_new_asset(
                        {
                            "name": checked_name[0],
                            "url": href,
                            "category": cat["id"],
                            "preview_image": image,
                            "details_image": "",
                            "variant_1_image": "",
                            "variant_2_image": "",
                            "variant_3_image": "",
                            "have_preview_image_changed": False,
                            "have_details_image_changed": False,
                            "have_variant_1_image_changed": False,
                            "have_variant_2_image_changed": False,
                            "have_variant_3_image_changed": False,
                            "last_change_date": input_value["utc_timestamp"],
                            "need_to_check": True,
                            "format_sbsar": "SBSAR" in checked_name[1],
                            "format_sbs": "SBS" in checked_name[1],
                            "format_exr": "EXR" in checked_name[1],
                            "format_fbx": "FBX" in checked_name[1],
                            "format_glb": "GLB" in checked_name[1],
                            "format_mdl": "MDL" in checked_name[1],
                            "have_format_sbsar": False,
                            "have_format_sbs": False,
                            "have_format_exr": False,
                            "have_format_fbx": False,
                            "have_format_glb": False,
                            "have_format_mdl": False,
                        }
                    )
                else:  # checking by url, since can have duplicate names
                    if (
                        ast[0]["preview_image"] != image
                        or need_update
                        or ast[0]["name"] != checked_name[0]
                    ):
                        input_value["updated_elements_count"] = (
                            input_value["updated_elements_count"] + 1
                        )
                        ast[0]["name"] = checked_name[0]
                        ast[0]["preview_image"] = image
                        ast[0]["have_preview_image_changed"] = True
                        ast[0]["last_change_date"] = input_value["utc_timestamp"]
                        ast[0]["need_to_check"] = True
                        ast[0]["format_sbsar"] = "SBSAR" in checked_name[1]
                        ast[0]["format_sbs"] = "SBS" in checked_name[1]
                        ast[0]["format_exr"] = "EXR" in checked_name[1]
                        ast[0]["format_fbx"] = "FBX" in checked_name[1]
                        ast[0]["format_glb"] = "GLB" in checked_name[1]
                        ast[0]["format_mdl"] = "MDL" in checked_name[1]
                        database.update_asset(ast[0])


def asset_scan_by_asset_type(database, debug, categories):
    """Initial scan of the https://substance3d.adobe.com/assets/allassets
    to save information about asset in the sqlite database"""

    # database = CommonDatabaseAccess(db_path=db_path, force=True)
    s = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(executable_path=s.path, options=options)

    url = "https://substance3d.adobe.com/assets/allassets"

    driver.get(url)
    time.sleep(2)
    # waiting to load cookie popup and dismissing it
    try:
        tabs = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        tabs.click()
    except NoSuchElementException:
        print("no popup found")

    utc_timestamp = datetime.datetime.utcnow()
    input_value = {
        "new_elements_count": 0,
        "updated_elements_count": 0,
        "asset_class": "",
        "utc_timestamp": utc_timestamp,
    }
    for cat in categories:
        try:  # sub element class name, like Ceramics

            single_category_asset_scan(input_value, driver, database, cat, debug)

        except StaleElementReferenceException:
            console.print("Exited with Errors !!!")
            break

    console.print("New elements - " + str(input_value["new_elements_count"]))
    console.print("Updated elements - " + str(input_value["updated_elements_count"]))
    console.print()
    console.print("All Done !!!")
    input("Press Enter to continue...")
    driver.close()


def detailed_scan(database):
    """Detailed scan of all not previously not checked assets
    to get references to the variant images"""
    # database = CommonDatabaseAccess(db_path=db_path, force=True)

    s = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(executable_path=s.path, options=options)
    # driver.maximize_window()

    url = "https://substance3d.adobe.com/assets/allassets"

    driver.get(url)
    time.sleep(2)
    # waiting to load cookie popup and dismissing it
    try:
        popup = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        popup.click()
    except NoSuchElementException:
        print("no popup found")

    time.sleep(1)
    utc_timestamp = datetime.datetime.utcnow()
    for asset in track(
        list(database.get_all_assets_for_check()),
        description="Assets that need to be checked",
    ):
        driver.get(asset["url"])
        time.sleep(10)
        view = driver.find_element(By.CLASS_NAME, "view")
        divs = view.find_elements(By.TAG_NAME, "div")
        variant_id = 1
        found_details_image = False
        for div in divs:
            css = div.value_of_css_property("background-image")
            if css == "none":
                continue
            link = css.split("?", 1)[0].split('"', 1)[1]
            if (
                link == asset["preview_image"]
            ):  # we don't need preview image, we already have it
                continue
            if "sixteen-by-nine" in div.get_attribute("class"):
                if asset["details_image"] != link and not found_details_image:
                    found_details_image = True
                    if asset["details_image"] != "":
                        asset["have_details_image_changed"] = True
                    asset["details_image"] = link
            else:
                if (
                    f"variant_{variant_id}_image" in asset
                    and asset[f"variant_{variant_id}_image"] != link
                ):
                    if asset[f"variant_{variant_id}_image"] != "":
                        asset[f"have_variant_{variant_id}_image_changed"] = True
                    asset[f"variant_{variant_id}_image"] = link
                variant_id = variant_id + 1
            asset["last_change_date"] = utc_timestamp
            asset["need_to_check"] = False
            database.update_asset(asset)

    console.print()
    console.print("All Done !!!")
    input("Press Enter to continue...")
    driver.close()


def check_asset_count(database):
    """Writes list of all asset types and categories and asset amount in them"""
    # database = CommonDatabaseAccess(db_path=db_path, force=True)
    console.print(database.prepare_asset_type_and_category_dictionary())

    console.print()
    console.print("All Done !!!")
    input("Press Enter to continue...")


def main():
    """Main menu to select desired activity
    Initial scan - checks  https://substance3d.adobe.com/assets/allassets for all assets present
    Detailed scan - opens each individual asset page to get links to variation images"""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--database",
        default="all_assets.db",
        help="Path to the SQLite file. (Default is %(default)s",
    )
    # parser.add_argument(
    #     "-c",
    #     "--chrome-driver",
    #     default=r"C:\going_headless\chromedriver.exe",
    #     help="Path to the chrome driver file. (Default is %(default)s",
    # )
    parser.add_argument(
        "--debug", action="store_true", help="Display extra information while working."
    )
    args = parser.parse_args()

    # if not path.exists(args.chrome_driver):
    #     console.print("Chromedriver file not found at " + args.chrome_driver + " !!!")
    #     input("Press Enter to exit...")
    #     sys.exit(0)

    database = CommonDatabaseAccess(db_path=args.database, force=True)

    menu_title = " Select action"
    menu_items = [
        "[1] Initial Asset Type and Category scan",
        "[2] Asset scan by Asset type",
        "[3] Detailed scan",
        "[4] Check Asset count",
        "[5] Quit",
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
            if menu_sel == 1:  # Initial scan
                initial_asset_type_and_category_scan(database, args.debug)
            elif menu_sel == 2:  # Asset scan by Asset type
                draw_asset_type_list_menu(database, args.debug)
            elif menu_sel == 3:  # Detailed scan
                detailed_scan(database)
            elif menu_sel == 4:  # Check asset count
                check_asset_count(database)
            elif menu_sel == 5:  # Quit
                menu_exit = True


if __name__ == "__main__":
    main()
