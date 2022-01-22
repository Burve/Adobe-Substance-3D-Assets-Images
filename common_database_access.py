"""Access to SQLite database class"""
import sqlite3

from os import path
from sqlite3 import Error
from rich.pretty import pprint


class DatabaseFileDoesNotExist(Exception):
    """Raised when the input value is too small

    Attributes:
        message -- explanation of the error"""

    def __init__(self, db_path, message="Database file '{}' does not exist !!!"):
        self.path = db_path
        self.message = message
        super().__init__(message.format(db_path))


class CommonDatabaseAccess:
    """Class to access SQLite database"""

    def __init__(self, db_path, force):
        """
        Checking if we have our db file
        :param str db_path: path to the database file
        :param bool force: if database file do not exist and force is True, it will be created
        """

        self.conn = None
        if not path.exists(db_path):
            if force:
                self.connect_to_database(db_path)
                self.create_database()
            else:
                raise DatabaseFileDoesNotExist(db_path)
        else:
            self.connect_to_database(db_path)

    def __del__(self) -> None:
        """ "Need to close database connection when we are fully done"""
        if self.conn:
            self.conn.close()

    def connect_to_database(self, db_path) -> None:
        """Creates connection to the database"""
        try:
            self.conn = sqlite3.connect(
                db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
        except Error as _e:
            pprint(_e)
        # finally:
        #     if self.conn:
        #         self.conn.close()

    def create_table(self, create_table_sql) -> None:
        """create a table from the create_table_sql statement
        Attributes:
          create_table_sql: a CREATE TABLE statement

        """
        try:
            _c = self.conn.cursor()
            _c.execute(create_table_sql)
        except Error as _e:
            print(_e)

    def create_database(self) -> None:
        """Creates database structure"""

        sql_create_asset_type_table = """ CREATE TABLE IF NOT EXISTS asset_type (
                                            id integer PRIMARY KEY,
                                            name text NOT NULL,
                                            url text NOT NULL
                                        ); """
        sql_create_category_table = """ CREATE TABLE IF NOT EXISTS category (
                                            id integer PRIMARY KEY,
                                            asset_type integer NOT NULL, 
                                            name text NOT NULL,
                                            url text NOT NULL,
                                            FOREIGN KEY (asset_type) REFERENCES asset_type (id)
                                        ); """
        sql_create_asset_table = """ CREATE TABLE IF NOT EXISTS asset (
                                            id integer PRIMARY KEY,
                                            category integer NOT NULL, 
                                            name text NOT NULL,
                                            url text NOT NULL,
                                            preview_image text NOT NULL,
                                            details_image text,
                                            variant_1_image text,
                                            variant_2_image text,
                                            variant_3_image text,
                                            have_preview_image_changed bool,
                                            have_details_image_changed bool,
                                            have_variant_1_image_changed bool,
                                            have_variant_2_image_changed bool,
                                            have_variant_3_image_changed bool,
                                            last_change_date timestamp,
                                            need_to_check bool,
                                            format_sbsar bool,
                                            format_sbs bool,
                                            format_exr bool,
                                            format_fbx bool,
                                            format_glb bool,
                                            format_mdl bool,
                                            have_format_sbsar bool,
                                            have_format_sbs bool,
                                            have_format_exr bool,
                                            have_format_fbx bool,
                                            have_format_glb bool,
                                            have_format_mdl bool,
                                            FOREIGN KEY (category) REFERENCES category (id)
                                        );"""
        self.create_table(sql_create_asset_type_table)
        self.create_table(sql_create_category_table)
        self.create_table(sql_create_asset_table)

    def set_new_asset_type(self, name, url) -> int:
        """Creates new entry with given asset type.
        Do not check for the duplicates, so be careful.

        :param str name: name of the asset type
        :param str url: url to the asset type
        :return: id of the new asset type entry
        """
        sql = """INSERT INTO asset_type (name, url) VALUES(?, ?)"""
        _c = self.conn.cursor()
        _c.execute(sql, (name, url))
        self.conn.commit()
        return _c.lastrowid

    def update_asset_type(self, asset_id, name, url) -> None:
        """Update asset type entry with given id to the new name

        :param int asset_id: id of the asset type for it's identification
        :param str name: changed name of the asset type
        :param str url: url to the asset type
        """
        sql = """UPDATE asset_type SET name = ?, url = ? WHERE id = ?"""
        _c = self.conn.cursor()
        _c.execute(sql, (name, url, asset_id))
        self.conn.commit()

    def get_asset_type_by_name(self, name) -> []:
        """Database query for the asset type

        :param str name: name of the asset type
        :return: asset type data
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset_type WHERE name=?", (name,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_asset_type_name_by_id(self, asset_id) -> str:
        """
        Get Asset type name by ID
        :param int asset_id: asset id
        :return: asset type name
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset_type WHERE id=?", (asset_id,))
        rows = _c.fetchall()

        return rows[0][1]

    def get_all_asset_types(self) -> []:
        """Database query for the asset type

        :return: asset type data
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset_type")

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def set_new_category(self, name, url, asset_type_id) -> int:
        """Creates new entry with given category.
        Do not check for the duplicates, so be careful.

        :param str name: name of the asset type
        :param str url: url to the asset type
        :param int asset_type_id: id of the parent asset type
        :return: id of the new category entry
        """
        sql = """INSERT INTO category (name, url, asset_type) VALUES(?, ?, ?)"""
        _c = self.conn.cursor()
        _c.execute(sql, (name, url, asset_type_id))
        self.conn.commit()
        return _c.lastrowid

    def update_category(self, category_id, name, url, asset_type_id) -> None:
        """Update category entry with given id to the new name

        :param int category_id: id of the asset type for it's identification
        :param str name: changed name of the asset type
        :param str url: url to the asset type
        :param int asset_type_id: id of the parent asset type
        """
        sql = """UPDATE category SET name = ?, url = ?, asset_type = ? WHERE id = ?"""
        _c = self.conn.cursor()
        _c.execute(sql, (name, url, asset_type_id, category_id))
        self.conn.commit()

    def get_category_by_name_and_asset_type_id(self, name, asset_type_id) -> []:
        """Database query for the category by name and asset type

        :param int asset_type_id: id of the asset type
        :param str name: name of the category
        :return: asset type data
        """
        _c = self.conn.cursor()
        _c.execute(
            "SELECT * FROM category WHERE name=? AND asset_type=?",
            (name, asset_type_id),
        )

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_all_categories(self) -> []:
        """Database query for the all categories

        :return: category data
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM category")

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_all_categories_by_id(self, category_id) -> []:
        """Database query for the all categories

        :return: category data
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM category WHERE id=?", (category_id,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_all_categories_by_asset_type_id(self, asset_type_id) -> [int]:
        """Database query for the all categories by asset type

        :param int asset_type_id: id of the asset type
        :return: asset type data
        """
        _c = self.conn.cursor()
        _c.execute(
            "SELECT * FROM category WHERE asset_type=?",
            (asset_type_id,),
        )

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def set_new_asset(
        self,
        asset_data,
    ) -> int:
        """Creates new entry with given asset.
        Do not check for the duplicates, so be careful.

        :param bool have_format_mdl: does local mdl exist
        :return:  id of the new asset entry
        """
        sql = """INSERT INTO asset (name, url, category, preview_image,
         details_image, variant_1_image, variant_2_image, variant_3_image,
         have_preview_image_changed, have_details_image_changed, have_variant_1_image_changed,
         have_variant_2_image_changed, have_variant_3_image_changed, last_change_date, 
         need_to_check, format_sbsar, format_sbs, format_exr, format_fbx, 
         format_glb, format_mdl, have_format_sbsar, have_format_sbs, have_format_exr, 
         have_format_fbx, have_format_glb, have_format_mdl) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        _c = self.conn.cursor()
        _c.execute(
            sql,
            (
                asset_data["name"],
                asset_data["url"],
                asset_data["category"],
                asset_data["preview_image"],
                asset_data["details_image"],
                asset_data["variant_1_image"],
                asset_data["variant_2_image"],
                asset_data["variant_3_image"],
                asset_data["have_preview_image_changed"],
                asset_data["have_details_image_changed"],
                asset_data["have_variant_1_image_changed"],
                asset_data["have_variant_2_image_changed"],
                asset_data["have_variant_3_image_changed"],
                asset_data["last_change_date"],
                asset_data["need_to_check"],
                asset_data["format_sbsar"],
                asset_data["format_sbs"],
                asset_data["format_exr"],
                asset_data["format_fbx"],
                asset_data["format_glb"],
                asset_data["format_mdl"],
                asset_data["have_format_sbsar"],
                asset_data["have_format_sbs"],
                asset_data["have_format_exr"],
                asset_data["have_format_fbx"],
                asset_data["have_format_glb"],
                asset_data["have_format_mdl"],
            ),
        )
        self.conn.commit()
        return _c.lastrowid

    def update_asset(self, asset_data) -> None:
        """Update asset entry by given id.
        Do not check for the duplicates, so be careful.

        :param []] asset_data: data of the asset
        :return:  id of the new asset entry
        """
        sql = """UPDATE asset SET name = ?, url = ?, category = ?, preview_image = ?,
                 details_image = ?, variant_1_image = ?, variant_2_image = ?, variant_3_image = ?,
                 have_preview_image_changed = ?, have_details_image_changed = ?, have_variant_1_image_changed = ?,
                 have_variant_2_image_changed = ?, have_variant_3_image_changed = ?, last_change_date = ?, 
                 need_to_check = ?, format_sbsar = ?, format_sbs = ?, format_exr = ?, format_fbx = ?, 
                 format_glb = ?, format_mdl = ?, have_format_sbsar = ?, have_format_sbs = ?, have_format_exr = ?, 
                 have_format_fbx = ?, have_format_glb = ?, have_format_mdl = ? WHERE id = ?"""
        _c = self.conn.cursor()
        _c.execute(
            sql,
            (
                asset_data["name"],
                asset_data["url"],
                asset_data["category"],
                asset_data["preview_image"],
                asset_data["details_image"],
                asset_data["variant_1_image"],
                asset_data["variant_2_image"],
                asset_data["variant_3_image"],
                asset_data["have_preview_image_changed"],
                asset_data["have_details_image_changed"],
                asset_data["have_variant_1_image_changed"],
                asset_data["have_variant_2_image_changed"],
                asset_data["have_variant_3_image_changed"],
                asset_data["last_change_date"],
                asset_data["need_to_check"],
                asset_data["format_sbsar"],
                asset_data["format_sbs"],
                asset_data["format_exr"],
                asset_data["format_fbx"],
                asset_data["format_glb"],
                asset_data["format_mdl"],
                asset_data["have_format_sbsar"],
                asset_data["have_format_sbs"],
                asset_data["have_format_exr"],
                asset_data["have_format_fbx"],
                asset_data["have_format_glb"],
                asset_data["have_format_mdl"],
                asset_data["id"],
            ),
        )
        self.conn.commit()

    def get_asset_by_name(self, name) -> []:
        """Database query for the asset

        :param str name: name of the asset looked in database
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset WHERE name=?", (name,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_asset_by_id(self, asset_id) -> []:
        """Database query for the asset

        :param int asset_id: name of the asset looked in database
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset WHERE id=?", (asset_id,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_asset_by_url(self, url) -> []:
        """Database query for the asset

        :param str url: url of the asset looked in database
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset WHERE url=?", (url,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_all_assets_by_category(self, category_id) -> []:
        """Database query for the asset

        :param int category_id: category id of the asset looked in database
        """
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset WHERE category=?", (category_id,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def get_all_assets_for_check(self) -> []:
        """Database query for the asset"""
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM asset WHERE need_to_check=?", (True,))

        rows = _c.fetchall()

        return [dict(row) for row in rows]

    def prepare_asset_type_and_category_dictionary(self) -> {}:
        """Creates dictionary with asset type and category names and element count

        :rtype: dictionary of the 'asset type' : (elements in type
                                                {'category': elements in category})
        """
        all_asset_types = self.get_all_asset_types()
        result = {}
        for asset_type in all_asset_types:
            all_categories = self.get_all_categories_by_asset_type_id(asset_type["id"])
            category_list = {}
            for category in all_categories:
                category_list[category["name"]] = len(
                    self.get_all_assets_by_category(category["id"])
                )
            result[asset_type["name"]] = (sum(category_list.values()), category_list)

        return result

    def get_asset_type_and_category_name_by_category_id(self, asset_type_id) -> []:
        _c = self.conn.cursor()
        _c.execute("SELECT * FROM category where id=?", (asset_type_id,))

        rows = _c.fetchall()
        res = [dict(row) for row in rows]
        _c.execute("SELECT * FROM asset_type where id=?", (res[0]["asset_type"],))
        rows1 = _c.fetchall()
        res1 = [dict(row) for row in rows1]

        return [res1[0]["name"], res[0]["name"]]

    def set_asset_art_as_updated(self, asset_id):
        sql = """UPDATE asset SET have_preview_image_changed = ?, have_details_image_changed = ?,
        have_variant_1_image_changed = ?, have_variant_2_image_changed = ?,
         have_variant_3_image_changed = ? WHERE id = ?"""
        _c = self.conn.cursor()
        _c.execute(sql, (False, False, False, False, False, asset_id))
        self.conn.commit()
        # return _c.lastrowid
