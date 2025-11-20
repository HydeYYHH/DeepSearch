from peewee import SqliteDatabase, Model, PrimaryKeyField
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_BASE_DIR, '..', 'assets', 'database.db')
db = SqliteDatabase(os.path.normpath(_DB_PATH), pragmas={
    'foreign_keys': 1
})


class BaseModel(Model):
    id = PrimaryKeyField()

    class Meta:
        database = db
