
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

Argument decorators are placed in the order they'll be used. The name should match a parameter in the function (in this
example, it's "user"). A type can be passed to parse the argument. If no type is given, anything can be used.

Détaché supports several argument types:

- :class:`detache.String` - String of text. Can be multi-word if surrounded with double quotes
- :class:`detache.Number` - Integer or float
- :class:`detache.User` - `discord.py member object <http://discordpy.readthedocs.io/en/rewrite/api.html#user>`_. Can be passed as a mention or username#1234

Custom types can also be created by inheriting from :class:`detache.Any`. This type takes a hexadecimal number and
converts it to an int, for example: ::

    class Hex(detache.Any):
        # arguments are parsed using regex patterns
        pattern = "(0x)?[0-9a-f]+"

        @classmethod
        def convert(cls, ctx, raw):
            # a context object and the raw argument are passed for conversion

            # remove 0x
            if raw.startswith("0x"):
                raw = raw[2:]

            return int(raw, base=16)  # return the converted argument


