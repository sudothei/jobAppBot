from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from chromedriver_py import binary_path # this will get you the path variable
import re
import time
import sys
import yaml
with open('config.yml', 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)
blocked_words = cfg['blocked_words']
search_terms = cfg['search_terms']
dice_username = cfg['dice_username']
dice_password = cfg['dice_password']

##################################################
###########   chromedriver options    ############
##################################################

# start configuring options
options = webdriver.ChromeOptions()

# if --headless flag is provided
if '--headless' in sys.argv:
    options.add_argument('headless')

options.add_argument('user-data-dir=diceCache');
options.add_argument("--no-sandbox");
options.add_argument("--disable-dev-shm-usage");
options.add_argument('--remote-debugging-port=45448')
options.add_argument("--disable-gpu")
options.add_argument('--ignore-certificate-errors')
driver = webdriver.Chrome(executable_path=binary_path, options=options)
driver.set_window_size(1920, 1080)
driver.implicitly_wait(10)

##################################################
################   functions    ##################
##################################################

def diceLogin():
    # attempt login
    try:
        dice_login = "https://www.dice.com/dashboard/login"
        driver.get(dice_login)
        email = driver.find_element_by_id('email')
        password = driver.find_element_by_id('password')
        login = driver.find_elements_by_css_selector('button[type=submit]')
        email.send_keys(dice_username)
        password.send_keys(dice_password)
        password.send_keys(Keys.ENTER)
        time.sleep(3)
        driver.get('https://www.dice.com/home/home-feed')
    except:
        pass

def diceSearchAndApply(search_term, remote):
    # search for terms
    driver.get('https://www.dice.com/jobs')
    time.sleep(3)
    search_url = driver.current_url
    search_url = re.sub('q=.*&', f"q={search_term}&", search_url)
    search_url = search_url.replace('pageSize=20', 'pageSize=200')
    if '&filters.easyApply=true' not in search_url:
        search_url = search_url + '&filters.easyApply=true'
    if remote and '&filters.isRemote=true' not in search_url:
        search_url = search_url + '&filters.isRemote=true'

    driver.get(search_url)

    # list of all jobs, applied or unapplied
    job_list = driver.find_elements_by_css_selector('.search-card')


    filtered_list = [ x for x in job_list if 'applied' not in x.get_attribute('outerHTML') ]

    for i in range(len(filtered_list)):
        print('...')
        try:
            next_application = filtered_list[i].find_element_by_css_selector('.card-title-link')
        except Exception as e:
            print(e)
            sys.exit(1)
        job_title = next_application.text

        skip_title = 0
        for blocked_word in [ b.lower() for b in blocked_words ]:
            if blocked_word in job_title.lower():
                skip_title = 1
                break
        if skip_title == 1:
            continue

        time.sleep(2)

        next_application.send_keys(Keys.CONTROL + Keys.RETURN)
        driver.switch_to.window(driver.window_handles[1])

        time.sleep(20)

        # this is a shadow element, which expands to a shadow tree
        button_shadow = driver.find_element_by_css_selector('dhi-wc-apply-button')

        # if already applied
        already_applied = driver.execute_script("return arguments[0].shadowRoot.querySelector('div').querySelector('#ja-apply-button').textContent;", button_shadow)
        if already_applied == 'Applied':
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

        # clicks the apply button in said tree, opening the easy apply form
        driver.execute_script("arguments[0].shadowRoot.querySelector('div').querySelector('#ja-apply-button').querySelector('a').click();", button_shadow)

        time.sleep(2)
        
        # clicks next
        submit_button = driver.find_element_by_class_name('btn-next')
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(2)
        
        # clicks apply
        submit_button = driver.find_element_by_class_name('btn-next')
        driver.execute_script("arguments[0].click();", submit_button)

        print(f"APPLIED TO: {job_title} on Dice")

        time.sleep(60)

        driver.close()
        driver.switch_to.window(driver.window_handles[0])


##################################################
################   main loop    ##################
##################################################

diceLogin()
for term in search_terms:
    print(f"searching for {term} jobs on Dice")
    diceSearchAndApply(term, remote=False)
    print(f"searching for {term} remote jobs on Dice")
    diceSearchAndApply(term, remote=True)
    sys.exit(0)
