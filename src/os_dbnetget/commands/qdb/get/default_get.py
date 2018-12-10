import logging
import signal
from io import BytesIO
from itertools import chain

from os_docid import docid
from os_qdb_protocal import create_protocal

from os_dbnetget.clients.sync_client import SyncClientPool
from os_dbnetget.commands.qdb.default_command import DefaultCommand
from os_dbnetget.exceptions import UsageError
from os_dbnetget.utils import binary_stdout

_logger = logging.getLogger(__name__)


class Get(DefaultCommand):
    ENGINE_NAME = 'default'


    def _get_endpoints(self, args):

        endpoints = None
        if args.endpoints:
            endpoints = tuple([e.strip()
                               for e in args.endpoints.split(',') if e.strip()])
        else:
            endpoints = tuple([e.strip()
                               for e in args.endpoints_list if e.strip()])
        if not endpoints:
            raise UsageError('No endpoints, check your arguments')

        return endpoints

    def _create_client_pool(self, args):
        return SyncClientPool(self._get_endpoints(args))

    def run(self, args):

        pool = self._create_client_pool(args)
        ouput = self._create_output(args)
        stop = False

        def on_stop(signum, frame):
            # try:
            stop = True
            print('---------------------------')
            pool.close()
            print('---------aaaaaaaaaaaaaa-')
            ouput.close()
            print('-----------dddddddddddddddd')
            # except:
            #     pass
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
            signal.signal(sig, on_stop)

        try:
            for line in chain.from_iterable(args.inputs):
                if stop:
                    print('break')
                    break
                line = line.strip()
                status = 'N'
                try:
                    d = docid(line)
                except NotImplementedError:
                    status = 'E'
                if status != 'E':
                    proto = create_protocal('get', d.bytes[16:])
                    p = pool.execute(proto)
                    status = 'N'
                    if p.value:
                        status = 'Y'
                        ouput.write(p.value)
                _logger.info('%s\t%s' % (line, status))
        # except Exception as e:
        #     raise e
        #     _logger.error('Error, %s' % str(e))
        finally:
            try:
                pool.close()
                ouput.close()
            except:
                pass
