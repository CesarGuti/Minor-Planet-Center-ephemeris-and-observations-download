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
# 2023-11-21 --> @Cesar G. de la Camara: The script now is able to obtain the
# perihelion date from MPC and adjust the observations date in relation to it. (v3)

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
    
    perihelion_date = None
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
        return successful_download, perihelion_date
    
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
        return successful_download, perihelion_date
    
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
    
    # Find the <td> tag with the 'perihelion date' and then find the next <td> for the date
    perihelion_date_tag = soup.find('td', text='perihelion date')
    perihelion_date_str = perihelion_date_tag.find_next('td').text
    
    # Process the date string to get rid of the decimal part
    date_str, _ = perihelion_date_str.split('.')
    perihelion_date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Ask the user if they agree with the found date
    user_input = input(f"The found perihelion date is {perihelion_date.date()}. Do you agree with this date? (yes/no): ")

    if user_input.lower() != 'yes':
        # If the user does not agree, ask for a new date
        new_date_str = input("Please enter a new perihelion date (YYYY-MM-DD): ")
        try:
            # Try to parse the new date
            perihelion_date = datetime.strptime(new_date_str, '%Y-%m-%d')
            print(f"The new perihelion date is set to: {perihelion_date.date()}")
        except ValueError as e:
            # Handle the error if the date format is incorrect
            print(f"Error: {e}. Please enter the date in the correct format.")
    
    return successful_download, perihelion_date
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
        date_to_print = (start_date + timedelta(days = days_to_download - 1)).strftime("%Y-%m-%d")
        print(f"Downloading ephemeris data until the {date_to_print}")
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
    
    print('Combining ephemeris and observations data')
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
    os.remove('downloaded_ephem_data.txt')
    os.remove('downloaded_obs_data.txt')
    print('Data combined successfully')
    
    return
#______________________________________________________________________________

def correct_dates_with_perihelion_date(perihelion_date):
    
    # Open the input file and create the output file
    with open('combined_data.txt', 'r') as input_file, open('modified_dates.txt', 'w') as output_file:
        for line in input_file:
            # Assuming the file is space or tab-delimited
            parts = line.strip().split()
            
            # Parse the date from the first three columns
            date_from_file = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            
            # Calculate the difference in days
            days_to_perihelion = (date_from_file - perihelion_date).days
            
            # Write the new line with the delta and the remaining parts
            new_line = ' '.join([str(days_to_perihelion)] + parts[3:])
            output_file.write(new_line + '\n')
    
    print('Dates successfully corrected with perihelion date')
    
    return
#______________________________________________________________________________

def rename_and_move_files(object_name, start_date, end_date):
    
    new_combined = f'{object_name}_total_observations_{start_date}_{end_date}.txt'
    new_reduced = f'{object_name}_reduced_observations_{start_date}_{end_date}.txt'

    total_obs_target_folder = 'Total observations'
    if not os.path.exists(total_obs_target_folder):
        os.makedirs(total_obs_target_folder)
    
    reduced_obs_target_folder = 'Reduced observations'
    if not os.path.exists(reduced_obs_target_folder):
        os.makedirs(reduced_obs_target_folder)

    # Rename and move new files
    os.rename('combined_data.txt', os.path.join(total_obs_target_folder, new_combined))
    os.rename('modified_dates.txt', os.path.join(reduced_obs_target_folder, new_reduced))

    # Delete auxiliary files
    if os.path.exists('combined_data.txt'):
        os.remove('combined_data.txt')
    if os.path.exists('modified_dates.txt'):
        os.remove('modified_dates.txt')

    

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
        success_down_obs, perihelion_date = download_observations(object_name)
        if success_down_obs == 0:
            print("There was an error downloading observations data.")
            break
        
        # Combining data
        combine_data()
        
        # Correcting dates
        correct_dates_with_perihelion_date(perihelion_date)
        
        # Renaming files
        rename_and_move_files(object_name, start_date, end_date)
        
        break
