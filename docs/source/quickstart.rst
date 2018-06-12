
Quickstart
==========

You can install the Détaché from PyPI: ::

    $ pip install detache

.. currentmodule:: detache


Basics
------

Détaché uses decorators to convert functions to commands.

Commands are declared through :func:`detache.command`, and arguments are added with :func:`detache.argument`. ::

    @detache.command("hi", description="Says hi to someone")
    @detache.argument("user", type_=detache.User, help="User to say hi to")
    async def say_hi(self, ctx, user):
        await ctx.send("Hi, " + user.mention + "!")

Command decorators are placed in front of the function and any arguments. The name passed will be a how a user calls
the command, and an optional description can be passed as well.

Argument decorators are placed in the order they'll be used.

Plugins
-------

Plugins are used to organize commands into groups. Plugins are created by inheriting a class from
:class:`detache.Plugin`. The :func:`detache.Bot.plugin` decorator should be placed before it with the name of the
plugin. ::

    import detache

    bot = detache.Bot()

    @bot.plugin("Example")
    class ExamplePlugin(detache.Plugin)
        """Example Description used when documenting plugins and commands"""

Plugins can also be split across multiple files. For the plugin to work, you have to import and register it to the bot. ::

    import detache

    from plugins.example import ExamplePlugin

    bot = detache.Bot()

    bot.register_plugin(ExamplePlugin, name="Example")

Background Tasks
----------------

Détaché also supports background tasks, which are run when the bot connects to Discord. If the bot loses connection,
the task will be cancelled and restart when the bot reconnects.

Similar to commands, the :func:`detache.background_task` decorator is used to declare a background task. ::

    @detache.background_task("say_hi")
    async def hi(self):
        # Say hi every 5 seconds.

        while True:
            for guild in self.bot.guilds:
                for channel in guild.channels:
                    await channel.send("Hi!")

            await asyncio.sleep(5)

Event Listeners
---------------

An important feature of Détaché is that a provides a high level API while still giving access to the underlying
events. Using event listeners, you can add a callback function to any
`discord.py event <http://discordpy.readthedocs.io/en/rewrite/api.html#event-reference>`_ through the
:func:`detache.event_listener` decorator.

This event listener listens for any "on_message_delete" events. ::

    @detache.event_listener("on_message_delete")
    async def undelete(self, message):
        await message.channel.send(
            "{} said {!r} at {}".format(message.author.mention, message.content, message.created_at)
        )
