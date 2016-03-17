from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session as AlembicSession

from seabird.plugin import Plugin


# This is the base all models should inherit from
Base = declarative_base()  # pylint: disable=invalid-name


class Session(AlembicSession):
    def get_or_create(self, model, **kwargs):
        # http://stackoverflow.com/a/21146492
        try:
            return self.query(model).filter_by(**kwargs).one(), True
        except NoResultFound:
            created = model(**kwargs)
            try:
                self.add(created)
                self.flush()
                return created, False
            except IntegrityError:
                self.rollback()
                return self.query(model).filter_by(**kwargs).one(), True


class DatabasePlugin(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.engine = create_engine(self.bot.config.get('DB_URI',
                                                        'sqlite:///bot.db'))
        self.engine.connect()

        # We need to use our own session class so we can add methods onto
        # it. In particular, get_or_create is very useful.
        self.sessionmaker = sessionmaker(bind=self.engine, class_=Session)

    @contextmanager
    def session(self):
        """Provide a transactional scope around a series of operations.

        This is taken from the SQLAlchemy docs and adapted slightly to fit in
        here.

        It will be available on the bot object as db_session.
        """
        session = self.sessionmaker()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


class DatabaseMixin:
    def __init__(self, bot):
        self.db = bot.load_plugin(DatabasePlugin)  # noqa # pylint: disable=invalid-name
