# Minor Planet Center ephemeris and observations download and reduction
The mpc_down script is a software programmed in Python for the automatic download of observations of a specific object from the Minor Planet Center database. It is capable of reducing observations by perihelion distance and
distance to Earth. It is also useful for overlapping observations from different orbits by calculating the date relative to the perihelion and the orbital period.

The script performs the following tasks:
  1. It asks the user for the following information: the name of the object, the start date, and the end date of the interval from which the observations are to be obtained.
  2. It downloads from the MPC all existing observations for the given interval and also obtains the ephemerides for each observation date (∆, r, α). Additionally, if available, it retrieves for each object the date of
     perihelion (Tq) and its period.
  3. It asks the user if it is satisfied with the obtained perihelion and period data. If not, it requests the user to input new ones.
  4. It saves the total of the found observations without reducing, in a file in the **'Total Observations'** folder, with the following format; year, month, day, m(∆,r,α), filter, '∆', 'r', and 'α'.
  5. It obtains for each observation the days relative to perihelion (t - Tq). For comets with observations in multiple orbits, if the search covers several orbits, it aims to stack all observations as if it were a
     single orbit to obtain the Secular Light Curve. This involves subtracting or adding to t - Tq the orbital period (T) as many times as necessary until the value is in the set: [-T/2, T/2].
  6. It discards observations from unwanted filters.
  7. It applies to the observed magnitudes the ‘V’ band correction and obtains the absolute magnitude by reducing by ‘∆’ and ‘r’. That is, it obtains m(1,1,α).
  8. It saves in the **'Reduced Observations'** folder a file with the following format: year, month, day, t - Tq, '∆', 'r', 'α', m(∆,r,α), and m(1,1,α).
  9. It saves in the **'Plots'** folder a graph for the total observations (m(∆,r,α)) and another for the reduced observations (m(1,1,α)) to preview the data obtained before a more exhaustive analysis.

This code is a great help in studying the light curves of comets and asteroids, as it greatly speeds up the task of downloading and reducing data, a process that can take hours without this code.

## License
**This software is provided for scientific research purposes only. Any commercial use or redistribution of this software without the express written consent of the author(s) is strictly prohibited. The author is not 
responsible for any misuse of this code. By using this software, you agree to abide by these terms and conditions.**

## How to use it
Mpc_down can be used in two different ways:
  - Installation of a Python 3 IDE: One can proceed to install a free Python 3 interpreter to be able to read the file mpc_down_v5_1.py. There are many free Python interpreters available on the internet. Some of the
    most recommended include:
      - Anaconda
      - Spyder
      - PyDev
  - Use the executable: This is the simplest option. It simply involves clicking on the mpc_down_v5_1.exe file, and it will start running without the need for any installation. However, the executable file couldn't be
    uploaded to GitHub due to its large size. Download it from the following link: https://drive.google.com/file/d/1jVg6GiVUpIIXoWybNfzpRWIRZp18Qhzb/view?usp=drive_link .One can create an executable using the PyInstaller library with the following command: _>> pyinstaller --onefile mpc_down_v5_1.py_
