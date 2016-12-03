import logging
import re

import telepot
import telepot.aio
from telepot import glance
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from skybeard.beards import BeardAsyncChatHandlerMixin, ThatsNotMineException

logger = logging.getLogger(__name__)


def get_args(msg):
    return msg['text'].split(" ")[1:]


class NamedVoteBeard(telepot.aio.helper.ChatHandler,
                     BeardAsyncChatHandlerMixin):

    __userhelp__ = """Named voting for skybeard-2

· Type /nvtest to make test poll.
· Type /nvask to ask a specific yes/no question. Optionally, provide the question directly to /nvask as:
    <code>/nvask Is it sleeping?</code>
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_command("nvtest", self.test)
        self.register_command("nvask", self.ask_question)

        self.yes_no_maybe = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="a) Yes",
                    callback_data=self.serialize('a)')),
                 InlineKeyboardButton(
                     text="b) No",
                     callback_data=self.serialize('b)'))],
                [InlineKeyboardButton(
                    text="c) Maybe",
                    callback_data=self.serialize('c)'))],
            ])

    async def _post_quiz(self, text, reply_markup):
        await self.sender.sendMessage(
            '{}\na)\nb)\nc)'.format(text),
            reply_markup=reply_markup)

    async def ask_question(self, msg):
        args = get_args(msg)
        if args:
            await self._post_quiz(
                text=" ".join(args),
                reply_markup=self.yes_no_maybe)
        else:
            await self.sender.sendMessage("Sup. What's the question?")
            query_msg = await self.listener.wait()
            await self._post_quiz(
                text=query_msg['text'],
                reply_markup=self.yes_no_maybe)

    async def test(self, msg):
        await self._post_quiz(
            text="Select an answer:",
            reply_markup=self.yes_no_maybe)

    async def on_callback_query(self, msg):
        query_id, from_id, query_data = glance(msg, flavor='callback_query')
        try:
            data = self.deserialize(query_data)
        except ThatsNotMineException:
            return

        if msg['from']['last_name']:
            name = "{} {}".format(
                msg['from']['first_name'], msg['from']['last_name'])
        else:
            name = msg['from']['first_name']

        text_as_list = msg['message']['text'].split("\n")
        for i in range(len(text_as_list)):
            if text_as_list[i][:2] == data:
                if name in text_as_list[i]:
                    text_as_list[i] = await self.remove_name(
                        text_as_list[i], name)
                else:
                    text_as_list[i] = await self.add_name(
                        text_as_list[i], name)

        new_text = "\n".join(text_as_list)

        # TODO set up to take the keyboard from the query
        await self.bot.editMessageText(
            telepot.origin_identifier(msg),
            text=new_text,
            reply_markup=self.yes_no_maybe)

    async def add_name(self, text, name):
        if text[-1] == ")":
            return "{} {}".format(text, name)
        else:
            return "{}, {}".format(text, name)

    async def remove_name(self, text, name):
        retval = re.sub(r"\s{},?".format(name), "", text)
        if retval[-1] == ",":
            retval = retval[:-1]
        retval = retval.strip()
        return retval
