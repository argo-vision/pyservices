# coding=utf-8
"""
Manage the processing of the messages and the saving part.
On exception during the processing part the message in handled.
"""

import logging

logger = logging.getLogger(__package__)


class Handler:
    """
    Manage the processing of the messages and the saving part.
    On exception during the processing part the message in handled.
    """

    def __init__(self, chain, saver):
        """

        :param chain: The processing chain dictionary. '_fixed' field is required.
        :param saver: Where the messages must be saved.
        """
        self._chain = chain
        self._saver = saver

    def feed(self, messages):
        """
        Process the message on a chain and pass the result to a saver.
        If there is an exception during the process a nack is done on the message.

        :param messages: The messages list to process.
            On fail nack on message else is passed to the saver
        """
        logger.info("Processing messages")
        for x in messages:
            result = {}

            for key in self._chain:
                try:
                    val = self._chain[key](x.data)
                except Exception as e:
                    logger.error("Failed to process data: {}".format(e))
                    break

                result[key] = val
            else:
                self._saver.save(result, x)

        logger.info("Data processed")
