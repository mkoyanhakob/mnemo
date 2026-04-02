import logging
import subprocess
import json

logger = logging.getLogger('Mnemo')

class Chunker():
    def __init__(self):
        pass

    def _decode_raw_data(self, raw_data):
        key = raw_data.key.decode('utf-8')
        raw_payload = raw_data.value

        try:
            # Run Process For Auger Etcd Decoder.
            auger_process = subprocess.Popen(
                ['auger', 'decode', '--output', 'json'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = auger_process.communicate(input=raw_payload)

            if auger_process.returncode == 0:
                decoded_event_json = json.loads(stdout.decode('utf-8'))
                    
                # Remove the noise: 'managedFields'.
                decoded_event_json.get('metadata', {}).pop('managedFields', None)

                return decoded_event_json
            else:
                logger.error(f'Auger: Decoding failed for {key}: {stderr.decode()}')
        except Exception as e:
            logger.error(f'Processing error: {e}')

    def _chunk_data(self, data):
        meta = data.get('metadata', {})
        inv = data.get('involvedObject', {})

        key_id = f"{inv.get('name', 'unknown')}.{data.get('reason', 'unknown')}"

        search_string = (
            f"REASON: {data.get('reason', 'Unknown')} | "
            f"MESSAGE: {data.get('message', 'No message')} | "
            f"OBJECT: {inv.get('kind')}/{inv.get('name')} | "
            f"TIMESTAMP: {meta.get('creationTimestamp')} | "
            f"SOURCE: {data.get('source', {}).get('component', 'unknown')} | "
            f"OBJECT_NAMESPACE: {inv.get('namespace')} | "
            f"COUNT: {data.get('count', 1)} | "
            f"TYPE: {data.get('type', 'Unknown')} | "
        )

        metadata = {
            'uid': meta.get('uid'),
            'creation_timestamp': meta.get('creationTimestamp'),
            'first_timestamp': data.get('firstTimestamp') or data.get('eventTime'),
            'last_timestamp': data.get('lastTimestamp') or data.get('eventTime'),
            'count': data.get('count', 1),
            'involved_uid': inv.get('uid'),
            'involved_name': inv.get('name'),
            'resource_version': inv.get('resourceVersion'),
            'involved_kind': inv.get('kind', ''),
            'involved_namespace': inv.get('namespace', ''), 
            'reason': data.get('reason', ''), 
            'type': data.get('type', ''), 
            'source_component': data.get('source', {}).get('component', '')
        }

        return {
            'id': key_id,
            'document': search_string,
            'metadata': metadata
        }
    
    def process(self, raw_data):
        decoded_data = self._decode_raw_data(raw_data)
        if not decoded_data:
            logger.warning(f'Mnemo: Skipping decode.')
            return None
        
        chunked_data = self._chunk_data(decoded_data)

        return chunked_data