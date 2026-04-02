from etcd3 import Etcd3Client
import sys
import logging
import os

etcd_host = os.getenv('ETCD_HOST')

logger = logging.getLogger('Mnemo')

class EtcdManager():
    def __init__(self):
        try:
            logger.info('Mnemo: Connecting to etcd ...')
             
            # Connecting To Etcd KV Store.
            self.etcd_client = Etcd3Client(
                host=etcd_host,
                port='2379', 
                ca_cert='/var/kubernetes/certs/etcd/ca.crt',
                cert_cert='/var/kubernetes/certs/etcd/server.crt', 
                cert_key='/var/kubernetes/certs/etcd/server.key', 
            )
            logger.info('Mnemo: Etcd connection established.')
             
            self.events_iterator, _ = self.etcd_client.watch_prefix('/registry/events')
            logger.info('Mnemo: Started watching on /registry/events ...')
        except Exception as e:
            logger.error(f'Mnemo: Failed to connect to etcd: {e}')
            sys.exit(1)
    
    def event(self):
         try:
            event = next(self.events_iterator)
            return event
         except StopIteration:
            return None
