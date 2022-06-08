from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from chromedriver_py import binary_path # this will get you the path variable
import time
import yaml
import sys
from os.path import exists
with open('config.yml', 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)
blocked_words = cfg['blocked_words']
search_terms = cfg['search_terms']
monster_username = cfg['monster_username']
monster_password = cfg['monster_password']
app_count = 0
skip_count = 0

##################################################
###########   chromedriver options    ############
##################################################

# start configuring options
options = webdriver.ChromeOptions()

# if --headless flag is provided
if '--headless' in sys.argv:
    options.add_argument('headless')

options.add_argument('user-data-dir=monsterCache')
options.add_argument("--disable-dev-shm-usage");
options.add_argument("--no-sandbox");
options.add_argument('--remote-debugging-port=45447')
options.add_argument("--disable-gpu")
options.add_argument('--ignore-certificate-errors')
driver = webdriver.Chrome(executable_path=binary_path, options=options)
driver.set_window_size(1920, 1080)
driver.implicitly_wait(10)

##################################################
###############   functions    ###################
##################################################

def scrollToBottom():
    try:
        job_list = driver.find_element_by_id('card-scroll-container')
        driver.execute_script("arguments[0].scrollTo(0, document.getElementById('card-scroll-container').scrollHeight);", job_list)
        time.sleep(1)
        driver.execute_script("arguments[0].scrollTo(0, 0);", job_list)
        time.sleep(1)
        driver.execute_script("arguments[0].scrollTo(0, document.getElementById('card-scroll-container').scrollHeight);", job_list)
        time.sleep(3)
        buttons = driver.find_elements_by_tag_name("button")
        load_more_button = [ button for button in buttons if button.text == 'Load more' ]
        if len(load_more_button) == 1:
            driver.execute_script("arguments[0].click();", load_more_button[0])
    except Exception as e:
        print(e)
        time.sleep(3)

def monsterLogin():
    # log into Monster using provided credentials if not logged in
    try:
        monster_login = "https://www.monster.com/profile/detail"
        driver.get(monster_login)
        email = driver.find_element_by_id('email')
        password = driver.find_element_by_id('password')
        login = driver.find_elements_by_tag_name('button')
        login = [ button for button in login if 'Log' in button.get_attribute('innerHTML') ][0]
        # driver.execute_script("arguments[0].setAttribute('value',arguments[1])",email, monster_username)
        # driver.execute_script("arguments[0].setAttribute('value',arguments[1])",password, monster_password)
        email.click()
        email.send_keys(monster_username)
        password.click()
        password.send_keys(monster_password)
        login.click()
        time.sleep(10)
    except:
        pass

#####################################################
#############  tryApplication function  #############
#####################################################


def tryApplication(next_apply_button, job_title):
    global app_count
    global skip_count

    # try to get company name (sometimes is invalid for for some reason)
    try:
        company_name = driver.execute_script("return arguments[0].parentElement.parentElement.parentElement.querySelector('h3').innerText;", next_apply_button)
    except:
        company_name = "COULDN'T GET COMPANY NAME"
        skip_count += 1
        print(company_name)

    # skip job if company is on skiplist
    if company_name in skiplist:
        skip_count += 1
        return

    # clicks apply button
    driver.execute_script("arguments[0].click();", next_apply_button)

    # skip job if application is offsite
    time.sleep(8)
    driver.switch_to.window(driver.window_handles[1])
    if len(driver.window_handles) > 1 and 'monster.com' not in driver.current_url:

        # closes offsite tabs
        while len(driver.window_handles) > 1:
            driver.close()

        # adds company name to skipfile
        skiplist.append(company_name)
        skipfile.write(f"{company_name}\n")
        skip_count += 1

        driver.switch_to.window(driver.window_handles[0])
        # doesn't return in cases where easyapply is still possible on the first tab
        # TODO unnecessary
        # if driver.find_elements_by_css_selector('button[data-testid="onboarding-submit-button"]') == []:
            # return

    # if the job was already applied to
    submit_buttons = driver.find_elements_by_css_selector('button[data-testid=onboarding-submit-button]')
    if len( submit_buttons ) == 0 and len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)
        skip_count += 1
        return

    # click submit
    if 'monster.com/profile' in driver.current_url and len(driver.window_handles) > 1:
        next_submit_button = submit_buttons[0]
        next_submit_button.send_keys(Keys.ENTER)
        time.sleep(4)
        if len(driver.find_elements_by_css_selector('button[data-testid=onboarding-submit-button]')) == 0:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

    # in case the application form can't submit
    if len(driver.window_handles) > 1 and len(driver.find_elements_by_css_selector('button[data-testid=onboarding-submit-button]')) != 0:
        close_application = driver.find_element_by_css_selector('button[data-testid=cancel-onboarding-iconbutton]')
        driver.execute_script("arguments[0].click();", close_application)
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)
        skip_count += 1
        return

    # if the application submits properly
    app_count = app_count + 1
    print(f"APPLIED TO: {job_title} on Monster")




