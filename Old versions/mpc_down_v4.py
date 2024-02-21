# -*- coding: utf-8 -*-
"""
===============================================================================
                                PURPOSE
===============================================================================
"""
# The following script is used to download ephemerides data and observation 
# data from the Minor Planet Center database.
#
# The script combine ephemeris and observations data into a single file (Total
# Observations). This file contains the following columns: year, month, day,
# observed magnitud, used filter, distance from Earth (delta), distance from
# Sun (r) and orbit phase (alpha).
#
# In addition, the data is reduced (Reduced Observations). The dates are 
# converted to days relative to perihelion, observations from certain filters 
# are discarded, the observed magnitudes are corrected by delta and r, and a V
# band correction is also applied.

"""
===============================================================================
                               CHANGE LOG
===============================================================================
"""
# 2023-11-01 --> @Cesar G. de la Camara: RELEASE (python 3.9) (v1)
#
# 2023-11-07 --> @Cesar G. de la Camara: The user enters a start and end date 
# and the script itself makes as many ephemeris requests as necessary to fill 
# that entered time interval. We no longer have a 4001 day restriction. Additionally,
# multiple observations for the same day are taken into account.(v2)
#
# 2023-11-21 --> @Cesar G. de la Camara: The script now is able to obtain the
# perihelion date from MPC and adjust the observations date in relation to it. (v3)
#
# 2023-11-27 --> @Cesar G. de la Camara: The script now is able to obtain, not
# only the perihelion date from MPC, but also the period in order to be able to
# overlap observations from multiple orbits. Finally, the observed magnitudes
# are reduced. (v4)

"""
===============================================================================
                               LIBRARIES
===============================================================================
"""
import requests
import math
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

# Filters correction to V
v_band_correction = {'blank': [0],
                    'U': [-1.3],
                    'B': [-0.8],
                    'g': [-0.35],
                    'V': [0],
                    'r': [0.14],
                    'R': [0.4],
                    'C': [0.4],
                    'W': [0.4],
                    'i': [0.32],
                    'z': [0.26],
                    'I': [0.8],
                    'J': [1.2],
                    'w': [-0.13],
                    'y': [0.32],
                    'L': [0.2],
                    'H': [1.4],
                    'K': [1.7],
                    'Y': [0.7],
                    'G': [0.28],
                    'v': [0],
                    'c': [-0.05],
                    'o': [0.33],
                    'u': [2.5],
                    'N': [0], # Nuclear observations
                    'T': [0], # Total observations
                    }
# Discarted filters
discarded_filters = ['U', 'u', 'B', 'I', 'J', 'H', 'K']

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
    period = None
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
        return successful_download, perihelion_date, period
    
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
        return successful_download, perihelion_date, period
    
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
    
    #----PERIHELION DATE & PERIOD RETRIEVE-------------------------------------
    perihelion_date = None
    period = None
    
    # Find the <td> tag with the 'perihelion date' and then find the next <td> for the date
    perihelion_date_tag = soup.find('td', text='perihelion date')
    perihelion_date_str = perihelion_date_tag.find_next('td').text
    
    # Find the <td> tag with the 'period (years)' and then find the next <td> for the date
    period_tag = soup.find('td', text='period (years)')
    period_str = period_tag.find_next('td').text
    
    # Check that values of the perihelion date and period have been found
    perihelion_date_found = bool(perihelion_date_str.strip())
    period_found = bool(period_str.strip())
    if (not perihelion_date_found) and (not period_found):
        print("No value has been found either for the perihelion date or the period")
        perihelion_date = new_perihelion_or_period(False, True)
        period = new_perihelion_or_period(True,False)
        
    elif not bool(perihelion_date_str.strip()):
        print("No value found for perihelion date")
        perihelion_date = new_perihelion_or_period(False, True )
        period = float(period_str) * 365.25
        print(f"The found period is {period_str} years ({str(period)} days)")
        
    elif not bool(period_str.strip()):
        print("No value found for period")
        period = new_perihelion_or_period(True, False)
        date_str, _ = perihelion_date_str.split('.')
        perihelion_date = datetime.strptime(date_str, '%Y-%m-%d')
        print(f"The found perihelion date is {perihelion_date.date()}")
        
    else:     
        # Process the perihelion date string to get rid of the decimal part
        date_str, _ = perihelion_date_str.split('.')
        perihelion_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Convert the period value from years to days
        period = float(period_str) * 365.25  
        
        # Ask the user if they agree with the found values
        print(f"The found perihelion date is {perihelion_date.date()}")
        print(f"The found period is {period_str} years ({str(period)} days)")
        
    # Check if user agree with the values
    user_input = input("Do you agree with these values? (yes/no): ")

    if user_input.lower() != 'yes':
        perihelion_date = new_perihelion_or_period(False, True)
        period = new_perihelion_or_period(True,False)
        
    return successful_download, perihelion_date, period
