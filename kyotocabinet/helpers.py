"""
====================
kyotocabinet.helpers
====================
"""
import os

from collections.abc import MutableMapping
from functools import partial, wraps
from threading import RLock

import msgpack

from lz4.block import compress, decompress

from _kyotocabinet import DB, Error as KyotoError

from .utils import green_iter, green_sleep, smart_str


COMPRESSORS = {
    None: (lambda item: item, lambda item: item),
    'lz4': (compress, decompress),
}
SERIALIZERS = {
    'msgpack': (msgpack.dumps, partial(msgpack.loads, strict_map_key=False))
}


class KyotoCabinetClient(object):
    """KyotoCabinet datastore client."""

    __slots__ = ('path', 'simple_mode', '_connection_pool', '_options')

    def __init__(self, url, **options):
        assert url.startswith('kch://')
        self.path = url[6:]
        self.path = os.path.expanduser(self.path)
        err_msg = '{0} should be dir'
        if options.get('simple', False):
            self._connection_pool = None
            dir_name = os.path.dirname(self.path)
            assert os.path.exists(dir_name), err_msg.format(dir_name)
            self.simple_mode = True
        else:
            assert os.path.isdir(self.path), err_msg.format(self.path)
            self.simple_mode = False
            self._connection_pool = {}
        self._options = options

    def clone(self):
        """Clone current Client's connection params."""
        cloned = object.__new__(type(self))
        cloned.path = self.path
        cloned.simple_mode = self.simple_mode
        cloned._connection_pool = None if cloned.simple_mode else {}
        cloned._options = self._options
        return cloned

    def disconnect_all(self):
        """Close already opened connection to datastore."""
        if self.simple_mode:
            if self._connection_pool:
                self._connection_pool.close()
            self._connection_pool = None
        else:
            for connection in self._connection_pool.values():
                connection.close()
            self._connection_pool = {}
        return True

    def exists(self, key):
        """Check if key is present."""
        return smart_str(key) in self.get_connection(key)

    def flush_all(self):
        """
        Compeletely remove datastore from disk.

        Return ``True`` if flush operation succeed, ``False`` otherwise.
        """
        # If database already exists on disk - try to remove it
        if os.path.exists(self.path):
            # Close and nullify connection first
            if self._connection_pool:
                self.disconnect_all()
            filenames = (
                [self.path]
                if self.simple_mode
                else (item for item in list(os.walk(self.path))[0][-1])
            )
            for filename in filenames:
                try:
                    os.remove(os.path.join(self.path, filename))
                except (IOError, OSError):
                    return False
        return True

    def flush(self, key_prefix):
        if not self.simple_mode and key_prefix in self._connection_pool:
            self._connection_pool.pop(key_prefix).close()

        path = '{0}.kch'.format(os.path.join(self.path, key_prefix))
        try:
            os.remove(path)
        except (IOError, OSError):
            return False
        return True

    def get_connection(self, key, prefix=None):
        """Get connection to datastore."""
        if self.simple_mode:
            return self.get_connection_simple(key)
        else:
            return self.get_connection_splitted(key, prefix)

    def get_connection_simple(self, key):
        """Get connection to one DB."""
        if not self._connection_pool:
            assert self.path.endswith('kch')
            self._connection_pool = KyotoCabinetDict(
                self.path, **self._options
            )
        return self._connection_pool

    def get_connection_splitted(self, key, prefix=None):
        """Get connection by prefix of key."""
        prefix = key.rsplit(':', 1)[0] if prefix is None else prefix
        if prefix not in self._connection_pool:
            file_name = '{0}.kch'.format(os.path.join(self.path, prefix))
            self._connection_pool[prefix] = KyotoCabinetDict(
                file_name, **self._options
            )
        return self._connection_pool[prefix]

    def get(self, key):
        """
        Get key value from cache.

        If key does not exist in cache returns ``None`` instead of raising
        ``NotFoundError``.
        """
        key = smart_str(key)
        return self.get_connection(key).get(key)

    def get_multi(self, keys, key_prefix=None):
        """
        Get multiple keys values from cache.

        If some of keys does not exist they would be missed in response.
        """
        results = {}
        if key_prefix:
            key_prefix = '{0}:'.format(key_prefix.rstrip(':'))
            connection = self.get_connection(key_prefix)
            mapped_keys = {
                '{0}{1}'.format(key_prefix, key): key for key in keys
            }
            for key in mapped_keys:
                value = connection.get(smart_str(key))
                if value is not None:
                    results[mapped_keys[key]] = value
        else:
            for key in keys:
                value = self.get(key)
                if value is not None:
                    results[key] = value
        return results

    def iteritems(self, prefix):
        """Iterate through items."""
        return iter(self.get_connection(prefix).items())

    def iterkeys(self, prefix):
        """Iterate through keys."""
        return iter(self.get_connection(prefix).keys())

    def itervalues(self, prefix):
        """Iterate through items."""
        return iter(self.get_connection(prefix).values())

    def keys(self, prefix):
        """Get all keys."""
        return list(self.iterkeys(prefix))

    def set(self, key, value, time=0, format=None):
        """Set key value to cache."""
        if isinstance(value, set):
            value = list(value)

        key = smart_str(key)
        self.get_connection(key)[key] = value
        return True

    def set_multi(self, data, time=0, format=None, key_prefix=None):
        """
        Set multiple keys values to cache.

        Returns list of keys which couldn't be stored to cache.
        """
        if key_prefix:
            key_prefix = '{0}:'.format(key_prefix.rstrip(':'))
            connection = self.get_connection(key_prefix)
            for key, value in data.items():
                if isinstance(value, set):
                    value = list(value)
                key = smart_str('{0}{1}'.format(key_prefix, key))
                connection[key] = value
            self.sync(key_prefix)
        else:
            for key, value in data.items():
                self.set(key, value)
            self.sync()

        return []

    def sync(self, prefix=None):
        """Synchronize cache state with disk."""
        if self.simple_mode or prefix:
            self.get_connection(prefix).sync(hard=False)
        else:
            for connection in self._connection_pool.values():
                connection.sync(hard=False)
        return True


