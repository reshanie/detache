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

import logging
import discord
import aiohttp

from detache.command import Context
from detache import errors

import inspect

default_log = logging.getLogger("outlet")


class Bot(discord.Client):
    """
    Bot class. All of the code for your bot is written in plugins then registered with the bot.

    :keyword str default_prefix: (Optional) Default bot prefix. This can be overrided for per-server prefixes.
    :keyword logger: Logging object. The Detache log is used by default.
    """

    def __init__(self, *, default_prefix="!", logger=default_log):
        super().__init__()

        self.log = logger

        self.http_session = aiohttp.ClientSession()

        self.default_prefix = default_prefix

        async def get_prefix(guild):
            return self.default_prefix

        self.get_prefix = get_prefix

        self.plugins = []

        self.commands = {}

    def register_plugin(self, plugin, name=None):
        """
        Registers plugin to the bot.

        :param plugin: Plugin class. Must inherit :class:`detache.Plugin`
        :param str name: (Optional) Name of the plugin.
        """

        plugin = plugin(self)  # init plugin

        self.plugins.append(plugin)  # add to list
        self.commands.update(**plugin.commands)  # add commands to dict

    def plugin(self, name=None):
        """
        Plugin decorator for use in single file bots. Put this decorator before a plugin class for it to be registered
        automatically.

        :param str name: (Optional) Name of the plugin.
        """

        def decorator(plugin):
            self.register_plugin(plugin, name=name)

        return decorator

    def prefix(self, func):
        """
        To use a different command prefix for every guild your bot is in, put this decorator on a function that takes a
        :class:`discord.Guild` and returns the bot prefix. For example ::

            bot = detache.Bot()

            @bot.prefix()
            def get_prefix(ctx):
                # search for prefix in database
                # if not found, fallback to "!"

                return Prefixes.filter(guild_id=ctx.guild.id).first() or "!"

        If the get_prefix function returns None, the default prefix will be used instead.

        This decorator can be used on functions or coroutines.
        """

        async def get_prefix(guild):
            # use await if the get_prefix function is a coroutine
            if inspect.iscoroutine(func) or inspect.iscoroutinefunction(func):
                return await func(guild) or self.default_prefix
            else:
                return func(guild) or self.default_prefix

        # update with new func
        self.get_prefix = get_prefix

    # event handling

    async def on_message(self, message):
        if isinstance(message.channel, discord.TextChannel) and message.author != self.user:
            # happened in a guild, could be a command

            prefix = await self.get_prefix(message.guild)

            content = message.content
            if content.startswith(prefix) and content != prefix:
                self.log.debug("command called: {!r}".format(message.content))

                split = content[len(prefix):].split(" ")  # remove prefix, split up args and command

                cmd = split[0]
                args = " ".join(split[1:]) if len(split) > 0 else ""  # put args back together

                # check if command exists
                if cmd in self.commands:
                    command_object = self.commands[cmd]

                    # create command context
                    ctx = Context(command_object.plugin, message, prefix)

                    # attempt command
                    try:
                        await command_object.process(ctx, args)
                    except errors.CommandError as e:  # parsing error, i.e. wrong arg type
                        await message.channel.send(e)
                else:
                    # command does not exist!!
                    await message.channel.send("{}**{}** isn't a command.".format(prefix, cmd))

        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_message", message))
            self.loop.create_task(plugin.__on_message__(message))

    async def on_ready(self):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_ready"))
            self.loop.create_task(plugin.__on_ready__())

    async def on_shard_ready(self):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on__shard_ready"))
            self.loop.create_task(plugin.__on_shard_ready__())

    # passthrough

    async def on_typing(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_typing", *args, **kwargs))

    # messages

    async def on_message_delete(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_message_delete", *args, **kwargs))

    async def on_raw_message_delete(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_raw_message_delete", *args, **kwargs))

    async def on_message_edit(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_message_edit", *args, **kwargs))

    # reactions

    async def on_reaction_add(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_reaction_add", *args, **kwargs))

    async def on_reaction_remove(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_reaction_remove", *args, **kwargs))

    async def on_reaction_clear(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_reaction_clear", *args, **kwargs))

    # private channels

    async def on_private_channel_delete(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_private_channel_delete", *args, **kwargs))

    async def on_private_channel_create(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_private_channel_create", *args, **kwargs))

    async def on_private_channel_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_private_channel_update", *args, **kwargs))

    # guild channels

    async def on_guild_channel_delete(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_channel_delete", *args, **kwargs))

    async def on_guild_channel_create(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_channel_create", *args, **kwargs))

    async def on_guild_channel_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_channel_update", *args, **kwargs))

    # members

    async def on_member_join(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_member_join", *args, **kwargs))

    async def on_member_remove(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_member_remove", *args, **kwargs))

    async def on_member_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_member_update", *args, **kwargs))

    async def on_member_ban(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_member_ban", *args, **kwargs))

    async def on_member_unban(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_member_unban", *args, **kwargs))

    # guilds

    async def on_guild_join(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_join", *args, **kwargs))

    async def on_guild_remove(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_remove", *args, **kwargs))

    async def on_guild_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_update", *args, **kwargs))

    # roles

    async def on_guild_role_create(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_role_create", *args, **kwargs))

    async def on_guild_role_delete(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_role_delete", *args, **kwargs))

    async def on_guild_role_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_role_update", *args, **kwargs))

    # emojis

    async def on_guild_emojis_update(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_emojis_update", *args, **kwargs))

    # guild availability

    async def on_guild_available(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_available", *args, **kwargs))

    async def on_guild_unavailable(self, *args, **kwargs):
        for plugin in self.plugins:
            self.loop.create_task(plugin.__on_event__("on_guild_unavailable", *args, **kwargs))
