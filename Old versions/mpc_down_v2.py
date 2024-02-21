# -*- coding: utf-8 -*-
"""
===============================================================================
                                PURPOSE
===============================================================================
"""
# The following script is used to download ephemerides data and observation 
# data from the Minor Planet Center database and combine them into a single 
# output file. The output file contains the columns: year, month, day, distance
# from Earth (delta), distance from Sun (r), phase, magnitude and filter.

"""
===============================================================================
                               CHANGE LOG
===============================================================================
"""
# 2023-11-01 --> @Cesar G. de la Camara: RELEASE (python 3.9) (v1)
# 2023-11-07 --> @Cesar G. de la Camara: The user enters a start and end date 
# and the script itself makes as many ephemeris requests as necessary to fill 
# that entered time interval. We no longer have a 4001 day restriction. Additionally,
# multiple observations for the same day are taken into account.(v2)

"""
===============================================================================
                               LIBRARIES
===============================================================================
"""
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

"""
===============================================================================
                               VARIABLES
===============================================================================
"""
# Default values for ephemeris form fields that if not sent gives an error
title = "Predefined title"
base_url = "Predefined base url"
interval = 1 # interval days between ephemeris samples

"""
===============================================================================
                               FUNCTIONS
===============================================================================
"""
def user_input():
    
    # Name
    object_name = input("Type the object name: ")
    
    # Start date of observations
    valid_start_date = False
    while not valid_start_date:
        start_date = input('Type the start date of observations (YYYY-MM-DD format): ')
        try:
            # Trying to convert the entered date into an object of type datetime
            date = datetime.strptime(start_date, '%Y-%m-%d')
            valid_start_date = True
        except ValueError:
            # If a ValueError exception occurs, the date is invalid
            print ('Invalid date. Please enter a valid date in YYYY-MM-DD format.')
    
    # End date of observations
    valid_end_date = False
    while not valid_end_date:
        end_date = input('Type the end date of observations (YYYY-MM-DD format): ')
        try:
            # Trying to convert the entered date into an object of type datetime
            date = datetime.strptime(end_date, '%Y-%m-%d')
            valid_end_date = True
        except ValueError:
            # If a ValueError exception occurs, the date is invalid
            print ('Invalid date. Please enter a valid date in YYYY-MM-DD format.')
    
    return object_name, start_date, end_date
#______________________________________________________________________________

def download_ephemeris(start_date, num_days, object_name, append_mode):
    
    # Form URL
    url_ephem = "https://cgi.minorplanetcenter.net/cgi-bin/mpeph2.cgi"
    
    # Request header
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Form fields needed:
    data = {
        'ty': 'e',  # Return ephemerides
        'd': start_date,    # Start date of ephemerides
        'l': num_days,  # Num days from start date
        'TextArea': object_name,    #Object name
        'i': interval,  # Sample interval
        'u': 'd',  # Sample interval measurments units = days
        'tit' : title,  
        'bu' : base_url,
        #... add more if needed
    }

    # Sending POST request with the form data
    print('Downloading ephemeris data')
    response = requests.post(url_ephem, data=data, headers=headers)
    successful_download = 0

    # If request succeded, process content
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        print('Success in submitting the ephemeris form')
        
        data_element = soup.find('pre')
    else:
        print('The ephemeris form submission was not successful')        
        return successful_download
        
    if data_element:
        data_text = data_element.text.splitlines()
        print('Available ephemeris data')
    else:
        print("Not available ephemeris data")
        print(response.text)     # -------------------->> Only for debugging
        return successful_download
    
    # Extract the columns of interest
    extracted_data = []
    for line in data_text:
        parts = line.split()
        if len(parts) > 13:  # To make sure it is a data line
            # Extract year, month, day, Delta, r and phase
            year, month, day, delta, r, phase = parts[0], parts[1], parts[2], parts[8], parts[9], parts[11]
            extracted_data.append(f"{year} {month} {day} {delta} {r} {phase}")
    
    # Write the extracted data into a .txt file
    file_mode = 'a' if append_mode else 'w'
    with open('downloaded_ephem_data.txt', file_mode) as file:
        for line in extracted_data:
            file.write(line + '\n')
            
    print('Ephemeris data stored successfully')
    successful_download = 1
    
    return successful_download
#______________________________________________________________________________

