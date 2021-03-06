import cmd
import db
import logging
import argparse
import re

import transaction
import account
import util

logger = util.get_logger("jnab")


class ArgumentParserError(Exception):
    pass


class JnabArgparser(argparse.ArgumentParser):

    # Override the exit function to only throw error instead of exiting
    def exit(self, status=0, message=None):
        logger.info("JnabArgparser exit method called: (%d) %s" %
                (status, message))
        raise ArgumentParserError(message)

    # Override the error function to only throw error instead of calling exit
    # and avoid double printing error message
    def error(self, message):
        logger.info("JnabArgparser error method called: %s" % message)
        raise ArgumentParserError(message)


# Argument checking function for account.Currency
def arg_type_account_currency(line):
    logger.debug("arg_type_account_currency: entry")
    msg = ""
    if type(line) is not str:
        msg = "%r is not a string!" % line
        logger.error(msg)
    elif not hasattr(account.Currency, line.upper()):
        msg = "%r is not a valid account currency" % line
        logger.error(msg)
    if msg:
        raise argparse.ArgumentTypeError(msg)
    logger.debug("arg_type_account_currency: exit")
    return line


# Argument checking function for account.Type
def arg_type_account_type(line):
    logger.debug("arg_type_account_type: entry")
    msg = ""
    if type(line) is not str:
        msg = "%r is not a string!" % line
        logger.error(msg)
    elif not hasattr(account.Type, line.upper()):
        msg = "%r is not a valid account type" % line
        logger.error(msg)
    if msg:
        raise argparse.ArgumentTypeError(msg)
    logger.debug("arg_type_account_type: exit")
    return line


class JnabShell(cmd.Cmd):

    def preloop(self):
        self.database = db.DB(db.DEFAULT_DB_FILENAME, create_new=True)
        self.curr_account = None

        # new account parser
        self.do_new_parser = JnabArgparser(
                description="Argument parser for new account command")
        self.do_new_parser.add_argument(
                "-n",
                "--name",
                type=str,
                required=True)
        self.do_new_parser.add_argument(
                "-t",
                "--type",
                type=arg_type_account_type,
                required=True)
        self.do_new_parser.add_argument(
                "-c",
                "--currency",
                type=arg_type_account_currency,
                required=True)

        # add transaction parser
        self.do_add_parser = JnabArgparser(
                description="Argument parser for add transaction command")
        self.do_add_parser.add_argument(
                "-n",
                "--name",
                type=str,
                required=True)
        self.do_add_parser.add_argument(
                "-a",
                "--amount",
                type=int,
                required=True)
        self.do_add_parser.add_argument(
                "-d",
                "--date",
                type=str,
                required=False)
        self.do_add_parser.add_argument(
                "-b",
                "--budget",
                type=str,
                required=False)
        self.do_add_parser.add_argument(
                "-t",
                "--transfer",
                action="store_true",
                required=False)
        self.do_add_parser.add_argument(
                "-c",
                "--clear",
                action='store_true',
                required=False)

    @classmethod
    def split_line(self, line):
        return re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', line)

    """
    List all active accounts and their ID
    """
    def do_ls(self, line):
        # TODO: Add a verbose mode to show deactivated accouts too
        account_list = self.database.get_all_accounts()
        for account in account_list:
            if account.ACTIVE:
                if account == self.curr_account:
                    print("* %s" % str(account))
                else:
                    print("  %s" % str(account))

    def help_ls(self):
        print("List out all active accounts")

    def _get_account(self, line):
        # This should always be true from cmd module
        assert type(line) is str

        name = None
        id = None

        if line.isdigit():
            id = int(line)
        elif line.isprintable():
            name = line

        try:
            return self.database.get_account(account_id=id, account_name=name)
        except db.DBAccountLookupError as e:
            # Determine if using account NAME or ID for selection
            print("Invalid account info, unable to find account %s" % line)
            return None

    """
    Select an account to work on
    """
    def do_sel(self, line):
        account = self._get_account(line)
        if account:
            print(str(account))
            self.curr_account = account
        else:
            return False

    def help_sel(self):
        print("Select a current working account")
        print("sel <ID|NAME>")

    """
    Create new account
    """
    def do_new(self, line):
        argv = self.split_line(line)
        try:
            args = self.do_new_parser.parse_args(args=argv)
        except ArgumentParserError as e:
            logger.error("ArgumentParserError for %s" % line)
            if e:
                print(e)
                logger.error(e)
            args = None
        if args:
            # Set default account values
            new_account_obj = account.Account({})
            new_account_obj.NAME = args.name.strip("\"")
            new_account_obj.CURRENCY = args.currency
            new_account_obj.TYPE = args.type
            new_account_obj.RATE_TO = 1
            new_account_obj.BALANCE = 0
            new_account_obj.ACTIVE = True
            self.database.add_account(new_account_obj)

    def help_new(self):
        self.do_new_parser.print_usage()

    """
    Disable an existing account
    """
    def do_deactive(self, line):
        pass

    def help_deactive(sel):
        print("Select an account to deactive")
        print("active <ID|NAME>")

    """
    Disable an existing account
    """
    def do_reactive(self, line):
        pass

    def help_reactive(sel):
        print("Select an account to re-active")
        print("reactive <ID|NAME>")

    """
    Add a transaction to the currently selected account
    """
    def do_add(self, line):
        if not self.curr_account:
            print("Please select an account first!!")
            return False

        argv = self.split_line(line)
        try:
            args = self.do_add_parser.parse_args(args=argv)
        except ArgumentParserError as e:
            logger.error("ArgumentParserError for %s" % line)
            if e:
                print(e)
                logger.error(e)
            args = None
        if args:
            # Set default account values
            new_trans_obj = transaction.Transaction({})
            new_trans_obj.DATE = args.date
            new_trans_obj.NAME = args.name.strip("\"")
            new_trans_obj.TYPE = args.transfer
            new_trans_obj.BUDGET_ID = args.budget
            new_trans_obj.AMOUNT = args.amount
            new_trans_obj.CLEAR = args.clear
            self.curr_account.add_transaction(new_trans_obj)

    def help_add(self):
        self.do_add_parser.print_usage()

    def do_EOF(self, line):
        self.database._close()
        return True
