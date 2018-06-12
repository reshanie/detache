
.. currentmodule:: detache

Arguments
=========

.. autofunction:: argument

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


