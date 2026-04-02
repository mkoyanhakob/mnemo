from core import MnemoCore
from api import MnemoApi
import threading
import logging

logger = logging.getLogger('Mnemo')

if __name__ == '__main__':
    core = MnemoCore()

    mnemo_api = MnemoApi(core_instance=core)

    api_thread = threading.Thread(target=mnemo_api.run_api, daemon=True)
    api_thread.start()
    logger.info('Mnemo: API started!')

    core.run()