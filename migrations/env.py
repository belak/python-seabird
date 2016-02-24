from importlib import import_module
from logging.config import dictConfig
import os.path
from pkgutil import walk_packages
import sys

from alembic import context
from sqlalchemy import create_engine

# Add the directory above the migrations dir to the path to ensure all the
# models can be found.
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.path.pardir)))

from seabird import modules
from seabird.config import Config
from seabird.modules.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set up the loggers. This is essentially the loggers from the default config
# in dict form.
dictConfig({
    'version': 1,
    'root': {
        'level': 'WARN',
        'handlers': ['console']
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'level': 'NOTSET',
            'formatter': 'generic',
        },
    },
    'formatters': {
        'generic': {
            'format': '%(levelname)-5.5s [%(name)s] %(message)s',
            'datefmt': '%H:%M:%S',
        }
    },
    'loggers': {
        'alembic': {
            'level': 'INFO',
            'handlers': [],
        },
        'sqlalchemy': {
            'level': 'WARN',
            'handlers': ['console'],
        },
    },
})

# target_metadata is used for autogenerate support
target_metadata = Base.metadata

# Make sure we get all plugins which need models
for _, name, _ in walk_packages(modules.__path__, 'seabird.modules.'):
    import_module(name)

# Get the config module
# TODO: Make sure the default is only in one place.
config = Config()
config.from_module('config')
db_uri = config.get('DB_URI', 'sqlite:///bot.db')


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=db_uri, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = create_engine(db_uri)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
