#-*- coding: utf-8 -*-

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.util import object_state
from sqlalchemy.ext.declarative import declarative_base

from .exception import OperationException

__all__ = ['AbstractModel']

DeclarativeBase = declarative_base()


class AbstractModel(DeclarativeBase):
    __abstract__ = True

    class Meta:
        session = None
        as_scoped_session = True

    @property
    def state(self):
        return object_state(self)

    @property
    def is_transient(self):
        return self.state.transient

    @property
    def is_pending(self):
        return self.state.pending

    @property
    def is_persistent(self):
        return self.state.persistent

    @property
    def is_deleted(self):
        return self.state.deleted

    @classmethod
    def get_session(cls):
        if cls.Meta.as_scoped_session:
            Session = scoped_session(cls.Meta.session)
            return Session()
        return cls.Meta.session()

    @classmethod
    def session(cls):
        return cls.get_session()

    @classmethod
    def get_query(cls, instance):
        return cls.get_session().query(instance)

    @classmethod
    def query(cls):
        return cls.get_query(cls)

    @classmethod
    def create(cls, data):
        return cls.new(**data)

    @classmethod
    def new(cls, **kwargs):
        return cls(**kwargs)

    @classmethod
    def get(cls, id):
        return cls.query().get(id)

    @classmethod
    def all(cls):
        return cls.query().all()

    @classmethod
    def find(cls, id=None):
        if not id is None:
            return cls.get(id)
        return cls.all()

    @classmethod
    def find_by(cls, **kwargs):
        return cls.query().filter_by(**kwargs).all()

    @classmethod
    def exists(cls, **kwargs):
        return cls.query().exists(**kwargs)

    @classmethod
    def offset(cls, offset):
        return cls.query().offset(offset)

    @classmethod
    def limit(cls, limit):
        return cls.query().limit(limit)

    @classmethod
    def count(cls):
        return cls.query().count()

    @classmethod
    def execute(cls, *args, **kwargs):
        try:
            return cls.session().execute(*args, **kwargs)
        except Exception, err:
            raise OperationException(err.message)

    def insert(self, with_commit=True):
        try:
            session = self.session()
            session.add(self)
            if with_commit:
                session.commit()
        except Exception, err:
            raise OperationException(err.message)
        return True

    @classmethod
    def insert_all(cls, entities, with_commit=True):
        try:
            session = cls.session()
            session.bulk_save_objects(entities)
            if with_commit:
                session.commit()
        except Exception, err:
            cls.rollback()
            raise OperationException(err.message)

    def update(self, with_commit=True):
        if with_commit:
            try:
                self.session().commit()
            except Exception, err:
                raise OperationException(err.message)
        return True

    def delete(self, with_flush=True):
        try:
            session = self.session()
            if self.is_transient:
                return True
            elif self.is_pending:
                session.delete(self)
                return True

            if with_flush:
                if self.is_persistent:
                    session.delete(self)
                    session.flush()
        except Exception, err:
            raise OperationException(err.message)
        return True

    def save(self, with_commit=True):
        if self.is_transient:
            return self.insert(with_commit)
        return self.update(with_commit)

    @classmethod
    def rollback(cls):
        return cls.session().rollback()

    def set_session_as_scoped(self, as_scoped):
        self.Meta.as_scoped_session = bool(as_scoped)

    def apply_from_dict(self, data):
        for k, v in data.items():
            setattr(self, k, v)
        return self
