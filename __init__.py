import logging
import re
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.ext.dispatcher import run_async
from skybeard.beards import Beard


logger = logging.getLogger(__name__)

def drop_prefix(data):
    return data[3:]

class NamedVoteBeard(Beard):
    """Named voting for skybeard-2

    Type /nvtest to make test poll.
    Type /nvask to ask a specific yes/no question.
    """

    class YesNoQuestionEnum(Enum):
        ASKING = 1

    def initialise(self):
        self.disp.add_handler(CommandHandler("nvtest", self.test))

        # Conversation for a simple yes no question
        self.disp.add_handler(ConversationHandler(
            entry_points=[CommandHandler('nvask', self.ask_what)],
            states={
                self.YesNoQuestionEnum.ASKING: [MessageHandler(Filters.text, self.ask), ]
            },
            fallbacks=[CommandHandler('cancel', lambda x, y: ConversationHandler.END)]
        ))

        self.disp.add_handler(CallbackQueryHandler(self.update_quiz))

        self.yes_no_maybe = InlineKeyboardMarkup([
            [InlineKeyboardButton("a) Yes", callback_data='nvta)'),
             InlineKeyboardButton("b) No", callback_data='nvtb)')],
            [InlineKeyboardButton("c) Maybe", callback_data='nvtc)')],
        ])


    # YesNoQuestion code
    def ask_what(self, bot, update):
        update.message.reply_text("Sup. What's your question?")

        return self.YesNoQuestionEnum.ASKING

    def ask(self, bot, update):
        update.message.reply_text('{}\na)\nb)\nc)'.format(update.message.text), reply_markup=self.yes_no_maybe)

        return ConversationHandler.END

    def test(self, bot, update):
        update.message.reply_text('Please choose:\na)\nb)\nc)', reply_markup=self.yes_no_maybe)


    def add_name(self, text, name):
        if text[-1] == ")":
            return "{} {}".format(text, name)
        else:
            return "{}, {}".format(text, name)

    def remove_name(self, text, name):
        retval = re.sub(r"\s{},?".format(name), "", text)
        if retval[-1] == ",":
            retval = retval[:-1]
        retval = retval.strip()
        return retval


    def update_quiz(self, bot, update):
        query = update.callback_query

        text_as_list = query.message.text.split("\n")

        data = drop_prefix(query.data)
        full_name = "{} {}".format(query.from_user.first_name, query.from_user.last_name)
        for i in range(len(text_as_list)):
            if text_as_list[i][:2] == data:
                if full_name in text_as_list[i]:
                    text_as_list[i] = self.remove_name(text_as_list[i], full_name)
                else:
                    text_as_list[i] = self.add_name(text_as_list[i], full_name)

        new_text = "\n".join(text_as_list)

        # TODO set up to take the keyboard from the query
        bot.editMessageText(text=new_text,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=self.yes_no_maybe)
