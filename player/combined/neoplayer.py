from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ConfigParser import ConfigParser

from pyvirtualdisplay import Display

import re
import sys
import time
import random
import datetime

from url import URLs
from xpath import XPaths
import locators 
import foodclub

# TODO: add action that verifies user is logged in after every page load

class Player():
    config  = None
    fout    = None
    display = None
    driver  = None

    error_count = 0

    use_virtual = True # TODO: put into config.ini

    datetime_format = '%H:%M:%S %m-%d-%Y' # TODO: put into config.ini

    # Overhaul's member variables

    profile  = ""
    driver   = None
    tries    = 3

    username = ""
    password = ""

    def __init__(self):
        # Parse config file, read contents into 'config' class member
        try:
            parser = ConfigParser()
            parser.read('config.ini')
            self.config = {}
            self.config['profile']  = parser.get('player', 'profile')
            self.config['runonce']  = parser.get('daemon', 'runonce')
            self.config['logfile']  = parser.get('logging', 'logfile')
            self.config['username'] = parser.get('account', 'username')
            self.config['password'] = parser.get('account', 'password')
            self.config['petname']  = parser.get('account', 'petname')
            self.config['wait']     = parser.get('driver', 'wait')
            self.config['visible']  = parser.get('display', 'visible')
            self.config['x']        = parser.get('display', 'x')
            self.config['y']        = parser.get('display', 'y')
        except Exception as e:
            sys.stderr.write("Exception encountered when parsing config file.\n")
            sys.exit(1)

    def __del__(self):
        # Close Selenium WebDriver if open
        try:
            self.driver.quit()
        except:
            pass

        # Stop virtual display if running
        if self.use_virtual == True and type(self.display).__name__ == 'Display' and self.display.is_alive() == True:
            self.display.stop()

        # Close log file if open
        if type(self.fout).__name__ == 'file' and self.fout.closed == False:
            self.fout.close()

    def start(self):
        # Start virtual display
        if self.use_virtual == True:
            try:
                self.display = Display(visible = self.config['visible'], size = (self.config['x'], self.config['y'])).start()
            except Exception as e:
                sys.stderr.write("Exception encountered when opening virtual display:\n%s\n" % str(e))
                sys.exit(3)

        # Open Selenium WebDriver, set window size, set function alias
        try:
            self.driver = WebDriver(firefox_profile = FirefoxProfile(self.config['profile']))
            #self.driver.set_window_size(self.config['x'], self.config['x']) # TODO: add resize yea or nay to config.ini
            self.driver.implicitly_wait(self.config['wait'])
            self.febx = self.driver.find_element_by_xpath
            self.febcn = self.driver.find_element_by_class_name
            self.febcs = self.driver.find_element_by_css_selector
        except Exception as e:
            sys.stderr.write("Exception encountered when opening WebDriver:\n%s\n" % str(e))
            sys.exit(4)

    def stop(self):
        # Close Selenium WebDriver
        try:
            self.driver.quit()
        except Exception as e:
            sys.stderr.write("Exception encountered when closing WebDriver:\n%s\n" % str(e))

        # Stop virtual display
        try:
            if self.use_virtual == True and type(self.display).__name__ == 'Display' and self.display.is_alive() == True:
                self.display.stop()
        except Exception as e:
            sys.stderr.write("Exception encountered when stopping virtual display:\n%s\n" % str(e))

        self.writeAndFlush("\n")

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Controls                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    def run(self):
        while True:
            # Start resources, log in and, if successful, perform tasks, then stop resources
            self.start()
            if self.login():
                #self.battledome()
                self.academy()
                #self.bet()
            self.stop()

            # Exit instead of sleeping if run_once is enabled
            if self.config['runonce'].lower() == "true":
                return

            # Go to sleep
            random.seed()
            #now = datetime.datetime.now()
            #then = (now + datetime.timedelta(days = 1)).replace(hour = random.randint(9, 12), minute = random.randint(0, 59), second = random.randint(0, 59))
            #delta = (then - now).total_seconds()
            #self.writeAndFlush("Sleeping until %s (%d seconds).\n" % ((now + datetime.timedelta(seconds = delta)).strftime('%m-%d-%Y %H:%M:%S'), delta))
            #time.sleep(delta)
            time.sleep(random.uniform(29000, 32000))

    def login(self):
        self.writeAndFlush("Attempting to log in as %s..." % self.config['username'])

        attempt = 0
        while attempt < 3:
            self.getAndWait(URLs.general['root'], 1.5, 2.5)

            try:
                if self.is_logged_in():
                    if self.get_logged_in_username() == self.config['username']:
                        self.writeAndFlush("Already logged in as %s." % self.config['username'])
                        return True
                    else:
                        self.writeAndFlush("Logging out of %s." % self.get_logged_in_username())
                        self.logout()

                self.clickAndWait(self.febx(XPaths.login['login_link']), 0.25, 0.5)
                self.clickAndWait(self.febx(XPaths.login['username_field']), 0.2, 0.5) # Probably already focused
                self.typeAndWait(self.febx(XPaths.login['username_field']), self.config['username'], 0.1, 0.2)
                self.typeAndWait(self.febx(XPaths.login['username_field']), Keys.TAB, 0.25, 0.5)
                self.typeAndWait(self.febx(XPaths.login['password_field']), self.config['password'], 0.5, 1.0)
                self.clickAndWait(self.febx(XPaths.login['login_button']), 4.0, 7.0)

                if self.is_logged_in():
                    if self.get_logged_in_username() == self.config['username']:
                        self.writeAndFlush("Successfully logged in to %s." % self.config['username'])
                        return True
                    else:
                        self.writeAndFlush("Successfully logged in, but not as desired user???")
                        self.logout()
                        attempt += 1
                        continue

                return True
            except Exception as e:
                attempt += 1

                self.writeAndFlush("Login attempt %i failed." % attempt)
                sys.stderr.write("Exception during login attempt:\n%s\n" % str(e))

                # Ensure we're not somehow logged into something for next attempt
                self.logout()

        self.writeAndFlush("Could not log in to %s. Exiting." % self.config['username'])
        sys.stderr.write("Could not log in to %s.\n" % self.config['username'])

        return False

    # Overhaul's login function
    def login0(self):
        self.getAndWait(URLs.login['login'], 0.5, 1)

        element_field_username = self.febx(locators.login['field_username'].XPath)
        element_field_password = self.febx(locators.login['field_password'].XPath)
        element_button_login = self.febcn(locators.login['button_login'].Class)

        # TODO: make sure correct elements are focused as we go
        self.clickAndWait2(element_field_username, 0.5, 1.0)
        self.typeAndWait(element_field_username, self.username + Keys.TAB, 0.5, 1.0)
        self.typeAndWait(element_field_password, self.password, 0.5, 1.0)
        self.clickAndWait2(element_button_login, 3.0, 5.0)

        # TODO: wait for some new element or lack of old or url change to confirm login complete
        #WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, 'IdOfMyElement')))
        #wait(driver, 15).until_not(EC.title_is(title))

    def logout(self):
        if self.is_logged_in():
            try:
                self.clickAndWait(self.febx(XPaths.account['logout_link']), 1.0, 2.5)
                self.writeAndFlush("Successfully logged out.")
            except:
                pass

    def bank(self, action, amount):
        self.getAndWait(URLs.bank['bank'], 0.5, 1)

        if action == "withdraw":
            element_field_withdraw = self.febx(locators.bank['element_field_withdraw'].XPath)
            element_button_withdraw = self.febx(locators.bank['element_button_withdraw'].XPath)

            self.clickAndWait2(element_field_withdraw, 0.5, 1.0)
            self.typeAndWait(element_field_withdraw, str(amount), 0.5, 1.0)
            self.clickAndWait2(element_button_withdraw, 1.5, 2.5)

            # TODO: formal driver wait for dialog box
            try:
                self.driver.switch_to.alert.accept()
                self.sleepRange(1.0, 2.0)
            except:
                pass

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Wrappers                                                                                                      ##
    ##                                                                                                                ##
    ####################################################################################################################

    # TODO: always check to see if we're logged in
    def getAndWait(self, url, sleep_lower, sleep_upper):
        try:
            self.driver.get(url)
            self.sleepRange(sleep_lower, sleep_upper)
            return True
        except Exception as e:
            sys.stderr.write("getAndWait: encountered exception: %s\n", e.message)
            return False

    def clickAndWait(self, element, lower, upper):
        element.click()
        time.sleep(random.uniform(lower, upper))

    # Overhaul's clickAndWait
    def clickAndWait2(self, element, sleep_lower, sleep_upper):
        try:
            element.click()
            self.sleepRange(sleep_lower, sleep_upper)
            return True
        except Exception as e:
            sys.stderr.write("clickAndWait2: encountered exception: %s\n", e.message)
            return False

    def typeAndWait(self, element, keys, sleep_lower, sleep_upper):
        try:
            for letter in keys:
                element.send_keys(letter)
                self.sleepRange(0.05, 0.07, 1.0)
            self.sleepRange(sleep_lower, sleep_upper)
            return True
        except Exception as e:
            sys.stderr.write("typeAndWait: encountered exception: %s\n", e.message)
            return False

    def selectAndWait(self, element, value, sleep_lower, sleep_upper):
        try:
            element.select_by_value(value)
            self.sleepRange(sleep_lower, sleep_upper)
            return True
        except Exception as e:
            sys.stderr.write("selectAndWait: encountered exception: %s\n", e.message)
            return False

    def sleepRange(self, lower, upper, variation = 1.25):
        lower = random.uniform(lower / variation, lower * variation)
        upper = random.uniform(lower / variation, upper * variation)
        time.sleep(random.uniform(lower, upper))

    def writeAndFlush(self, string):
        print string

        try:
            self.fout = open(self.config['logfile'], 'a')
        except Exception as e:
            sys.stderr.write("Exception encountered when opening log file.\n")
            sys.stderr.write("Logged message: %s - %s\n" % (datetime.datetime.now().strftime(self.datetime_format), string))
            return

        try:
            self.fout.write("%s - %s\n" % (datetime.datetime.now().strftime(self.datetime_format), string))
            self.fout.flush()
        except:
            sys.stderr.write("Exception encountered when writing to log file.\n")
            sys.stderr.write("Logged message: %s - %s\n" % (datetime.datetime.now().strftime(self.datetime_format), string))

        if type(self.fout).__name__ == 'file' and self.fout.closed == False:
            self.fout.close()

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Auxiliary                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    # TODO: instead, check for login button or the sign in page
    def is_logged_in(self):
        try:
            logout = self.driver.find_element_by_id('logout_link')
            return logout.is_displayed()
        except:
            return False

    def get_logged_in_username(self):
        return self.febx(XPaths.account['username']).text

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Battledome                                                                                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

    def battledome(self):
        # TODO: change checks so this doesn't need to be used
        self.item_limit = False
        # TODO: change battle_loop so these can be local
        self.fight_number = 0 # Track fight number for logging

        try:
            self.battle_loop(0, 0) # Begin battle loop
        except Exception as e:
            self.writeAndFlush("Was unable to Battledome: %s" % e.message)

    # TODO: replace clunky hacky shit with exception raising and catching
    def battle_loop(self, start_attempt, attack_attempt):
        if self.select_and_enter_battle() == False: # These errors are showstoppers. Just give up now.
            raise Exception("Unrecoverable error encountered while attempting to enter Battledome. Aborting.")

        while self.item_limit == False:
            if self.start_battle() == False: # If error encountered while beginning battle, retry
                if start_attempt < 5:
                    self.writeAndFlush("Error encountered while attempting to begin battle. Reentering Battledome. Retry count: %d" % start_attempt + 1)
                    return self.battle_loop(start_attempt + 1, attack_attempt)
                else:
                    raise Exception("Failed out while trying to battle. Aborting.")

            first = True # Used to determine which ability to use
            while self.collect_rewards() == False: # Attack until rewards are detected
                if self.attack(first) == False: # Retry when error is encountered while trying to attack
                    if attack_attempt < 10:
                        self.writeAndFlush("Error encountered while attempting to attack. Reentering Battledome. Retry count: %d" % attack_attempt + 1)
                        return self.battle_loop(start_attempt, attack_attempt + 1)
                    else:
                        raise Exception("Failed out while trying to battle. Aborting.")
                first = False

            # Reset retries after each successful fight
            start_attempt = 0
            attack_attempt = 0

            self.fight_number += 1
            self.writeAndFlush("Fight %i completed." % self.fight_number)

        self.writeAndFlush("Battledome prize limit reached.")

    # Select opponent and enter battle
    def select_and_enter_battle(self):
        self.getAndWait(URLs.bd['main'], 0.5, 1.5) # Navigate to Battledome main page
        self.clickAndWait(self.febx(XPaths.bd['main']['battle']), 0.5, 1.5) # Click "battle" button to begin selection process or reenter battle in progress

        try: # Begin new battle; select pet and opponent
            selected_pet = self.febx(XPaths.bd['fight']['pet_name']).text # Get name of pet selected for battle
            if self.config['petname'] != selected_pet: # Verify selected pet
                self.writeAndFlush("Wrong pet selected.")
                return False

            self.clickAndWait(self.febx(XPaths.bd['fight']['continue1']), 0.5, 1.0) # Click continue buttons to continue to opponent selection
            self.clickAndWait(self.febx(XPaths.bd['fight']['continue2']), 1.0, 2.0)

            self.clickAndWait(self.febx(XPaths.bd['fight']['opponent_hard']), 1.0, 2.0) # Select opponent and difficulty

            # TODO: desired opponent to config.ini, implement more flexible method by which to select opponent
            if self.febx(XPaths.bd['fight']['opponent_name']).text != "Chia Clown": # Verify selected opponent
                self.writeAndFlush("Opponent mismatch. Selected opponent name: %s" % self.febx(XPaths.bd['fight']['opponent_name']).text)
                return False

            self.clickAndWait(self.febx(XPaths.bd['fight']['battle']), 3.0, 7.0) # Click "Battle!" button to enter Battledome

            self.writeAndFlush("Entered Battledome.")
        except: # Returned battle in progress
            self.writeAndFlush("Reentered Battledome.")

        return True

    # Called at beginning of fight or when restarting fight. Begins fight.
    def start_battle(self):
        try: # Press the "play again" button if this is the end of a previous fight
            self.clickAndWait(self.febx(XPaths.bd['arena']['play_again']), 3.0, 5.0)
        except:
            pass

        ex = None
        attempt = 0

        # Attempt to begin the battle by pressing the 'Fight!' button
        while attempt < 3:
            try:
                # TODO: wait until element loaded
                self.clickAndWait(self.febx(XPaths.bd['arena']['fight1']), 5.0, 7.5) # Press first "fight" button to begin the fight
                return True
            except Exception as e: # Upon failure, reload page and try again
                ex = e
                attempt += 1
                self.error_count += 1
                self.driver.save_screenshot('%i-start_battle_exception.png' % self.error_count)
                self.getAndWait(URLs.bd['arena'], 3.0, 7.0)

        self.writeAndFlush("Error beginning battle.")
        sys.stderr.write("Error beginning battle:\n%s\n" % ex.message)
        return False
    
    def attack(self, first):
        if self.select_item('slot1', 'item1') == False or self.select_item('slot2', 'item2') == False: # Select equipment; check for failures
            return False

        # Select ability; Lens Flare if first turn of battle, otherwise select secondary ability; check for failures
        ability = 'ability1' if first == True else 'ability2'
        if self.select_item('slot3', ability) == False:
            return False

        # TODO: wrap in try-catch maybe?
        self.clickAndWait(self.febx(XPaths.bd['arena']['fight2']), 4.0, 7.0) # Click "Attack" button

        self.skip_replay()

        return True

    def select_item(self, slot, selection):
        if self.driver.current_url != URLs.bd['arena']:
            sys.stderr.write("select_item error: incorrect current url: %s\n" % self.driver.current_url)

        ex = None
        tries = 0

        # TODO: rework into something less shitty
        while tries < 10: # Retry once per second for fifteen seconds to allow ample time for Battledome to finish loading
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, XPaths.bd['arena'][slot]))).click()
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, XPaths.bd['arena'][selection]))).click() # Check if not visible
                return True
            except Exception as e:
                ex = e # Printed if all tries fail out
                tries += 1
                self.error_count += 1
                self.driver.save_screenshot('%i-select_item_exception.png' % self.error_count)

        self.writeAndFlush("Couldn't select item.")
        sys.stderr.write("Couldn't select item:\n%s" % str(ex))
        return False

    # TODO: check if fight button is inactive
    def skip_replay(self):
        tries = 0
        #found = False

        while tries < 5: # Retry once per second for ten seconds to allow ample time for next screen to finish loading
            try:
                if 'replay' not in self.febx(XPaths.bd['arena']['skip_replay']).get_attribute('class'): # Only click replay button if animation isn't finished and we're therefor able to collect the prizes or attack again
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, XPaths.bd['arena']['skip_replay']))).click()
                return
            except Exception as e:
                self.driver.save_screenshot('%i-skip_replay_exception.png' % self.error_count)
                self.error_count += 1
                tries += 1

        self.writeAndFlush("'Skip replay' button was not found. Attempting to continue.")

    # TODO: devise a way to ensure battle still in progress
    def collect_rewards(self):
        try:
            self.clickAndWait(self.febx(XPaths.bd['arena']['collect_rewards']), 1.5, 2.5) # Check to see if battle is over by attempting to click 'collect rewards' button, which also obviously collects the rewards
            self.check_if_limit_reached() # Set item_limit boolean used in main Battledome loop. What an ugly hack.
            return True
        except:
            return False # If element is not found, either the battle isn't over or something bad happened

    def check_if_limit_reached(self):
        try:
            #if "You have reached the item limit for today!" in self.febx(XPaths.bd['arena']['item_limit']).text: # Check rewards div for item limit text
            if "You have reached the item limit for today!" in WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, XPaths.bd['arena']['item_limit']))).text: # Check rewards div for item limit text
                self.item_limit = True
        except:
            pass # If element is not found, either the battle isn't over or something bad happened

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Academy                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def academy(self):
        if self.check_if_enrolled():
            if self.withdraw_payment():
                return self.pay_for_course()
        else:
            self.complete_course()
            if self.select_course():
                if self.withdraw_payment():
                    return self.pay_for_course()

    def select_course(self):
        course = self.decide_course()

        self.getAndWait(URLs.academy['courses'], 1.0, 2.5)

        try:
            # TODO: clean this shit up
            self.clickAndWait(self.febx("//select[@name='course_type']/option[text()='%s']" % course), 0.5, 1.5)                   # Select course
            self.clickAndWait(self.febx("//select[@name='pet_name']/option[text()[contains(.,'Ryadow')]]"), 3.0, 5.0)              # Select pet
            self.clickAndWait(self.febx(XPaths.academy['courses']['start_course']), 3.0, 5.0)                                      # Start course
            return True
        except:
            self.writeAndFlush("Couldn't select pet at Swashbuckling Academy.")
            return False

    def get_pet_stats(self):
        if self.driver.current_url != URLs.academy['status']:
            self.getAndWait(URLs.academy['status'], 1.0, 3.0)

        stats = {}
        try:
            name                = self.febx(XPaths.academy['status']['pet']).text
            level               = int(self.febx(XPaths.academy['status']['level']).text)
            stats['Agility']    = int(self.febx(XPaths.academy['status']['movement']).text)
            stats['Defence']    = int(self.febx(XPaths.academy['status']['defense']).text)
            stats['Strength']   = int(self.febx(XPaths.academy['status']['strength']).text)
            stats['Endurance']  = int(self.febx(XPaths.academy['status']['hitpoints']).text.split()[-1])
            return { 'Name' : name, 'Level' : level, 'Stats' : stats }
        except:
            self.writeAndFlush("Couldn't parse pet status at Swashbuckling Academy.")
            return None

    def decide_course(self):
        pet = self.get_pet_stats()
        level = pet['Level']
        stats = pet['Stats']

        reg_thresh = level * 2
        hps_thresh = level * 3 if level < 20 else level * 2 + 20

        minStat = min(stats, key=stats.get)
        maxStat = max(stats, key=stats.get)
        minVal = stats[minStat]
        maxVal = stats[maxStat]

        last = str(level)[-1]
        close = last == '8' or last == '9' or last == '0'

        full = stats['Strength'] == reg_thresh and stats['Defence'] == reg_thresh and stats['Agility'] == reg_thresh
        over = stats['Strength'] > reg_thresh or stats['Defence'] > reg_thresh or stats['Agility'] > reg_thresh

        if over:
            return 'Level'
        elif close and full and stats['Endurance'] < hps_thresh:
            return 'Endurance'
        elif maxVal > reg_thresh:
            return 'Level'
        else:
            return minStat

    def withdraw_payment(self):
        try:
            self.getAndWait(URLs.sdb['fdc'], 1.5, 3.5)
            self.clickAndWait(self.febx(XPaths.sdb['remove_one']), 2.0, 3.0)
            return True
        except:
            self.writeAndFlush("Couldn't withdraw payment for Swashbuckling Academy.")
            return False

    # TODO: check to make sure we actually paid
    def pay_for_course(self):
        if self.driver.current_url != URLs.academy['status']:
            self.getAndWait(URLs.academy['status'], 1.5, 2.5)

        try:
            self.clickAndWait(self.febx(XPaths.academy['status']['pay']), 5.0, 10.0)
            self.writeAndFlush("Paid for training course at Swashbuckling Academy.")
            return True
        except:
            self.writeAndFlush("Couldn't pay for course at Swashbuckling Academy.")
            return False

    def check_if_enrolled(self):
        if self.driver.current_url != URLs.academy['status']:
            self.getAndWait(URLs.academy['status'], 0.5, 1.0)

        try:
            self.febx(XPaths.academy['status']['pay'])
            return True
        except:
            return False
    
    # TODO: detect if we got bonus to level causing us to skip close condition, thereby missing a bunch of cheaper endurance training
    def complete_course(self):
        if self.driver.current_url != URLs.academy['status']:
            self.getAndWait(URLs.academy['status'], 2.5, 3.5)
        
        try:
            self.clickAndWait(self.febx(XPaths.academy['status']['complete']), 3.0, 7.0)
            self.writeAndFlush("Completed training course at Swashbuckling Academy.")
        except:
            #self.writeAndFlush("Couldn't complete course at Swashbuckling Academy.")
            pass # Pet was probably simply not on a course.

    ####################################################################################################################
    ##                                                                                                                ##
    ##  Food Club                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    # TODO: validate bets before beginning
    def bet(self):
        # TODO: count bets to see if they're already placed
        #self.getAndWait(URLs.foodclub['current'], 1.0, 2.0)
        #bets_table = febx(xpath_current['bets_table'])
        #bets_rows = bets_table.find_elements_by_tag_name('tr')

        self.getAndWait(URLs.foodclub['boochi'], 0.5, 1.0)

        # The date the bets are for
        bets_for = self.febcs("body > center:nth-child(6) > p:nth-child(1) > font:nth-child(1)").text

        # Each set consists of one or more pairs
        sets = []

        # Forumlate set of all bets by parsing somebody's bets table
        source = self.driver.page_source
        bets = re.findall("<td><b>[^=]+<br><\/td>", source)
        for bet in bets:
            # Each pair consist of arena name and pirate name
            pairs = re.findall("<b>([^<]*)<\/b>: ([^<]*)<br>", bet)
            s = []
            for pair in pairs:
                s.append(pair)
            sets.append(s)

        self.getAndWait(URLs.foodclub['place'], 0.5, 1.0)

        # TODO: instead of or in addtion to this, validate scraped bets as possible for the current day
        next_round = str([int(c) for c in self.febcs(".content > center:nth-child(1) > b:nth-child(2)").text.split() if c.isdigit()][0])
        if next_round not in bets_for:
            sys.stderr.write("These bets don't appear to be up to date.\n")
            return

        # Parse bet amount from bets page, withdraw for ten bets
        amount = self.febx(foodclub.xpath_foodclub['bet_amount']).text
        self.bank('withdraw', str(int(amount) * 10))

        # Place each set of bets
        for s in sets:
            self.getAndWait(URLs.foodclub['place'], 1.0, 2.0)
            bet_element = self.febx(foodclub.xpath_foodclub['place_bet'])
            # Pairs consist of arena in first index, pirate in second
            for pair in s:
                element_arena = self.febx(foodclub.xpath_arena[pair[0]])                                               # Arena checkbox element
                element_pirate = self.febx(foodclub.xpath_pirate[pair[0]])                                             # Pirate option element?
                element_option = Select(element_pirate)                                                                # Arena pirate option box element
                self.clickAndWait2(element_arena, 0.5, 1.0)                                                             # Click arena checkbox
                self.selectAndWait(element_option, foodclub.dict_pirates[pair[1]], 0.5, 1.0)                           # Select pirate from option box
            element_amount = self.febx(foodclub.xpath_foodclub['bet_box'])                                             # Bet amount text box element
            self.clickAndWait2(element_amount, 0.5, 1.0)
            self.typeAndWait(element_amount, amount, 0.5, 1.0)
            self.clickAndWait2(bet_element, 2.0, 3.0)
            #self.wait()
            WebDriverWait(self.driver, 10).until_not(EC.title_is(URLs.foodclub['place']))
    
    def wait(self):
        for count in xrange(0, 30):
            # Look for success page
            try:
                bets = self.febx(foodclub.xpath_foodclub['current_bets'])
                bets.click() # ???
                if bets.text == "Current Bets": # ???
                    return
            except:
                # Look for duplicate bet page
                try:
                    bets = self.febx(foodclub.xpath_foodclub['duplicate'])
                    bets.click() # ???
                    return
                except:
                    count += 1
                    self.sleepRange(1.0, 2.0)

########################################################################################################################
##                                                                                                                    ##
##  Main                                                                                                              ##
##                                                                                                                    ##
########################################################################################################################

if __name__ == '__main__':
    try:
        Player().run()
    except KeyboardInterrupt:
        print "Player stopped."