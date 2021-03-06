# -*- coding: utf-8 -*-
"""Excep Updater Wrapper Functions

This modules is intended to build a layer of abstraction on top of the win32com
api. The goal is for the user to be able to import this module into a script where they
acutally implament the updating of specific workbooks. 

"""
# Python Core packages
import os
from time import sleep, time

#from datetime import datetime
import sys
import logging

# win32 API 
import win32com.client as win32
import win32process
import win32gui
import win32api
import win32con

def open_excel():
    # Create a connector to Excel
    try:
        excel = win32.gencache.EnsureDispatch("Excel.Application")
        logging.debug(":".join([str(time()), "Excel Instance Closed"]))
    except:
        logging.critical(":".join([str(time()), "Failed to launch Excel, quit"]))
        return None
    #excel = win32.Dispatch("Excel.Application")
    #excel = win32.dynamic.Dispatch("Excel.Application")
    excel.Visible = True
    excel.DisplayAlerts = False
    
    return excel

def open_workbook(fp, excel):
    """Wraps some of the boilerplate that we have to open and work with Excel.
    
    Args:
        fp (str): Filepath of workbook to open
    Returns:
        win32 Excel Application driver: active driver to the open instance of Excel
        Excel Workbook Socket: The open socket to the workbook we opened
    """
    # Leverages the connector to open a particular workbook
    try:
        wb = excel.Workbooks.Open(fp)
        logging.debug(":".join([str(time()), "Opened " + fp]))
    except:
        logging.critical(":".join([str(time()), "Failed to open workbook"]))
        sys.exit(1)
        
    return wb

def refresh_save_quit(wb, protection, timer):
    """Refreshes, saves, and closes an open Excel workbook
    
    Args:
        wb (Excel Workbook Socket): The open socket to workbook to refresh
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] 
                                                       }
    """
    remove_sheet_protection(wb, protection)
    very_unhidden(wb, protection)
    wb.RefreshAll()
    sleep(timer)
    apply_sheet_protection(wb, protection)
    very_hidden(wb, protection)
    wb.Save()
    logging.debug("{}:refreshed and saved workbook successfully".format(time()))
    wb.Close(False)
    
def search_tree(parent_dir):
    """Searches the desginated parent dir and all subfolder, extracting the 
    filepaths and names of all files
    
    Args:
        parent_dir (str): The filepath of the parent directory
        
    Return:
        list: The list of 3-tuples with the dirpath, dirnames, and filesnames of 
        each child directory. 
    """
    children = [(dirpath, dirnames, filenames) for dirpath, dirnames, filenames in os.walk(parent_dir)]
    return children        

def get_all_filepaths(file_tree):
    """Construct the list of all files in terms of their filepath
    
    Args:
        file_tree (list): the list of tuples from search_tree
    Returns:
        list: the list of strings of all files as absolute file paths
    """
    return ['\\'.join([path, file]) for (path, child_dirs, files) in file_tree for file in files if file.endswith('.xlsm')]

def should_be_updated(file):
    """Validate that the file should be updated.
    
    """
    if file.startswith('~'):
        return False
    elif not ((file.endswith('xlsm')) |  (file.endswith('xlsx'))):
        return False
    else:
        return True

def apply_sheet_protection(wb, protection):
    """Apply sheet protection to sheets specified by protection dict
    
    Args:
        wb (Workbook socket): the workbook
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] }
    """
    sheetnames = protection.get('protect', [])
    for sheet in sheetnames:
        ws = wb.Sheets(sheet)
        ws.Protect(Password="Lighthouse", DrawingObjects=True, Contents=True, Scenarios=True)

def remove_sheet_protection(wb, protection):
    """Remove sheet protection to based on protection parameter dict
    
    Args:
        wb (Workbook socket): the workbook
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] }
    """
    sheetnames = protection.get('protect', [])
    for sheet in sheetnames:
        ws = wb.Sheets(sheet)
        ws.Unprotect(Password="Lighthouse")

def very_hidden(wb, protection):
    """Apply sheet protection to specified sheet(s)
    
    Args:
        wb (Workbook socket): the workbook
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] }
    """
    sheetnames = protection.get('veryhide', [])
    for sheet in sheetnames:
        ws = wb.Sheets(sheet)
        ws.Visible = 2
        
def very_unhidden(wb, protection):
    """Apply sheet protection to specified sheet(s)
    
    Args:
        wb (Workbook socket): the workbook
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] }
    """
    sheetnames = protection.get('veryhide', [])
    for sheet in sheetnames:
        ws = wb.Sheets(sheet)
        ws.Visible = -1