######################################################
#############  start searching for jobs  #############
######################################################

def monsterSearchAndApply(search_term, remote):
    global app_count
    global skip_count

    # input search terms and visit url
    monster_jobs = f"https://www.monster.com/jobs/search?q={search_term}&where="
    driver.get(monster_jobs)

    # if remote is set to True
    if remote:
        monster_jobs = driver.current_url + "&em=remote&et=remote"
        driver.get(monster_jobs)

    # loop through available jobs
    while True:

        print('...')
        apply_buttons = driver.find_elements_by_css_selector('button[data-test-id=svx-job-apply-button]')
        # end the run if there are no results
        if len(apply_buttons) == 0 and "We didn’t find any jobs matching your criteria" in driver.getPageSource():
            print(f"No More Results\nTOTAL APPLICATIONS: {app_count}")
            return

        # scroll lower if none left and grab next job
        while len(apply_buttons) <= skip_count:
            scrollToBottom()
            apply_buttons = driver.find_elements_by_css_selector('button[data-test-id=svx-job-apply-button]')

            # end the run if there is nothing left to apply to
            buttons = driver.find_elements_by_tag_name("button")
            no_more_results = [ button for button in buttons if button.text == 'No More Results' ]
            if no_more_results and len(apply_buttons) >= skip_count:
                print(f"No More Results\nTOTAL APPLICATIONS: {app_count}")
                return
        next_apply_button = apply_buttons[skip_count]

        # try to apply to job
        try:
            job_title = driver.execute_script("return arguments[0].parentElement.parentElement.parentElement.querySelector('a[data-test-id=svx-job-title]').innerText;", next_apply_button)

            skip_job = 0
            for blocked_word in [ b.lower() for b in blocked_words ]:
                if blocked_word in job_title.lower():
                    skip_count += 1
                    skip_job = 1
                    break
            if skip_job == 1:
                continue
            
            tryApplication(next_apply_button, job_title)
        except Exception as e:
            print(e)

##################################################
##############   main loop    ####################
##################################################

# checks if skipfile exists, creates it if not
if not exists('./monsterUnapplied.txt'):
    fp = open('monsterUnapplied.txt', 'x')
    fp.close()

# access file of company names to skip
with open('./monsterUnapplied.txt', 'r') as file:
    skiplist = [ x.strip() for x in file.readlines() ]
    file.close()
skipfile = open('./monsterUnapplied.txt', 'a')

monsterLogin()
for term in search_terms:

    app_count = 0
    skip_count = 0

    print(f"searching for {term} jobs on Monster")
    monsterSearchAndApply(term, remote=False)
    print(f"searching for {term} remote jobs on Monster")
    monsterSearchAndApply(term, remote=Tre)
    sys.exit(1)
