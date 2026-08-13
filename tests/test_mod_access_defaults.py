import sqlite3
import os
import tempfile
import unittest

from backend.database import init_db, get_user_mod_access_flag, set_user_mod_access


class ModAccessDefaultTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_data_dir = os.environ.get("GRAFIOS_VICTORTRUCKS_DATA_DIR")
        os.environ["GRAFIOS_VICTORTRUCKS_DATA_DIR"] = self.tmpdir.name
        import importlib
        import backend.database as database_module
        importlib.reload(database_module)
        database_module.init_db()
        self.conn = sqlite3.connect(database_module.DB_PATH)
        self.cursor = self.conn.cursor()
        # A fresh central database intentionally has no demo or migrated mods.
        # Create the catalog record required to verify the default permission.
        self.cursor.execute(
            """
            INSERT INTO mods (
                title, category, version, author, size_gb, size_bytes,
                compatibility, description, filename, sha256, thumbnail_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Mod de prueba", "Gráficos generales", "1.0.0", "Pruebas",
                0.0, 0, "1.50+", "", "mod_prueba.scs", "0" * 64, "",
            ),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.tmpdir.cleanup()
        if self.old_data_dir is None:
            os.environ.pop("GRAFIOS_VICTORTRUCKS_DATA_DIR", None)
        else:
            os.environ["GRAFIOS_VICTORTRUCKS_DATA_DIR"] = self.old_data_dir

    def test_missing_access_entry_defaults_to_not_acquired(self):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", ("santitrucks.oficial@gmail.com",))
        user = self.cursor.fetchone()
        self.cursor.execute("SELECT id FROM mods LIMIT 1")
        mod = self.cursor.fetchone()
        self.assertIsNotNone(user)
        self.assertIsNotNone(mod)

        # A new user starts with every mod NOT acquired: the server creates no
        # access rows automatically and the default is "locked".
        granted = get_user_mod_access_flag(self.cursor, user[0], mod[0])
        self.assertFalse(granted)

        # Only an explicit grant (performed by an ADMIN) unlocks the mod.
        set_user_mod_access(self.cursor, user[0], mod[0], True)
        self.conn.commit()
        granted_after = get_user_mod_access_flag(self.cursor, user[0], mod[0])
        self.assertTrue(granted_after)


if __name__ == "__main__":
    unittest.main()