def update_single_workbook(file, path, excel, protection={}, timer=8):
    """Routine for updating a simple workbook
    
    Args:
        file (str): The name of the file to update
        path (str): The path to the folder containing the file
        excel (Excel Connector): The open win32 Excel Application driver
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] 
                                                       }
        timer (int): the amount of time workbooks will need to update all queries
    """
    if is_file_checked_out(file):
        return None
    wb = open_workbook('\\'.join([path, file]), excel)
    sleep(3)
    if is_pq_available(excel):
       refresh_save_quit(wb, protection, timer=timer)
    else:
        logging.critical(":".join([str(time()), "PowerQuery has been closed.  Please force close and open Excel."]))
        return None
    sleep(3)
    return None

def update_all(parent_dir, protection={}, timer=8, excel=''):
    """Script for updating the folder
    
    Args:
        parent_dir (str): Filepath of the top level directory to update.  Will recurse through children.
        protection (Dict): parameters for protection { protect : [sheetnames],
                                                       veryhide : [sheetnames] }
        timer (Int): The amount of time to pause after trigger the query update. Increase for larger workbooks.
        excel (Excel Connector): 
    """
    all_files = search_tree(parent_dir)
    if excel == '':
        excel = open_excel()
    for path, child_dirs, files in all_files:
        os.chdir(path)
        #print(path, child_dirs, files)
        for file in files:
            print(file)
            update_single_workbook(file, path, excel, protection, timer=timer)
    if excel == '':
        close_excel_by_force(excel)

def is_pq_available(excel):
    """Checks if PowerQuery is connected to Excel
    
    Args:
        excel (Excel Connector): Open Excel Connector
    Return:
        bool: True if PowerQuery is connected, False otherwise
    """
    return excel.COMAddIns("Microsoft.Mashup.Client.Excel").Connect

def close_excel_by_force(excel):
    """Script for force closing excel
    
    Excel frequently fails to close automatically, even when using the appropriate
    excel.quit() method.  So this forces the quit to happen.
    
    Args:
        excel (Excel Connector): Open Excel Connector
    """
    # Get the window's process id's
    hwnd = excel.Hwnd
    t, p = win32process.GetWindowThreadProcessId(hwnd)
    # Ask window nicely to close
    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    # Allow some time for app to close
    sleep(3)
    # If the application didn't close, force close
    try:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p)
        if handle:
            win32api.TerminateProcess(handle, 0)
            win32api.CloseHandle(handle)
    except:
        pass

def configure_log(log_folder):
    """Configures the log for update cycle
    
    Currently uses a log folder and creates a file called update_{timestamp}.log
    """
    fn = str(time()).split(".")[0]
    logging.basicConfig(filename="".join([log_folder, '/log/update_', fn, '.log']), level=logging.DEBUG)

def is_file_checked_out(filename):
    """Checks if file is checked out on SharePoint
    
    One of the biggest challenges in this script is catching the "File already open"
    error.  When this happen the file opens, but then a small window pops up informing
    you of the problem.  This kills the updater, because the small window is a hard
    error to actually interact with.  So, by apply this small rename check on each file
    we can confirm if it's already open or not and thus avoid the error. 
    
    Args:
        filename (str): the name of the file to check
    Returns:
        bool: True if the rename operation fails, implying that it's checked out
    
    """
    just_name = filename.split('.')[0]
    try: 
        os.rename(filename, just_name+filename)
    except OSError:
        logging.critical("{}:".format(time()) + filename + ' is still open. Has not been refreshed.')
        return True    
   
    sleep(3)
    try:
        os.rename(just_name+filename, filename)
        return False
    except OSError:
        logging.critical("{}:".format(time()) + filename + ' got locked out.  Will wait and try again.')
        sleep(3)
        try:
            os.rename(just_name+filename, filename)
            logging.debug("{}:".format(time()) + filename + ' unlocked.  Successfully reverted name.')
            return False
        except:
            logging.critical("{}:".format(time()) + filename + ' is still locked out. Will need a manual rename')
            return True

#if __name__ == '__main__':
#    fp = 'P:\\Update Zone\\Refresh Zone\\FL Workbooks'
#    fp = 'C:\\Users\\aperusse\\Desktop\\FiveFiles'
#    configure_log()
#    update_all(fp, {'protect':['Dashboard']})