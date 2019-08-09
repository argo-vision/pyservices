import datetime
import json
import logging

from pymongo.errors import DuplicateKeyError

import pyservices

logger = logging.getLogger(__package__)


# TODO: db support needed
class Saver:
    """
    Simple saver class
    """

    def __init__(self, db):
        """
        Manage a dictionary of dbs where the information will be saved.
        :param db:
        """
        self._db = db

    def save(self, results, message):
        """
        Save the results.
        """
        decoded_result = {d: json.loads(pyservices.JSON.encode(results[d])) for d in results.keys()}

        try:
            id_res = decoded_result.pop('id')
        except KeyError:
            message.ack()
            return

        id_res['timestamp'] = datetime.datetime.fromisoformat(id_res['timestamp'])

        date = datetime.datetime.now().astimezone(datetime.timezone.utc)
        decoded_result['ingestion_time'] = date

        # fixme: ACK / NACK for gcloud
        try:
            self._db.insert_one(id_res, decoded_result)
            message.ack()
            logger.info("Data saved")
        except DuplicateKeyError:
            logger.warning("Received a duplicated message")
            message.ack()
        except Exception as e:
            logger.error("Exception in processing: {} ".format(e))
            message.nack()
