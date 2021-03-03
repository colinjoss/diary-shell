# Author: Colin Joss
# Last date updated: 3-2-2021
# Description: A simple python program for my personal diary system, made with the intention to
#              speed up the process of maintaining it.

import datetime
from datetime import datetime as dt
import os
import inquirer
from mutagen.mp3 import MP3
import math
import csv
from pyfiglet import Figlet
import calendar
import pandas as pd


class Diary:
    def __init__(self):
        with open("diary-data.csv", "r", newline="") as infile:
            self._entries = pd.read_csv(infile)

        self.title()
        self.calendar()
        self.main_menu()

    @staticmethod
    def title():
        """Displays the title of the program."""
        custom_fig = Figlet(font='slant')
        print(custom_fig.renderText('AUTO - DIARY'))
        print("Program by Colin Joss")
        print("-----------------------------------------\n")

    @staticmethod
    def calendar():
        """Displays the current calendar."""
        date = datetime.date.today().strftime("%B %d %Y")
        weekday = datetime.date.today().strftime("%A")
        print(f"Today is {weekday} {date}\n")
        year = datetime.date.today().year
        month = datetime.date.today().month
        print(calendar.month(year, month))

    def main_menu(self):
        """Presents a main menu to the user in the terminal."""
        close_program = False
        while close_program is False:
            selection = self.list_selection(["Update", "Search", "Close"])

            # Prompts user through the diary updating process
            if selection == "Update":
                self.update_diary()

            # Prompts user to search and returns a csv with the results
            elif selection == "Search":
                keyword = str(input("Enter a search term: "))
                search_results = self.search_by_keyword(keyword)
                self.create_search_csv(keyword, search_results)

            # Exits, saves, and updates the yearly csv and stats csv
            else:
                close_program = True
                self.update_statistics_csv(self.get_last_date_updated())
                print("Goodbye!")

    def update_diary(self):
        """Records new diary entry(s)."""
        today = self.get_current_date()
        last_entry = self.get_last_date_updated()

        # If there are entries missing, prompts the user to do those first!
        if last_entry != today:
            missing_days = self.get_missing_entry_dates(last_entry, today)
            print(missing_days)
            self.catch_up(missing_days)
            selection = self.list_selection(["Yes", "No"], "Would you like to skip today?")
            if selection == "Yes":
                return True

        # Prompts user to update the diary for today's date
        entry = self.new_entry(self.get_current_date(), self.get_current_year(),
                               self.get_current_month(), self.get_current_weekday())
        self.append_to_csv(entry)

    @staticmethod
    def get_missing_entry_dates(last_entry, today):
        """Calculates the difference between the date of the last entry and
        the current date, then returns a list of dates."""
        missing = []
        one_less_day = None
        less = 1

        # Collects dates in list between the current date and the date of the last entry
        while one_less_day != last_entry:
            if one_less_day is not None:
                missing.append(one_less_day)
            one_less_day = (dt.strptime(today, '%m/%d/%y') - datetime.timedelta(days=less)).strftime('%m/%d/%Y')
            less += 1
        missing.reverse()
        return missing

    def catch_up(self, missing_days):
        """Prompts the user to catch up on missed days with no diary entries."""
        print('You need to catch up on some days! Update these first. \n')
        for day in missing_days:
            date_object = dt.strptime(day, '%m/%d/%Y')
            date = day
            year = date_object.strftime('%Y')
            month = date_object.strftime('%B')
            weekday = date_object.strftime('%A')
            entry = self.new_entry(date, year, month, weekday)
            self.append_to_csv(entry)

    def new_entry(self, date, year, month, weekday):
        """Prompts the user through the components of a diary entry, and
        then adds the entry to the list of all entries."""
        date = date
        year = year
        month = month
        weekday = weekday
        summary = self.get_summary_from_user(date, weekday)
        happiness = self.get_happiness_from_user()
        duration = self.get_mp3_file_length()
        people = self.get_people_from_user()

        return [date, year, month, weekday, summary, happiness, duration, people]

    def search_by_keyword(self, keyword):
        """Accepts a search keyword and returns a list of matches."""
        search_results = []
        for row in self._entries:
            if row[2] is None or isinstance(row[2], str) is False:
                continue

            # Searches for a keyword match each entry's summary
            if keyword.lower() in row[2].lower():
                search_results.append(row)

        return search_results

    @staticmethod
    def create_search_csv(keyword, search_results):
        """Creates a csv file based on search results."""
        if not search_results:
            return print("No results.\n")

        with open(f"{keyword.lower()}_{datetime.date.today()}.csv", "w", newline="") as infile:
            csv_writer = csv.writer(infile)
            csv_writer.writerows(search_results)
        print("Search results successfully generated!\n")

    def update_statistics_csv(self, last_entry):
        """Automatically calculates a set of statistics from my diary and
        organizes it in a csv."""
        print(self.get_total_files())
        if last_entry is None:
            return None

        # Generates list of all complete years (except 2013, a partial)
        current_year = int(self.get_current_year())
        total_years = []
        while current_year != 2013:
            current_year = current_year - 1
            total_years.append(current_year)

        # Calculate key statistics for every available year
        for year in total_years:
            current_year = self._entries.loc[self._entries['year'] == year]
            year_happiness = current_year.describe()['happiness']['mean']

            # Calculate lists of months and weekdays ranked by happiness, people ranked by mentions
            months_ranked = self.calculate_happiest_month(current_year)
            weekdays_ranked = self.calculate_happiest_weekday(current_year)
            people_ranked = self.calculate_most_mentioned(current_year)

            # Updates the stats spreadsheet
            v = 'w' if year == int(self.get_current_year())-1 else 'a'
            with open('statistics.csv', f'{v}', newline="") as outfile:
                pd.DataFrame({year: year_happiness}, index=[year]).to_csv(outfile)
                pd.DataFrame(months_ranked, index=[year]).to_csv(outfile)
                pd.DataFrame(weekdays_ranked, index=[year]).to_csv(outfile)
                pd.DataFrame(people_ranked, index=[year])[0:10].to_csv(outfile)

    def calculate_happiest_month(self, current_year):
        """Takes the current year and returns a dictionary of the months in that
        year sorted by their happiness rating."""
        months_ranked = {}
        for month in ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'November', 'December']:
            current_month = current_year.loc[current_year['month'] == month]
            month_happiness = current_month.describe()['happiness']['mean']
            months_ranked[month] = month_happiness

        return self.sort_dict_by_value(months_ranked, True)

    def calculate_happiest_weekday(self, current_year):
        """Takes the current year and returns a dictionary of the weekdays in that
        year sorted by their happiness rating."""
        weekdays_ranked = {}
        for weekday in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            current_weekday = current_year.loc[current_year['weekday'] == weekday]
            month_happiness = current_weekday.describe()['happiness']['mean']
            weekdays_ranked[weekday] = month_happiness

        return self.sort_dict_by_value(weekdays_ranked, True)

    def calculate_most_mentioned(self, current_year):
        """Takes the current year and returns a dictionary of the people mentioned
        that year sorted by how many times they were mentioned."""
        people_ranked = {}
        for people in current_year['people'].tolist():
            if isinstance(people, str) is False:
                continue

            for person in people.split(', '):
                if person not in people_ranked:
                    people_ranked[person.title()] = 1
                else:
                    people_ranked[person.title()] += 1

        return self.sort_dict_by_value(people_ranked, True)

    # Getters and helpers --------------------------------------

    @staticmethod
    def get_current_date():
        """Returns the current date."""
        return datetime.date.today().strftime("%m/%d/%y")

    @staticmethod
    def get_current_weekday():
        """Returns the current day of the week as a string."""
        return datetime.date.today().strftime("%A")

    @staticmethod
    def get_current_month():
        """Returns the current month of the year as a string."""
        return datetime.date.today().strftime("%B")

    @staticmethod
    def get_current_year():
        """Returns the current year as a string."""
        return datetime.date.today().strftime("%Y")

    def get_last_date_updated(self):
        """Returns the most recent diary entry, or None if there are
        no entries."""
        if self._entries is None:
            return None
        date_object = dt.strptime(self._entries['date'].iloc[-1], '%m/%d/%Y')
        return date_object.strftime('%m/%d/%Y')

    def get_total_entries(self):
        """Returns the total number of user-submitted entries."""
        return len(self._entries)

    def get_total_files(self):
        """Returns the total number of user-submitted files."""
        duration_df = self._entries['duration'].dropna()
        return len(duration_df)

    def get_total_length(self):
        """Calculates the sum total amount of recording time."""
        sum_in_seconds = 0
        for year in self._entries:
            for month in self._entries[year]:
                for entry in self._entries[year][month]:
                    if entry["length"] is None or entry["length"] == " ":
                        continue
                    hours, minutes, seconds = self.split_time(entry["length"])
                    hours = self.times_sixty(self.times_sixty(hours))
                    minutes = self.times_sixty(minutes)
                    sum_in_seconds += (hours + minutes + seconds)

        return self.convert_seconds_to_hms(sum_in_seconds)

    def get_mp3_file_length(self):
        """Prompts user to select an mp3 file and returns the length of
        the linked file if it is an mp3, but None if it is any other file type."""
        main_folder = os.getcwd()
        os.chdir(main_folder + "\\new-update-files")
        selection = self.list_selection(["No file"] + os.listdir(), "Which file?")
        if selection == "No file":
            os.chdir(main_folder)
            return None

        audio = MP3(main_folder + "\\new-update-files\\" + selection)
        length = audio.info.length
        hms_string = self.convert_seconds_to_hms(length)
        os.chdir(main_folder)
        return hms_string

    def append_to_csv(self, entry):
        # Appends new entry as a row to the data csv
        with open('diary-data.csv', 'a', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(entry)

        # Reloads the newly updated csv into the diary assistant program
        with open('diary-data.csv', 'r', newline='') as infile:
            self._entries = pd.read_csv(infile)

    @staticmethod
    def convert_seconds_to_hms(seconds):
        """Accepts a number of seconds and returns a string of the time,
        with hours and minutes, divided by colons."""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{math.floor(hours)}:{math.floor(minutes)}:{math.floor(seconds)}"

    @staticmethod
    def split_time(time):
        """Accepts a string formatted as "H:M:S:" and returns the hours,
        minutes, and seconds separately."""
        time_list = str(time).split(":")
        return int(time_list[0]), int(time_list[1]), int(time_list[2])

    @staticmethod
    def split_date(date):
        """Splits a hyphenated date into its year/month/day parts, and returns each as an int."""
        date_list = str(date).split("-")
        return int(date_list[0]), int(date_list[1]), int(date_list[2])

    @staticmethod
    def times_sixty(num):
        """Accepts a number and returns the product of it and 60."""
        return num * 60

    def check_new_year(self, year):
        """Checks if the current year is contained in self._entries, and if not, creates a new year."""
        if year not in self._entries:
            self._entries[year] = {}

    def check_new_month(self, year, month):
        """Checks if the current month is contained in self._entries, and if not, creates a new month."""
        if month not in self._entries[year]:
            self._entries[year][month] = []

    @staticmethod
    def get_summary_from_user(date, weekday):
        """Prompts the user through a detailed summary for a given date."""
        print(f"This is the summary for {weekday}, {date}.")
        print("Remember to be as detailed as possible - and to use as many "
              "KEYWORDS as you can! \n")
        morning = str(input("This morning, I... "))
        afternoon = str(input("In the afternoon, I... "))
        evening = str(input("During the evening, I... "))
        opinion = str(input("Overall, I'd say today was... "))

        summary = f"This morning, I {morning} In the afternoon, I {afternoon} " \
                  f"During the evening, I {evening} Overall, I'd say today was {opinion}"
        return summary

    def get_happiness_from_user(self):
        """Prompts users to select from a list of ratings and then returns that rating."""
        selection = self.list_selection([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                                        "How would you rate today?")
        return float(selection)

    def get_people_from_user(self):
        """Prompts users to input the names of people until they exit."""
        done = False
        count = 1
        people = []
        print("Please input all the names of people - first and last - who are noteworthy to this day.")
        while done is False:
            person = str(input(f"{count}: "))
            people.append(person)
            count += 1
            selection = self.list_selection(["Yes", "No"], "Add another name?")
            if selection == "No":
                done = True
        return people

    def get_year_from_user(self):
        """Prompts the user to input a valid year (contained within self._entries).
        Returns None if year is invalid."""
        year = str(input("Please input a year as a four-digit number: "))
        if len(year) != 4 or year not in self._entries:
            return None
        return year

    @staticmethod
    def sort_dict_by_value(my_dict, order):
        """Accepts a dictionary and returns the dictionary sorted by value."""
        return {k: v for k, v in sorted(  # Returns a new dictionary
            my_dict.items(),  # Selecting from the dictionary "happiness" as a list of tuples
            key=lambda pair: pair[1],  # Sorting according to the second item in the tuple, AKA the value
            reverse=bool(order))}  # Reversing because by default it sorts in ascending order

    def add_first_entry(self):
        self.new_entry(self.get_current_date(), self.get_current_year(),
                       self.get_current_month(), self.get_current_weekday())

    @staticmethod
    def list_selection(choices, message=""):
        """Receives a list of choices and an optional message, and users the inquirer
        module to present those options to the user. Returns the user selection."""
        options = [
            inquirer.List('list',
                          message=message,
                          choices=choices
                          )]
        selection = inquirer.prompt(options)
        return selection["list"]

    def search_by_date(self, search_date):
        """Accepts a search date and returns a list of matches."""
        matches = []
        for year in self._entries:
            for month in self._entries[year]:
                for entry in self._entries[year][month]:
                    if search_date in entry["date"]:
                        matches.append(entry)
        return matches

    @staticmethod
    def convert_num_to_month(num):
        """Accepts a number between 1-12 and returns matching month, or None if no match."""
        month_list = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        if 1 <= num <= 12:
            return month_list[int(num) - 1]
        return None

    # Extra functions for top-secret highly dangerous dev use ---------------------------------

    def import_stats_from_csv(self, filepath):
        """Takes a csv file, and if the file is formatted properly,
        pulls requisite data to create diary entries."""
        file = csv.reader(open(filepath))  # Opens the given file
        rows = list(file)

        for row in rows:  # Cycles through the rows, pulling data
            date = row[0]
            year, month, day = self.split_date(date)
            weekday = datetime.date(year, month, day).strftime("%A")
            month = self.convert_num_to_month(month)

            summary = None
            if row[1] != "" and row[1] is not None:
                summary = row[1].strip()

            happiness = None
            if row[2] != "" and row[2] is not None:
                happiness = float(row[2])

            length = None
            if row[3] != "" and row[3] is not None:
                length = row[3]

            people = []
            try:  # Gathers list of relevant people, or handles if none
                i = 4
                while row[i]:
                    people.append(str(row[i]))
                    i += 1
            except IndexError:
                pass

            if str(year) not in self._entries:  # Creates correct dicts / lists if new year / month
                self._entries[str(year)] = {}
            if str(month) not in self._entries[str(year)]:
                self._entries[str(year)][str(month)] = []

            self._entries[str(year)][str(month)].append({  # Creates a new diary entry
                "date": date,
                "weekday": weekday,
                "summary": summary,
                "happiness": happiness,
                "people": people,
                "length": length
            })

    def remove_string_from_summary(self, string):
        for year in self._entries:
            for month in self._entries[year]:
                for entry in self._entries[year][month]:
                    if entry["summary"] is None or entry["summary"] == "":
                        continue
                    if string.lower() in entry["summary"].lower():
                        new_summary = entry["summary"].replace(string, "")
                        entry["summary"] = new_summary

    def find_and_replace(self, find, replace):
        """Finds a string and replaces it with a new string."""
        for year in self._entries:
            for month in self._entries[year]:
                for entry in self._entries[year][month]:
                    if entry["people"] is None:
                        continue
                    for name in entry["people"]:
                        name.replace(find, replace)


if __name__ == '__main__':
    diary = Diary()
