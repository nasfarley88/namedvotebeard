import logging
import re
import string
from functools import partial

try:
    import dill as pickle
except ImportError:
    import pickle

import telepot
import telepot.aio
from telepot import glance
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from skybeard.beards import BeardChatHandler, ThatsNotMineException
from skybeard.decorators import onerror
from skybeard.utils import get_args
from skybeard.predicates import regex_predicate
from skybeard.bearddbtable import BeardDBTable

from .utils import get_user_name, make_reply_prefix

logger = logging.getLogger(__name__)


class NamedVoteBeard(BeardChatHandler):

    __userhelp__ = """Named voting for skybeard-2."""

    __commands__ = [
        (regex_predicate("_test"), 'test', "Ask a test question"),
        ('voteyesno', 'ask_question',
         "Ask a yes/no question. 0 args: ask for question."
         " 1+ args, uses args as question."),
        ("voteany", "vote_any", "Ask anything! 2 args: [question] [options]"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.test = partial(self.vote_any,
                            question="Test question?",
                            responses=["Yes", "No", "Foo bar?"])
        self.ask_question = partial(self.vote_any,
                                    responses=["Yes", "No", "Maybe"])
        self.messages_table = BeardDBTable(self, "messages")

    async def make_keyboard(self, items):
        """Creates keyboard for a given iterable of strings."""
        # TODO make this support rows of 2 if the question replies are small
        # enough
        inline_keyboard = []
        for item_ind, info in enumerate(items):
            prefix = make_reply_prefix(item_ind)
            button = {
                'text': "{} {}".format(prefix, info.strip()),
                'callback_data': self.serialize(prefix),
            }

            inline_keyboard.append([InlineKeyboardButton(**button)])

            keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        return keyboard

    @onerror("Sorry, something went wrong. Perhaps too few arguments?")
    async def vote_any(self, msg=None, question=None, responses=None):
        """Post a named vote message with arbitrary question/responses."""
        if msg is not None:
            args = get_args(msg['text'])
        if question is None:
            question = args[0]
        if responses is None:
            responses = [x.strip() for x in args[1:]]
        keyboard = await self.make_keyboard(responses)
        text = "{}\n{}".format(question,
                               "\n".join([string.ascii_letters[x]+")"
                                          for x in range(len(responses))]))
        msg = await self.sender.sendMessage(text, reply_markup=keyboard)
        with self.messages_table as table:
            table.insert(dict(msg_id=msg['message_id'],
                              msg=pickle.dumps(msg),
                              keyboard=pickle.dumps(responses)))

    async def on_callback_query(self, msg):
        query_id, from_id, query_data = glance(msg, flavor='callback_query')
        try:
            data = self.deserialize(query_data)
        except ThatsNotMineException:
            return

        name = get_user_name(msg['from'])

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

        with self.messages_table as table:
            entry = table.find_one(msg_id=msg['message']['message_id'])

        await self.bot.editMessageText(
             telepot.origin_identifier(msg),
             text=new_text,
             reply_markup=await self.make_keyboard(
                 pickle.loads(entry['keyboard'])))

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
