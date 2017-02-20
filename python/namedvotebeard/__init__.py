import logging
import re
import string

import dataset
#import yaml
import pickle

import telepot
import telepot.aio
from telepot import glance
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from skybeard.beards import BeardChatHandler, ThatsNotMineException
from skybeard import utils, decorators

logger = logging.getLogger(__name__)


def get_args(msg):
    return msg['text'].split(" ")[1:]

DB_NAME = "sqlite:///namedvotebeard.db"

class BeardDBTable(object):
    """Placeholder class for getting a table."""

    def __init__(self, beard, table_name):
        self.beard = beard
        self.table_name = beard.get_name()+"_"+table_name

    def __enter__(self):
        self.db = dataset.connect(DB_NAME)
        self.table = self.db[self.table_name]
        return self.table

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.commit()
        del self.db
        del self.table
        return

class NamedVoteBeard(BeardChatHandler):

    __userhelp__ = """Named voting for skybeard-2."""

    __commands__ = [
        ('nvtest', 'test', "Ask a test question"),
        ('voteyesno', 'ask_question',
         "Ask a yes/no question. 0 args: ask for question."
         " 1+ args, uses args as question."),
        ("voteany", "vote_any", "Ask anything! 2 args: [question] [options]"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    async def make_keyboard(self, items):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="{}) {}".format(string.ascii_letters[prefix], info.strip()),
                                      callback_data=self.serialize(string.ascii_letters[prefix]+")"))]
                for prefix, info in enumerate(items)])

        return keyboard

    @decorators.onerror("Sorry, something went wrong. Perhaps too few arguments?")
    async def vote_any(self, msg):
        args = utils.get_args(msg['text'])
        items = [x.strip() for x in args[1].split(",")]
        keyboard = await self.make_keyboard(items)
        text = "{}\n{}".format(args[0],
                               "\n".join([string.ascii_letters[x]+")" for x in range(len(items))]))
        msg = await self.sender.sendMessage(text, reply_markup=keyboard)
        with BeardDBTable(NamedVoteBeard, "messages") as table:
            table.insert(dict(msg_id=msg['message_id'], msg=pickle.dumps(msg), keyboard=pickle.dumps(items)))

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

        if 'last_name' in msg['from']:
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
        #await self.bot.editMessageText(
        #    telepot.origin_identifier(msg),
        #    text=new_text,
        #    reply_markup=self.yes_no_maybe)
        self.logger.debug(str(msg))
        with BeardDBTable(NamedVoteBeard, "messages") as table:
            entry = table.find_one(msg_id=msg['message']['message_id'])

        await self.bot.editMessageText(
             telepot.origin_identifier(msg),
             text=new_text,
             reply_markup=await self.make_keyboard(pickle.loads(entry['keyboard'])))

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