def _write_operation(func):
    """Decorate method to mark write operations in KyotoCabinetDict class."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._read_only:
            raise RuntimeError('Storage is in read-only mode')
        with self._write_lock:
            return func(self, *args, **kwargs)

    return wrapper


class KyotoCabinetDict(MutableMapping):
    """Simple KyotoCabinet dict-like wrapper.

    Makes Kyoto operating like python dict, using msgpack serialization and
    lz4 compression by default.

    Thread-safety and multiple writes:
    1. You can have any number of read_only storages for the same file.
    2. You cannot create several storages in write mode inside 1 process.
    3. You cannot create several storages in write mode in different processes
       as KyotoCabinet use file locking to prevent that.
    4. Write operations are thread safe.
    5. You cannot have readers if any writer is active. i.e. RWLock
    6. Don't forget to close storage explicitly or use the object itself
       as a context manager.
    """

    # Track opened files in write mode as it's not handled by KyotoCabinet
    # within the same process
    _opened_in_write_mode = set()

    def __init__(
        self,
        path,
        read_only=True,
        serializer='msgpack',
        compressor='lz4',
        open_options='#opts=s#msiz=0#bnum=524288#apow=3',
    ):
        # Store args for future use
        self._path = os.path.abspath(path)
        self._read_only = read_only
        self._open_options = open_options

        self._compressor = COMPRESSORS[compressor]
        self._serializer = SERIALIZERS[serializer]
        # Open kyoto storage
        self._db = self.__open_kyoto_file(
            self._path, self._read_only, self._open_options
        )
        self._write_lock = RLock()

    def __open_kyoto_file(self, path, read_only, open_options):
        """Open kyoto file."""
        assert path.endswith('.kch'), 'Should have .kch extension'
        if not read_only and path in KyotoCabinetDict._opened_in_write_mode:
            raise RuntimeError(
                'File {0} is already opened in the write mode'.format(path)
            )
        db = DB(DB.GEXCEPTIONAL)
        mode = DB.OWRITER | DB.OCREATE
        if read_only:
            mode = DB.OREADER
        try:
            result = db.open(
                '{0}{1}'.format(path, open_options),
                mode | DB.OTRYLOCK | DB.ONOREPAIR,
            )
        except KyotoError:
            result = None

        if not result:
            raise RuntimeError(
                'Failed to open kyoto file: {0} Error: {1}'.format(
                    path, db.error()
                )
            )
        if not read_only:
            KyotoCabinetDict._opened_in_write_mode.add(path)
        return db

    def __contains__(self, key):
        return self._db.check(key) != -1

    @_write_operation
    def __delitem__(self, key):
        del self._db[key]

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def __getitem__(self, key):
        value = self._db[key]
        if value is not None:
            return self._loads(value)
        raise KeyError(key)

    def __iter__(self):
        return green_iter(
            iter(item.decode('utf-8') for item in self._db.__iter__())
        )

    def __len__(self):
        return self._db.__len__()

    @_write_operation
    def __setitem__(self, key, value):
        result = self._db.set(key, self._dumps(value))
        if not result:
            raise RuntimeError('Cannot write: {0}'.format(self._db.error()))

    def _dumps(self, data):
        """Dump python object to string."""
        return self._compressor[0](self._serializer[0](data))

    def _loads(self, data):
        """Restore python object from string."""
        return self._serializer[1](self._compressor[1](data))

    @_write_operation
    def clear(self):
        """Delete all items from storage."""
        self._db.clear()
        self.sync()

    def close(self):
        """Perform proper file close."""
        self.sync()
        self._db.close()
        if not self._read_only:
            KyotoCabinetDict._opened_in_write_mode.discard(self._path)

    @_write_operation
    def defrag(self):
        """Defragment file via copying everything to a tmp file."""
        with self._write_lock:
            # Sync all data first
            self.sync()

            # Construct tmp DB
            tmp_path = self._path[:-4] + '.tmp.kch'
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            tmp_db = self.__open_kyoto_file(
                path=tmp_path, read_only=False, open_options=self._open_options
            )

            # Copy all keys to the tmp DB
            for key in self._db:
                tmp_db[key] = self._db[key]

            # Close both storages
            tmp_db.close()
            KyotoCabinetDict._opened_in_write_mode.discard(tmp_path)
            self.close()

            # Replace original file with new one and reopen it
            os.rename(tmp_path, self._path)
            self._db = self.__open_kyoto_file(
                self._path, self._read_only, self._open_options
            )

    def sync(self, hard=True):
        """Flush all updates to the disk.

        :param hard: bool, if True - cause synchronization with physical device
        """
        self._db.synchronize(hard)

    def warmup(self, chunk_size=128 * 1024):
        with open(self._path, 'rb') as fp:
            counter = 0
            while fp.read(chunk_size):
                counter += 1
                if counter % 1000 == 0:
                    green_sleep(0)
