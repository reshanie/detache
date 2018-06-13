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

import discord

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
        if raw[0] == raw[-1] == '"':
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
        else:
            user_id = int(re.search("[0-9]+", raw)[0])
            member = ctx.guild.get_member(user_id)

        if member is None:
            raise errors.ParsingError("{} isn't a member of {}.".format(raw, ctx.guild))

        return member


class Channel(Any):
    pattern = r'(<#([0-9]+)>|#.{1,255})'

    @classmethod
    def convert(cls, ctx, raw):
        # if starts with "#", name of channel was passed.
        if raw.startswith("#"):
            name = raw[1:]

            channel = discord.utils.get(ctx.guild.text_channels, name=name)
        else:
            channel_id = int(re.search("[0-9]+", raw)[0])

            channel = discord.utils.get(ctx.guild.text_channels, id=channel_id)

        if channel is None:
            raise errors.ParsingError("{} isn't a channel in {}.".format(raw, ctx.guild))

        return channel


class Role(Any):
    pattern = r'(<@&[0-9]+>|"[^\n]+"|[^ \n]+)'

    @classmethod
    def convert(cls, ctx, raw):
        # if starts with "<@&", role mention was passed.
        if raw.startswith("<@&") and raw.endswith(">"):
            role_id = int(re.search("[0-9]+", raw)[0])

            role = discord.utils.get(ctx.guild.roles, id=role_id)
        else:
            name = raw

            if name[0] == name[-1] == '"':  # multi word, remove quotes
                name = name[1:-1]

            role = discord.utils.get(ctx.guild.roles, name=name)

        if role is None:
            raise errors.ParsingError("{} isn't a role in {}.".format(raw, ctx.guild))

        return role


# argument decorator

def argument(name, type=None, default=None, required=True, nargs=1, help=None):
    """
    Command argument.

    :param name: Name of the argument. Should match one of the function's arguments.
    :param type: (Optional) Argument type. Leave as None to accept any type.
    :param default: (Optional) Default value.
    :param required: (Optional) Whether the argument is required. Defaults to True
    :param nargs: (Optional) Number of times the argument can occur. Defaults to 1. -1 allows unlimited arguments.
    :param help: (Optional) Argument description.

    If nargs is anything other than 1, the parsed argument will be returned as a list.
    """

    if nargs not in (1, -1) and not required:
        raise ValueError("nargs must = 1 or -1 for arguments that aren't required")

    type = type or Any  # default ArgumentType class accepts anything as valid argument

    class Argument:
        @classmethod
        def no_match_error(cls):
            if nargs == 1:
                raise errors.ParsingError(
                    "**{}** is a required {}.".format(name, type.__name__.lower())
                )
            else:
                raise errors.ParsingError(
                    "**{}** are required.".format(name + ("" if name.endswith("s") else "s"))  # use plural
                )

        @classmethod
        def consume(cls, ctx, args):
            """
            Parses an argument from an argument string, and returns the argument string with this argument consumed.

            :return: parsed, argString
            """

            parsed, args = type.consume(ctx, args)  # use argument type's parsing function

            if parsed is NoMatch:  # argument is wrong type or not found
                if required or nargs != 1:
                    cls.no_match_error()
                else:
                    parsed = default

            return parsed, args

    Argument.name = name
    Argument.help = help
    Argument.type_ = type
    Argument.nargs = nargs
    Argument.required = required

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


def command(name, description=None, required_permissions=None):
    """
    Command decorator. Put this before a command and its arguments.

    :param str name: Name of command
    :param str description: Description of commands
    :param list[str] required_permissions: (Optional) Permissions required to use command
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
                arg_name = arg.type_.__name__ + ("(s)" if arg.nargs != 1 else "")

                doc += "• {} **{}**".format(arg_name, arg.name)

                if arg.help is not None:
                    doc += " - {}".format(arg.help)

                doc += "\n"

            doc += "\n" + self.description

            return doc

        async def process(self, ctx, content):
            # process given arguments and run the command

            # check for required permissions before parsing
            if required_permissions is not None:
                author_perms = ctx.author.permissions_in(ctx.channel)

                for perm in required_permissions:
                    # check permission. if not specified in permissions, assume False
                    if not getattr(author_perms, perm, False):
                        raise errors.MissingPermissions("This command requires the `{}` permission.".format(perm))

            parsed_args = {}

            try:
                for arg in self.args:
                    # parse argument and update with what's left of argument string

                    if arg.nargs == 1:  # only 1 arg
                        parsed, content = arg.consume(ctx, content)

                        parsed_args[arg.name] = parsed

                    elif arg.nargs == -1:  # any number of args
                        parsed = []

                        while True:
                            try:
                                value, content = arg.consume(ctx, content)

                                parsed.append(value)
                            except errors.ParsingError as e:  # no more args
                                if len(parsed) == 0 and arg.required:
                                    # must pass at least one arg if it's required
                                    raise e

                                break

                        parsed_args[arg.name] = parsed
                    else:
                        parsed = []

                        for i in range(arg.nargs):  # limit to nargs
                            try:
                                value, content = arg.consume(ctx, content)

                                parsed.append(value)
                            except errors.ParsingError:  # no more args
                                break

                        parsed_args[arg.name] = parsed

            except errors.ParsingError as e:
                raise errors.ParsingError("{}\n\n{}".format(e, self.make_doc(ctx.prefix)))

            reply = await self.func(ctx.plugin, ctx, **parsed_args)

            if reply:
                await ctx.send(reply)

    return Command
