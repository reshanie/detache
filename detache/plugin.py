# Copyright (c) 2018 James Patrick Dill
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import discord

from detache.command import CommandInherit
from detache.wrappers import EventListenerInherit, BgTaskInherit


class Plugin:
    """
    Plugin class. Create your own plugins by inheriting this class.
    """

    __plugin_name__ = "Plugin"

    def __init__(self, bot):
        #: Bot the plugin belongs to
        self.bot = bot

        #: aiohttp.ClientSession to be used for any HTTP requests
        self.http = self.bot.http_session

        self.log = self.bot.log

        self.commands = self.find_commands()
        self.event_listeners = self.find_event_listeners()
        self.bg_tasks = self.find_bg_tasks()

    def __repr__(self):
        return "Plugin({!r})".format(self.__plugin_name__)

    def find_commands(self):
        """Returns dict of commands."""

        self.log.debug("finding commands in {!r}".format(self))

        commands = {}

        for name in dir(self):
            o = getattr(self, name)
            if issubclass(o.__class__, CommandInherit):  # check for command objects
                o.plugin = self
                commands[o.name] = o

                self.log.debug("found command: {!r}".format(o.name))

        return commands

    def find_event_listeners(self):
        """Returns dict of event listeners."""

        self.log.debug("finding event listeners in {!r}".format(self))

        listeners = {}
        # example:
        # {
        #     "on_message": [<func>, <func>],
        #     "on_message_delete": [<func>]
        # }

        for name in dir(self):
            o = getattr(self, name)
            if issubclass(o.__class__, EventListenerInherit):  # check for command objects
                if o.event not in listeners:
                    listeners[o.event] = []

                listeners[o.event].append(o)

                self.log.debug("found event listener")

        return listeners

    def find_bg_tasks(self):
        """Returns dict of background tasks."""

        self.log.debug("finding background tasks in {!r}".format(self))

        tasks = {}

        for name in dir(self):
            o = getattr(self, name)
            if issubclass(o.__class__, BgTaskInherit):  # check for command objects
                tasks[o.id] = o

                self.log.debug("found background task: {!r}".format(o.id))

        return tasks

    def create_task(self, *args, **kwargs):
        """
        Shortcut to :meth:`Plugin.bot.loop.create_task`

        Call this on a coroutine to run it without blocking.

        :returns: asyncio.Task
        """

        return self.bot.loop.create_task(*args, **kwargs)

    # event pre-processing, command handling

    async def __on_event__(self, event, *args, **kwargs):
        # triggers event listeners

        for listener in self.event_listeners.get(event, []):  # empty list if no event listeners
            self.create_task(listener.execute(self, *args, **kwargs))  # use plugin as self arg

            self.log.debug("{!r} event listener triggered".format(event))

    async def __on_ready__(self):
        for task in self.bg_tasks.values():
            task.restart(self.bot.loop, self)

    async def __on_shard_ready__(self):
        pass

    async def __on_message__(self, message):
        pass
