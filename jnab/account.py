import logging

from enum import Enum

import util

class Currency(Enum):
    USD = 1     # US Dollar
    EURO = 2    # EURO
    CHF = 3     # Swish Franc
    CNY = 4     # Chinese Yuan
    CAD = 5     # Canadian Dollar

class Type(Enum):
    CHECKING = 1
    CREDIT = 2
    CASH = 3

class AccountError(Exception):
    pass

class AccountInvalidAttributeError(AccountError):
    pass

logger = util.get_logger("account")

class Account(object):

    account_db_attributes = ['ID', 'NAME', 'TYPE', 'CURRENCY', 'RATE_TO', 'BALANCE', 'ACTIVE']

    def __init__(self, account_dict):
        for key in account_dict:
            if key in self.account_db_attributes:
                self.__setattr__(key, account_dict[key])

    def __setattr__(self, name, value):
        if name not in self.account_db_attributes:
            raise AccountInvalidAttributeError("Invalid Account object attribute %s" % name)
        # Do not allow permenent account attribute to be changed
        if name in ['ID', 'NAME', 'CURRENTY', 'TYPE'] and hasattr(self, name):
            raise AccountInvalidAttributeError("Unable to change existing permenent account attribute %s" % name)

        # Modify the some attributes before setting it
        if name == 'TYPE':
            if type(value) is int:
                super.__setattr__(self, name, Type(value))
            elif type(value) is str:
                super.__setattr__(self, name, Type(Type.__getattr__(value.upper()).value))
        elif name == 'CURRENCY':
            if type(value) is int:
                super.__setattr__(self, name, Currency(value))
            elif type(value) is str:
                super.__setattr__(self, name, Currency(Currency.__getattr__(value.upper()).value))
            else:
                abort()
        elif name == 'NAME':
            super.__setattr__(self, name, value.upper())
        else:
            super.__setattr__(self, name, value)

    def _dict(self):
        account_dict = {}
        for attr in self.account_db_attributes:
            if attr == 'TYPE' or attr == 'CURRENCY':
                account_dict[attr] = self.__getattribute__(attr).value
            else:
                account_dict[attr] = self.__getattribute__(attr)
        return account_dict

    def __repr__(self):
        return repr(self._dict())

    def __str__(self):
        # TODO use corresponding unicode currency symbol
        return "%d - %s: $%f; %s, %s, RATE(%f)" % (self.ID, self.NAME, self.BALANCE, self.CURRENCY.name, self.TYPE.name, self.RATE_TO)

    def check_sanity(self):
        for attr in self.account_db_attributes:
            if not hasattr(self, attr):
                return False
        # TODO: more in depth check of each field with type and content
        ## Configure:
        ### account name
        ### currency
        ### account type
        ### conversion rate
        ### transaction lookup table
