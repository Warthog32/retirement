import json

# Configuration keys
CONFIG_EXPENSES = 'expenses' # monthly expenses during start year
CONFIG_INFLATION = 'inflation' # annual inflation percentage

CONFIG_INCOME_SOURCES = 'incomeSources'
CONFIG_INCOME_NAME = 'name'
CONFIG_INCOME_AMOUNT = 'amount'
CONFIG_INCOME_START_AGE = 'startAge'
CONFIG_INCOME_END_AGE = 'endAge'

CONFIG_ACCTS = 'accounts'
CONFIG_ACCT_NAME = 'name'
CONFIG_ACCT_BALANCE = 'balance'
CONFIG_ACCT_TARGET_BALANCE = 'targetBalance'
CONFIG_ACCT_RETURN_RATE = 'returnRate'

CONFIG_START_YEAR = 'startYear'
CONFIG_END_YEAR = 'endYear'

# Output-only keys
KEY_YEAR = 'year'
CONFIG_INCOME_TOTAL = 'incomeTotal'
KEY_EXPENSES = 'expenses'

OUTPUT_KEYS = [(KEY_YEAR, "%d")
               , (KEY_EXPENSES, "%.2f")
               , (CONFIG_INCOME_TOTAL, "%.2f")
              ]

#------------------ Config

def validateConfig():
    assert config[CONFIG_EXPENSES] >= 0
    assert config[CONFIG_INFLATION] >= 0 and config[CONFIG_INFLATION] <= 1

    assert config[CONFIG_ACCTS] is not None and len(config[CONFIG_ACCTS]) > 0
    for acctName in config[CONFIG_ACCTS]:
        acct = config[CONFIG_ACCTS][acctName]
        assert acct[CONFIG_ACCT_BALANCE] is not None
        assert acct[CONFIG_ACCT_BALANCE] >= 0
        assert acct[CONFIG_ACCT_RETURN_RATE] is not None
        assert acct[CONFIG_ACCT_RETURN_RATE] >= 0
        assert (CONFIG_ACCT_TARGET_BALANCE not in acct
                or acct[CONFIG_ACCT_TARGET_BALANCE] > 0
               )

    assert (config[CONFIG_INCOME_SOURCES] is not None
            and len(config[CONFIG_INCOME_SOURCES]) > 0
           )
    for income in config[CONFIG_INCOME_SOURCES]:
        assert income[CONFIG_INCOME_NAME] is not None
        assert income[CONFIG_INCOME_AMOUNT] is not None

#------------------ Util

def filterYear(year, config):
    return ( (not (CONFIG_START_YEAR in config) or config[CONFIG_START_YEAR] <= year) and
             (not (CONFIG_END_YEAR in config) or config[CONFIG_END_YEAR] >= year)
           )
           
#------------------ Calc functions

def calcReturns(current, previous):
    current[CONFIG_ACCTS] = {}
    for acctName in config[CONFIG_ACCTS]:
        cfgAcct = config[CONFIG_ACCTS][acctName]
        if previous is None:
            newAcct = cfgAcct
            newAcct[CONFIG_ACCT_BALANCE] = ( cfgAcct[CONFIG_ACCT_BALANCE]
                                             * (1.0 + cfgAcct[CONFIG_ACCT_RETURN_RATE])
                                           )
        else:
            prvAcct = previous[CONFIG_ACCTS][acctName]
            newAcct = prvAcct.copy()
            newAcct[CONFIG_ACCT_BALANCE] = ( prvAcct[CONFIG_ACCT_BALANCE] 
                                             * (1.0 + cfgAcct[CONFIG_ACCT_RETURN_RATE])
                                           )
        current[CONFIG_ACCTS][acctName] = newAcct

def calcExpenses(current, previous):
    if (previous == None):
        current[KEY_EXPENSES] = config[CONFIG_EXPENSES]
    else:
        current[KEY_EXPENSES] = previous[KEY_EXPENSES] * (1 + config[CONFIG_INFLATION])

def calcIncome(current, previous):
    current[CONFIG_INCOME_TOTAL] = 0

    for incomeSource in config[CONFIG_INCOME_SOURCES]:
        if filterYear(current[KEY_YEAR], incomeSource):
            current[CONFIG_INCOME_TOTAL] += incomeSource[CONFIG_INCOME_AMOUNT]
    # TBD -- need to adjust the above for inflation

def calcBalanceAdjust(current, previous):

    # TBD: to not hardcode "savings"...

    # Adjusts balances of savings account to add yearly income
    # and remove yearly expenses.
    savings = current[CONFIG_ACCTS]["savings"]
    savings[CONFIG_ACCT_BALANCE] += current[CONFIG_INCOME_TOTAL]
    savings[CONFIG_ACCT_BALANCE] -= current[KEY_EXPENSES]

    deficit = savings[CONFIG_ACCT_TARGET_BALANCE] - savings[CONFIG_ACCT_BALANCE]

    # Draw/Push funds from other accounts to match savings target.
    # TBD to add priorities or similar to control ordering
    for acctName in current[CONFIG_ACCTS]:
        if acctName == "savings" or deficit == 0:
            continue
        acct = current[CONFIG_ACCTS][acctName]

        if deficit < 0:
            acct[CONFIG_ACCT_BALANCE] += -deficit
            savings[CONFIG_ACCT_BALANCE] += deficit
            deficit = 0
        elif deficit > 0 and acct[CONFIG_ACCT_BALANCE] > 0:
            transfer = min(deficit, acct[CONFIG_ACCT_BALANCE])
            savings[CONFIG_ACCT_BALANCE] += transfer
            acct[CONFIG_ACCT_BALANCE] -= transfer
            deficit -= transfer


def calcYear(current, previous):
    calcReturns(current, previous)
    calcExpenses(current, previous)
    calcIncome(current, previous)
    calcBalanceAdjust(current,previous)

#------------------ Output

def outputYearsHtml(years):
    with open('Results.html', "w") as of:
        of.write("<HTML><BODY><TABLE>\n")

        of.write("<TR>")
        for keytup in OUTPUT_KEYS:
            of.write("<TH>"+keytup[0]+"</TH>")
        for acctName in config[CONFIG_ACCTS]:
            of.write("<TH>"+acctName+"</TH>")
        of.write("</TR>\n")

        for year in years:
            of.write("<TR>")
            for keytup in OUTPUT_KEYS:
                of.write("<TD>"+(keytup[1] % year[keytup[0]])+"</TD>")

            for acctName in config[CONFIG_ACCTS]:
                acct = year[CONFIG_ACCTS][acctName]
                of.write("<TD>"
                         +"%.2f" % acct[CONFIG_ACCT_BALANCE]
                         +"</TD>"
                        )

            of.write("</TR>\n")

        of.write("</TABLE></BODY></HTML>\n")

#------------------ Main loop

def main():
    with open("Configuration.json","r") as f:
        global config
        config = json.load(f)
    validateConfig()

    years = []
    previous = None
    for year in range(2021, 2071):
        current = {KEY_YEAR : year}
        calcYear(current, previous)
        years.append(current)
        previous = current
        if current[CONFIG_ACCTS]["savings"][CONFIG_ACCT_BALANCE] < 0:
            print('Destitute on year '+str(year))
            break

    outputYearsHtml(years)

main()
