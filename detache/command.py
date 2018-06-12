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

import inspect
import re

from detache import errors


class Context(object):
    """
    Command context, passed to command functions for easier handling

    :attr discord.Message message: Message
    :attr discord.Guild guild: Guild the message was sent in
    :attr discord.Channel channel: Channel the message was sent in
    :attr discord.Member: author: Author of the message
    """

    def __init__(self, plugin, message, prefix=""):
        self.plugin = plugin

        self.message = message

        self.guild = message.guild
        self.channel = message.channel
        self.author = message.author

        self.prefix = prefix

    async def send(self, *args, **kwargs):
        """
        Coroutine

        Sends a message in the context's channel. Pass the same arguments or keywords that you would to
        :meth:`discord.Channel.send`
        """

        await self.channel.send(*args, **kwargs)


# empty class returned when an type doesn't match
class NoMatch:
    pass


# argument types

class Any:
    pattern = "[^ ]+"

    @classmethod
    def convert(cls, ctx, raw):
        """
        Converts string argument to specified type.

        :param ctx: Context.
        :param str raw: Raw passed argument.
        """

        return raw

    @classmethod
    def consume(cls, ctx, args):
        """
        Parses an argument from an argument string, and returns the argument string with this argument consumed.

        :return: parsed, argString
        """

        match = re.match(cls.pattern, args, flags=re.IGNORECASE)

        if match:
            match = match[0]

            parsed = cls.convert(ctx, match)

            span = len(match)
            if span >= len(args):
                return parsed, ""

            return parsed, args[span + 1:]  # remove this argument from arguments string

        else:
            return NoMatch, args


class String(Any):
    pattern = r'("[^\n]+"|[^ \n]+)'

    @classmethod
    def convert(cls, ctx, raw):
        # if the string is multi-word, it is surrounded in quotes. remove them
        if " " in raw:
            return raw[1:-1]

        return raw


class Number(Any):
    pattern = "\d+(\.\d+)?"

    @classmethod
    def convert(cls, ctx, raw):
        try:
            if "." in raw:
                return float(raw)
            else:
                return int(raw)

        except ValueError:
            raise errors.WrongType("{!r} is not a number.".format(raw))


class User(Any):
    pattern = "(<@!?([0-9]+)>|.{2,32}#[0-9]{4})"

    @classmethod
    def convert(cls, ctx, raw):
        # if contains "#", user tag was passed. otherwise, mention
        if "#" in raw:
            member = ctx.guild.get_member_named(raw)

            if member is None:
                raise errors.ParsingError("{} isn't a member of {}.".format(raw, ctx.guild))

            return member
        else:
            user_id = int(re.search("[0-9]+", raw)[0])
            member = ctx.guild.get_member(user_id)

            if member is None:
                raise errors.ParsingError("{} isn't a member of {}.".format(raw, ctx.guild))

            return member


# argument decorator

def argument(name, type=None, default=None, help=None, required=True):
    """
    Command argument.

    :param name: Name of the argument. Should match one of the function's arguments.
    :param type: (Optional) Argument type. Leave as None to accept any type.
    :param default: (Optional) Default value.
    :param help: (Optional) Argument description.
    :param required: (Optional) Whether the argument is required. Defaults to True
    """

    type = type or Any  # default ArgumentType class accepts anything as valid argument

    class Argument:
        @classmethod
        def consume(cls, ctx, args):
            """
            Parses an argument from an argument string, and returns the argument string with this argument consumed.

            :return: parsed, argString
            """

            parsed, args = type.consume(ctx, args)  # use argument type's parsing function

            if parsed is NoMatch:  # argument is wrong type or not found
                if required:
                    raise errors.ParsingError(
                        "**{}** is a required {}.".format(name, type.__name__.lower())
                    )
                else:
                    parsed = default

            return parsed, args

    Argument.name = name
    Argument.help = help
    Argument.type_ = type

    # actual decorator
    def add_argument(func):
        if hasattr(func, "cmd_args"):
            func.cmd_args.append(Argument)  # add to command function's arg list
        else:
            func.cmd_args = [Argument]  # arg list doesnt exist, create it

        return func

    return add_argument


# used to check plugin for commands
class CommandInherit:
    pass


def command(name, description=None):
    """
    Command decorator. Put this before a command and its arguments.
    """

    class Command(CommandInherit):
        def __init__(self, func):
            self.name = name
            self.description = description or inspect.cleandoc(inspect.getdoc(func))

            self.args = list(reversed(getattr(func, "cmd_args", [])))  # fix order of arguments

            self.func = func

            self.__doc__ = self.make_doc()

        def __repr__(self):
            return "Command({!r})".format(self.name)

        def make_doc(self, prefix=""):
            doc = "{}**{}** ".format(prefix, self.name) + " ".join([arg.name for arg in self.args]) + "\n\n"  # syntax

            # list arg types, names, descriptions
            for arg in self.args:
                doc += "• {} **{}**".format(arg.type_.__name__, arg.name)

                if arg.help is not None:
                    doc += " - {}".format(arg.help)

                doc += "\n"

            doc += "\n" + self.description

            return doc

        async def process(self, ctx, content):
            """
            Process given arguments and run the command. This doesn't include checking the prefix and command name,
            the bot handles that.
            """
            parsed_args = {}

            try:
                for arg in self.args:
                    # parse argument and update with what's left of argument string
                    parsed, content = arg.consume(ctx, content)

                    parsed_args[arg.name] = parsed
            except errors.ParsingError as e:
                raise errors.ParsingError("{}\n\n{}".format(e, self.make_doc(ctx.prefix)))

            reply = await self.func(ctx.plugin, ctx, **parsed_args)

            if reply:
                await ctx.send(reply)

    return Command
