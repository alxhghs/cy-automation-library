# -*- coding: utf-8 -*-
"""Automated Section Creation
Script for the automatic creation of sections in cyschoolhouse. Please ensure
you have all dependencies, and have set up the input file called "section-creator-input.csv"
in the input files folder.

"""
import pandas as pd
import cyschoolhousesuite as cysh
from selenium.webdriver.support.ui import Select
from time import sleep
import logging

def import_parameters():
    """Import configuration data from Excel.
    """
    data = pd.read_excel('input_files/section-creator-input.xlsx')
    return data.to_dict(orient='records')

def nav_to_section_creation_form(driver):
    """Navigate to section creation form
    
    Must already be logged into SalesForce
    """
    driver.get('https://na24.salesforce.com/a1A/o')
    driver.find_element_by_name("new").click()
    sleep(2)

def input_staff_name(driver, staff_name):
    """Selects the staff name from the drop down
    """
    dropdown = Select(driver.find_element_by_id("j_id0:j_id1:staffID"))
    dropdown.select_by_visible_text(staff_name)

def fill_static_elements(driver):
    """Fills in the static fields in the section creation form
    
    Includes the start/end dat, days of week, if time is in or out of school,
    and the estimated amount of time for that section.
    """
    driver.find_element_by_id("j_id0:j_id1:startDateID").send_keys("08/14/2017")
    driver.find_element_by_id("j_id0:j_id1:endDateID").send_keys("06/15/2018")
    driver.find_element_by_id("j_id0:j_id1:freqID:1").click()
    driver.find_element_by_id("j_id0:j_id1:freqID:2").click()
    driver.find_element_by_id("j_id0:j_id1:freqID:3").click()
    driver.find_element_by_id("j_id0:j_id1:freqID:4").click()
    driver.find_element_by_id("j_id0:j_id1:freqID:5").click()
    dropdown = Select(driver.find_element_by_id("j_id0:j_id1:inAfterID"))
    dropdown.select_by_visible_text("In School")
    driver.find_element_by_id("j_id0:j_id1:totalDosageID").send_keys("900")
    sleep(2)

def select_school(driver, school):
    """ Selects the school name from section creation form
    """
    dropdown = Select(driver.find_element_by_id("j_id0:j_id1:school-selector"))
    dropdown.select_by_visible_text(school)

def select_subject(driver, section_name):
    """ Selects the section type
    """
    try:
        driver.find_element_by_xpath("//label[contains(text(), '"+ section_name +"')]").click()
        sleep(2)
        driver.find_element_by_xpath("//input[@value='Proceed']").click()
    except:
        print("Hopefully it's okay")
    
def save_section(driver):
    """ Saves the section
    """
    driver.find_element_by_css_selector('input.black_btn:nth-child(2)').click()
    sleep(2)

def update_nickname(driver, nickname):
    driver.find_element_by_css_selector('#topButtonRow > input:nth-child(3)').click()
    sleep(2)
    driver.find_element_by_id("00N1a000006Syte").send_keys(nickname)
    driver.find_element_by_xpath("//input[@value=' Save ']").click()
    sleep(2)

def create_single_section(driver, parameter):
    nav_to_section_creation_form(driver)
    select_school(driver, parameter['School'])
    sleep(2)
    select_subject(driver, parameter['SectionName'])
    sleep(2)
    input_staff_name(driver, parameter['ACM'])
    sleep(2)
    fill_static_elements(driver)
    save_section(driver)
    logging.info("Created {} section for {}".format(parameter['SectionName'], parameter['ACM']))
    update_nickname(driver, parameter['Nickname'])
    
    
        
# runs the entire script
def section_creation():
    params = import_parameters()
    driver = cysh.get_driver()
    cysh.open_cyschoolhouse18(driver)
    for p in params:
        try:
            create_single_section(driver, p)
        except:
            print("Section creation failed for {}".format(p['ACM']))
            logging.error("Section creation failed for {}".format(p['ACM']))
            driver.quit()
            driver = cysh.get_driver()
            cysh.open_cyschoolhouse18(driver)
            driver.find_element_by_xpath("//input[@value='Proceed']").click()
            continue
    driver.quit()
    
if __name__ == '__main__':
    section_creation()