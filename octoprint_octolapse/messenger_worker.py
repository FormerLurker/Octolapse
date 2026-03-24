# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################
from __future__ import absolute_import
from __future__ import unicode_literals
from threading import Thread, Lock
# Remove python 2 support
# from six.moves import queue
import queue as queue
from collections import deque
import time
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class PluginMessage(object):
    def __init__(self, message_data, message_type, rate_limit_seconds=0):
        self.create_stamp = time.time()
        self.message_data = message_data
        self.message_type = message_type
        self.rate_limit_seconds = rate_limit_seconds

class PluginMessageQueue(object):
    def __init__(self):
        self.type_queue_dictionary = {}

    def add(self, plugin_message):
        assert(isinstance(plugin_message, PluginMessage))
        # see if this is a new message type
        if plugin_message.message_type not in self.type_queue_dictionary:
            # create the new message queue item
            queue_type_item = {
                "rate_limit_seconds": plugin_message.rate_limit_seconds,
                "messages": deque(),
                "last_time_sent": 0,
                "num_rate_limited": 0,
                "num_sent": 0
            }
            self.type_queue_dictionary[plugin_message.message_type] = queue_type_item
        else:
            # the queue type exists, fetch it
            queue_type_item = self.type_queue_dictionary[plugin_message.message_type]
            # update the rate_limit_seconds in case it's changed
            queue_type_item["rate_limit_seconds"] = plugin_message.rate_limit_seconds

        # see if we should add this message to the queue
        message_queue = queue_type_item["messages"]
        assert(isinstance(message_queue, deque))
        # see if this message type has been rate limited
        if queue_type_item["rate_limit_seconds"] > 0:
            # update the number of messages we have rate limited
            queue_type_item["num_rate_limited"] += len(message_queue)
            # clear the current queue type since it was rate limited and we've received a newer message
            message_queue.clear()
        # append the message to the message queue for the message type
        message_queue.append(plugin_message)

    def get_messages_to_send(self):
        current_time = time.time()
        messages_to_send = []
        for queue_type in self.type_queue_dictionary.keys():
            current_queue = self.type_queue_dictionary[queue_type]
            messages = current_queue["messages"]
            if len(messages) > 0:
                # see if it's time to send
                if (
                    current_queue["rate_limit_seconds"] + current_queue["last_time_sent"] < current_time
                ):
                    # set the time last sent to the current time
                    current_queue["last_time_sent"] = current_time
                    # set the number of messages sent
                    current_queue["num_sent"] += len(messages)
                    # add all of the messages.  There really only should ever be 1 message in a rate limited
                    # queue according to the current implementation, but let's loop through just in case we change
                    # this.
                    while len(messages) > 0:
                        messages_to_send.append(messages.popleft())

        return messages_to_send


class MessengerWorker(Thread):
    def __init__(self, message_queue, plugin_manager, plugin_id, update_period_seconds=1):
        super(MessengerWorker, self).__init__()
        self._queue = message_queue
        self._plugin_manager = plugin_manager
        self.plugin_id = plugin_id
        self.update_period_seconds = update_period_seconds
        self.daemon = True
        self.lock = Lock()
        self.message_queue = PluginMessageQueue()

    def _send_messages(self, plugin_messages):
        for message in plugin_messages:
            if "type" not in message.message_data:
                message.message_data["type"] = message.message_type
            self._plugin_manager.send_plugin_message(self.plugin_id, message.message_data)

    # look for new plugin messages
    def run(self):
        while True:
            try:
                plugin_message = self._queue.get(timeout=self.update_period_seconds)
                assert(isinstance(plugin_message, PluginMessage))
                # add the message to the queue
                self.message_queue.add(plugin_message)
                # see if we should send any messages
                self._send_messages(self.message_queue.get_messages_to_send())
            except queue.Empty:
                pass
            except Exception as e:
                logger.exception("An unexpected exception occurred while sending message to the UI.")
