import time
from peewee import IntegerField, CharField

from . import db, BaseModel


class Session(BaseModel):
    created_at = IntegerField()
    abstract = CharField(null=True)

    class Meta:
        table_name = 'session'

    @classmethod
    def create(cls):
        with db.atomic():
            obj = cls(created_at=int(time.time()))
            obj.save()
            return obj

    @classmethod
    def update_abstract(cls, session_id: int, abstract: str):
        obj = cls.get_or_none(cls.id == session_id)
        if not obj or obj.abstract:
            return False
        obj.abstract = abstract
        obj.save()
        return True

    @classmethod
    def delete_session(cls, session_id: int):
        obj = cls.get_or_none(cls.id == session_id)
        if not obj:
            return False
        from .history import History
        with db.atomic():
            History.delete().where(History.session == session_id).execute()
            obj.delete_instance()
        return True

    @classmethod
    def get_sessions(cls):
        return list(cls.select())