#______________________________________________________________________________
def new_perihelion_or_period(valid_perihelion_date, valid_period):
    
    new_value = None
    if  not valid_perihelion_date:
        new_date_str = input("Please enter a new perihelion date (YYYY-MM-DD): ")
        try:
            # Try to parse the new date
            perihelion_date = datetime.strptime(new_date_str, '%Y-%m-%d')
            print(f"The new perihelion date is set to: {perihelion_date.date()}")
            new_value = perihelion_date
        except ValueError as e:
            # Handle the error if the date format is incorrect
            print(f"Error: {e}. Please enter the date in the correct format.")
    
    elif not valid_period:
        new_period_str = input("Please enter a new period value (in days): ")
        try:
            # Try to parse the period
            period = float(new_period_str)
            print(f"The new period value is set to: {new_period_str} days")
            new_value = period
        except ValueError as e:
            # Handle the error if the period format is incorrect
            print(f"Error: {e}. Please enter the period value in the correct format.")
    
    return new_value
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
        
    print(f"{n_obs} total observations have been found for the defined interval")
                    
    
    # Delete auxiliary files
    os.remove('downloaded_ephem_data.txt')
    os.remove('downloaded_obs_data.txt')
    
    return n_obs
#______________________________________________________________________________

def correct_dates(perihelion_date, period):
   
    with open('combined_data.txt', 'r') as infile, open('modified_dates.txt', 'w') as outfile:
        for line in infile:
            parts = line.split()
    
            # Be sure that selected line is valid
            if len(parts) < 3:
                continue
    
            # Build date with firts three columns
            year, month, day = parts[:3]
            date_str = f"{year}-{month}-{day}"
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
    
            delta_days = (current_date - perihelion_date).days
    
            # Adjust delta_days to fit in the interval [- period/2, period/2]
            while delta_days < - period / 2:
                delta_days += period
            while delta_days > period / 2:
                delta_days -= period
            
            # Round to the nearest integer
            delta_days_rounded = round(delta_days)
    
            # Type new line
            modified_line = f"{delta_days_rounded} " + " ".join(parts[3:]) + " " + " ".join(parts[:3]) + "\n"
            outfile.write(modified_line)
    
    print('Dates successfully corrected with perihelion date and period')
    
    return
#______________________________________________________________________________

def reduce_magnitudes():
    
    # Discarding useless filters
    n_discarded_obs = 0
    n_obs_left = 0
    filters_message = ', '.join(discarded_filters)
    print(f"Discarding observations made with the following filters: {filters_message}")
    print('Reducing observations')
    
    with open('modified_dates.txt', 'r') as infile, open('reduced_data.txt', 'w') as outfile:
        for line in infile:
            parts = line.split()
            m_observed = float(parts[1])
            filter_value = parts[2]
            delta_value = float(parts[3])
            r_value = float(parts[4])
            
            if filter_value not in discarded_filters:
                # Reducing magnitudes by delta and r and applying V band correction, rounding by 2 decimals
                m_abs = round(m_observed - 5*math.log10(delta_value*r_value) + v_band_correction[filter_value][0], 2)
                # Output line: year month day t-tq delta r phase m_observed m_abs
                outfile.write(f"{parts[6]} {parts[7]} {parts[8]} {parts[0]} {parts[3]} {parts[4]} {parts[5]} {parts[1]} {str(m_abs)} \n")
                n_obs_left += 1
            else:
                n_discarded_obs += 1
    
    print(f"{str(n_discarded_obs)} observations have been discarded. {str(n_obs_left)} observations left ")
    
    if n_obs_left != 0:
        print('Observations reduced successfully')
    
    # Delete auxiliary files
    if os.path.exists('modified_dates.txt'):
        os.remove('modified_dates.txt')
        
    return n_obs_left
    
    
    
#______________________________________________________________________________

def rename_and_move_files(object_name, start_date, end_date, n_obs_left):
    
    new_object_name = object_name.replace("\\", "_").replace("/", "_").replace(" ", "_")
    new_combined = f'{new_object_name}_total_observations_{start_date}_{end_date}.txt'
    new_reduced = f'{new_object_name}_reduced_observations_{start_date}_{end_date}.txt'

    total_obs_target_folder = 'Total observations'
    if not os.path.exists(total_obs_target_folder):
        os.makedirs(total_obs_target_folder)
    
    reduced_obs_target_folder = 'Reduced observations'
    if not os.path.exists(reduced_obs_target_folder):
        os.makedirs(reduced_obs_target_folder)

    # Rename and move new files
    os.rename('combined_data.txt', os.path.join(total_obs_target_folder, new_combined))
    if n_obs_left != 0:
        os.rename('reduced_data.txt', os.path.join(reduced_obs_target_folder, new_reduced))

    # Delete auxiliary files
    if os.path.exists('combined_data.txt'):
        os.remove('combined_data.txt')
    if os.path.exists('reduced_data.txt'):
        os.remove('reduced_data.txt')

    

"""
===============================================================================
                               PROGRAM
===============================================================================
""" 

if __name__ == "__main__":
    
    while True:
        # Asking user for inputs
        object_name, start_date, end_date = user_input()
        
        #Downloading ephemeris data
        success_down_ephem = download_ephem_for_period(start_date, end_date, object_name)
        if success_down_ephem == 0:
            print("There was an error downloading ephemeris data.")
            break
        
        # Downloading observations data
        success_down_obs, perihelion_date, period = download_observations(object_name)
        if success_down_obs == 0:
            print("There was an error downloading observations data.")
            break
        
        # Combining data
        n_obs = combine_data()
        
        if n_obs != 0:
            
            # Correcting dates
            correct_dates(perihelion_date, period)
            
            # Selecting by filter and reducing (by r and delta) the observations magnitudes
            n_obs_left = reduce_magnitudes()
            
            # Renaming files
            rename_and_move_files(object_name, start_date, end_date, n_obs_left)
        else:
            # Delete remaining auxiliary files
            if os.path.exists('combined_data.txt'):
                os.remove('combined_data.txt')  
        
        break
