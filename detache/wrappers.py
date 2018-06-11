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


# used for detection by plugin
class EventListenerInherit:
    pass


def event_listener(event, one_task=False):
    """
    Event listener decorator. Calls function every time the given event occurs, with the respective arguments.

    :param event: Event to listen for.
    :param bool one_task: (Optional) If True, this will check if the event listener is already running when it's called.
                          If so, the running task is cancelled.
    """

    # class wraps the callback function
    # class is detected by plugin and plugin triggers the event listener
    class EventListener(EventListenerInherit):
        def __init__(self, func):
            self.func = func
            self.event = event

            self.one_task = one_task

            self.task = None

        async def execute(self, *args, **kwargs):
            if self.one_task and self.task is not None and not self.task.done():  # check if old task still runnning
                self.task.cancel()

            self.task = await self.func(*args, **kwargs)

    return EventListener


# used for detection by plugin
class BgTaskInherit:
    pass


def background_task(id):
    """
    Background task decorator. Runs a coroutine in the background when the bot connects to Discord.

    :param id: Arbitrary id for the background task.
    """

    # wrapper class
    class BgTask(BgTaskInherit):
        def __init__(self, func):
            self.id = id

            self.func = func
            self.task = None

        def start(self, loop, self_):
            self.task = loop.create_task(self.func(self_))

        def cancel(self):
            if self.task is not None and not self.task.done():
                self.task.cancel()

        def restart(self, loop, self_):
            self.cancel()
            self.start(loop, self_)

    return BgTask
