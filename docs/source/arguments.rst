
.. currentmodule:: detache

Arguments
=========

.. autofunction:: argument

Détaché supports several argument types:

- :class:`detache.String` - String of text. Can be multi-word if surrounded with double quotes
- :class:`detache.Number` - Integer or float
- :class:`detache.User` - `discord.py member object <http://discordpy.readthedocs.io/en/rewrite/api.html#user>`_. Can be passed as a mention or username#1234
- :class:`detache.Channel` - `discord.py channel object <discordpy.readthedocs.io/en/rewrite/api.html#textchannel>`_.

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

Variadic Arguments
------------------

Variadic arguments allow an argument to be passed a specific or unlimited number of times. This is set with the `nargs`
parameter. If this is set to -1, an unlimited number of arguments is accepted.

Variadic arguments are passed to the underlying function as a list.

Example: ::

    @detache.command("add", "Variadic argument test that adds numbers.")
    @detache.argument("addends", detache.Number, nargs=-1, help="Addends")
    async def add_cmd(self, ctx, addends):
        return sum(addends)

If `nargs` is -1, then setting `required=False` will allow the argument to not be passed at all. Otherwise, the
argument must be passed at least once.
