import time

from peewee import IntegerField, TextField, ForeignKeyField

from . import BaseModel, db
from .session import Session


class History(BaseModel):
    timestamp = IntegerField()
    user_input = TextField()
    answer = TextField(null=True)
    session = ForeignKeyField(Session, backref='histories', column_name='session_id', on_delete='CASCADE')

    class Meta:
        table_name = 'history'

    @classmethod
    def create(cls, session_id: int, user_input: str, answer: str = None):
        with db.atomic():
            obj = cls(
                timestamp=int(time.time()),
                session=session_id,
                user_input=user_input,
                answer=answer
            )
            obj.save()
            return obj

    @classmethod
    def update_answer(cls, history_id: int, answer: str):
        obj = cls.get_or_none(cls.id == history_id)
        if not obj:
            return False
        obj.answer = answer
        obj.save()
        return True

    @classmethod
    def delete_history(cls, history_id: int):
        obj = cls.get_or_none(cls.id == history_id)
        if not obj:
            return False
        obj.delete_instance()
        return True

    @classmethod
    def get_histories(cls, session_id: int):
        return list(cls.select().where(cls.session == session_id))
