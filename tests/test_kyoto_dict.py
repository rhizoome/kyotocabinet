from unittest import TestCase
from unittest.mock import MagicMock, patch

from kyotocabinet import DB
from kyotocabinet.helpers import KyotoCabinetDict

DB_MOCK = MagicMock()
DB_MOCK.GEXCEPTIONAL = DB.GEXCEPTIONAL
DB_MOCK.OREADER = DB.OREADER
DB_MOCK.OWRITER = DB.OWRITER
DB_MOCK.OCREATE = DB.OCREATE
DB_MOCK.OTRYLOCK = DB.OTRYLOCK
DB_MOCK.ONOREPAIR = DB.ONOREPAIR

OS_MOCK = MagicMock()
OS_MOCK.path = MagicMock()
OS_MOCK.path.abspath = lambda identity: identity


@patch('kyotocabinet.helpers.os', OS_MOCK)
@patch('kyotocabinet.helpers.DB', DB_MOCK)
class TestKyotoCabinetDict(TestCase):

    def test_defrag(self):
        storage = KyotoCabinetDict('file.kch', read_only=False)
        with storage:
            storage.defrag()

    def test_extension(self):
        with self.assertRaises(AssertionError):
            KyotoCabinetDict('wrong_file')

    def test_readonly_fail(self):
        with KyotoCabinetDict('file.kch') as storage:

            with self.assertRaises(RuntimeError):
                storage['key'] = 'value'

            with self.assertRaises(RuntimeError):
                del storage['key']

            with self.assertRaises(RuntimeError):
                storage.clear()

            with self.assertRaises(RuntimeError):
                storage.defrag()

    def test_write_works(self):
        storage = KyotoCabinetDict('file.kch', read_only=False)
        with patch.object(storage, 'close') as close_mock, storage:
            storage['key'] = 'value'
            del storage['key']
        close_mock.assert_called_once_with()

    def test_2_writers_fails(self):
        storage = KyotoCabinetDict('file.kch', read_only=False)
        self.assertEqual(
            KyotoCabinetDict._opened_in_write_mode,
            {'file.kch'}
        )
        with self.assertRaises(RuntimeError):
            KyotoCabinetDict('file.kch', read_only=False)
        storage.close()
        self.assertEqual(KyotoCabinetDict._opened_in_write_mode, set())