def download_observations(object_name):
    
    # Form url
    url_obs = "https://www.minorplanetcenter.net/db_search/show_object"
    
    # Form fields needed
    params = {
        'object_id': object_name
    }
    
    # Sending POST request with the form data
    print('Downloading observations data')
    response = requests.get(url_obs, params=params)
    successful_download = 0
    
    # If request succeded, process content
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        print('Success in submitting the observtions form')
    else:
        print('The observations form submission was not successful')
        return successful_download
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Search all tables
    tables = soup.find_all('table')
    
    # Select the one that has "Date (UT)" in header
    for table in tables:
        header = table.find('th')
        if header and "Date (UT)" in header.text:
            break
    else:
        print("Observations table wasn't found")
        return successful_download
    
    # Extract all rows
    rows = table.find_all('tr')[1:]  # [1:] para excluir el encabezado

    # Write only selected data into a .txt file
    with open('downloaded_obs_data.txt', 'w') as f:
        for row in rows:
            columns = row.find_all('td')
            
            # Extract date
            date = columns[0].text.split()
            year, month, day = date[0], date[1], date[2].split('.')[0]  # erase decimals
            
            # Extract Magn and filter
            magn = columns[3].text
            
            f.write(f"{year} {month} {day} {magn}\n")
    print('Observations data stored successfully')
    successful_download = 1
    
    return successful_download
#______________________________________________________________________________

def download_ephem_for_period(start_date, end_date, object_name):
   
    success_down_ephem = 0
    n_iterations = 0
    append_mode = False
    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Calculate the total number of days between start_date and end_date
    difference = (end_date - start_date).days + 1  # Include the end_date

    # Loop until the entire period is covered
    while difference > 0:
        
        if n_iterations == 1:
            append_mode = True
        # Determine the number of days to download in this iteration
        days_to_download = min(difference, 4001)
        
        # Call the download function with the current start date and the number of days
        success_down_ephem = download_ephemeris(start_date.strftime("%Y-%m-%d"), days_to_download, object_name, append_mode)
        if success_down_ephem == 0:
            break
        
        # Update start_date and the remaining difference
        start_date += timedelta(days=days_to_download)
        difference -= days_to_download
        n_iterations += 1
    
    return success_down_ephem
        
#______________________________________________________________________________

def read_obs_data(file_path):

    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            date = ' '.join(parts[0:3])  # Combine year, month and day
            # Verify that at least 5 columns exist before attempting to access them
            if len(parts) >= 5:
                # Save mag and filter
                values = (parts[3], parts[4])
                data[date] = values
    return data
#______________________________________________________________________________

def combine_data():
    
    n_obs = 0
    with open('combined_data.txt', 'w') as out_file, open('downloaded_obs_data.txt', 'r') as obs_file:
        obs_lines = obs_file.readlines()
        
        for obs_line in obs_lines:
            obs_parts = obs_line.strip().split()
            if len(obs_parts) >= 5:  # Asegurarse de que hay al menos 5 columnas
                obs_date = ' '.join(obs_parts[0:3])
                
                with open('downloaded_ephem_data.txt', 'r') as eph_file:
                    for eph_line in eph_file:
                        eph_parts = eph_line.strip().split()
                        eph_date = ' '.join(eph_parts[0:3])
                        
                        if eph_date == obs_date:
                            new_line = ' '.join(obs_parts + eph_parts[3:6]) + '\n'
                            out_file.write(new_line)
                            n_obs += 1
        
    print(f"{n_obs} observations have been found for the defined interval")
                    
    
    # Delete auxiliary files
    #os.remove('downloaded_ephem_data.txt')
    #os.remove('downloaded_obs_data.txt')
    print('Data combined successfully')
    
    return

"""
===============================================================================
                               PROGRAM
===============================================================================
""" 

if __name__ == "__main__":
    
    while True:
        # Asking user for inputs
        object_name, start_date, end_date = user_input()
        
        #Downloadig ephemeris data
        success_down_ephem = download_ephem_for_period(start_date, end_date, object_name)
        if success_down_ephem == 0:
            print("There was an error downloading ephemeris data.")
            break
        
        # Downloading observations data
        success_down_obs = download_observations(object_name)
        if success_down_obs == 0:
            print("There was an error downloading observations data.")
            break
        
        # Combining data
        combine_data()
        break
