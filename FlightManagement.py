import sqlite3
from datetime import datetime


class FlightManager:
    # Table creation
    pilots_table = """
    CREATE TABLE IF NOT EXISTS Pilots (
        PilotID INTEGER PRIMARY KEY,
        FirstName TEXT NOT NULL,
        LastName TEXT NOT NULL,
        LicenseNumber TEXT UNIQUE NOT NULL
    )
    """

    destinations_table = """
    CREATE TABLE IF NOT EXISTS Destinations (
        DestinationID INTEGER PRIMARY KEY,
        AirportCode TEXT UNIQUE NOT NULL,
        CityName TEXT NOT NULL,
        Country TEXT NOT NULL,
        TimeZone TEXT NOT NULL
    )
    """

    flights_table = """
    CREATE TABLE IF NOT EXISTS Flights (
        FlightID INTEGER PRIMARY KEY,
        FlightNumber TEXT NOT NULL,
        Origin TEXT NOT NULL,
        Destination TEXT NOT NULL,
        DepartureTime DATETIME NOT NULL,
        Status TEXT NOT NULL CHECK(Status IN ('Scheduled', 'Delayed', 'Cancelled', 'Completed')),
        PilotID INTEGER,
        FOREIGN KEY (PilotID) REFERENCES Pilots(PilotID)
    )
    """
    #additional table added
    deleted_destinations_table = """
    CREATE TABLE IF NOT EXISTS DeletedDestinations (
        DestinationID INTEGER PRIMARY KEY,
        AirportCode TEXT NOT NULL,
        CityName TEXT NOT NULL,
        Country TEXT NOT NULL,
        TimeZone TEXT NOT NULL
    )
    """

    def __init__(self):

        self.connect = sqlite3.connect("flights.db")
        self.cursor = self.connect.cursor()
        self.cursor.execute(self.pilots_table)
        self.cursor.execute(self.destinations_table)
        self.cursor.execute(self.flights_table)
        self.cursor.execute(self.deleted_destinations_table)

        #reduce the duplication of data and limit the sqlite integrity error
        self.cursor.execute("SELECT COUNT(*) FROM Flights")
        count = self.cursor.fetchone()[0]

        if count == 0:

        # Added sample data derived by chatgpt -> https://chatgpt.com/share/679a8fb4-dd80-800b-ae6d-43d082a6d29a
            pilot_data = [
                ("James", "Anderson", "LIC123456"),
                ("Sarah", "Thompson", "LIC789012"),
                ("Robert", "Williams", "LIC345678"),
                ("Emily", "Johnson", "LIC901234"),
                ("Michael", "Brown", "LIC567890")
            ]

            destination_data = [
                ("LHR", "London", "United Kingdom", "GMT"),
                ("JFK", "New York", "United States", "GMT-5"),
                ("CDG", "Paris", "France", "GMT+1"),
                ("DXB", "Dubai", "United Arab Emirates", "GMT+4"),
                ("SYD", "Sydney", "Australia", "GMT+11")
            ]

            flight_data = [
                ("BA101", "LHR", "JFK", "2025-02-01 08:30:00", "Scheduled", 1),
                ("AF302", "CDG", "DXB", "2025-02-01 12:15:00", "Delayed", 2),
                ("EK450", "DXB", "SYD", "2025-02-02 18:45:00", "Completed", 3),
                ("AA789", "JFK", "LHR", "2025-02-03 09:00:00", "Cancelled", 4),
                ("QF200", "SYD", "CDG", "2025-02-04 21:30:00", "Scheduled", 5)
            ]

            for pilot in pilot_data:
                self.cursor.execute("INSERT INTO Pilots (FirstName, LastName, LicenseNumber) VALUES (?, ?, ?)",
                                    pilot)

            for dest in destination_data:
                self.cursor.execute(
                    "INSERT INTO Destinations (AirportCode, CityName, Country, TimeZone) VALUES (?, ?, ?, ?)",
                    dest)

            for flight in flight_data:
                self.cursor.execute(
                    "INSERT INTO Flights (FlightNumber, Origin, Destination, DepartureTime, Status, PilotID) VALUES (?, ?, ?, ?, ?, ?)",
                    flight)

        self.connect.commit()




    def view_all_flights(self):
        # Join Flights and Pilots tables to get pilot names
        self.cursor.execute("""
                SELECT 
                    f.FlightNumber, 
                    f.Origin, 
                    f.Destination, 
                    f.DepartureTime, 
                    f.Status,
                    CASE 
                        WHEN p.FirstName IS NULL THEN 'NO PILOT ASSIGNED'
                        ELSE p.FirstName || ' ' || p.LastName 
                    END as PilotName
                FROM Flights f
                LEFT JOIN Pilots p ON f.PilotID = p.PilotID
            """)
        all_flights = self.cursor.fetchall()

        print("\nAll Flight Information:")
        print("-" * 85)
        print(f"{'Flight #':<10} {'From':<10} {'To':<10} {'Departure':<20} {'Status':<10} {'Pilot':<20}")
        print("-" * 85)
        #template to view in table format
        for flight in all_flights:
            pilot_name = flight[5] if flight[5] else "No Pilot Assigned"
            print(f"{flight[0]:<10} {flight[1]:<10} {flight[2]:<10} {flight[3]:<20} {flight[4]:<10} {pilot_name:<20}")

        print("-" * 85)



    def view_all_pilots(self):
        self.cursor.execute("""
            SELECT 
                p.PilotID,
                p.FirstName,
                p.LastName,
                p.LicenseNumber,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM Flights f 
                        WHERE f.PilotID = p.PilotID 
                        AND f.Status IN ('Scheduled', 'Delayed')
                    ) THEN 'NOT AVAILABLE'
                    ELSE 'AVAILABLE'
                END as Status
            FROM Pilots p
        """)
        pilots = self.cursor.fetchall()

        print("\nAll Pilots Information:")
        print("-" * 85)
        print(f"{'ID':<5} {'First Name':<15} {'Last Name':<15} {'License':<15} {'Status':<20}")
        print("-" * 85)

        for pilot in pilots:
            print(f"{pilot[0]:<5} {pilot[1]:<15} {pilot[2]:<15} {pilot[3]:<15} {pilot[4]:<20}")

        print("-" * 85)



    def add_destination(self):
        print("\nAdd New Destination:")
        airport = input("Enter airport code (e.g., LHR): ")
        city = input("Enter city name: ")
        country = input("Enter country: ")
        timezone = input("Enter timezone (e.g., GMT+1): ")

        # format into capital letters and noun (first letter capitalised)
        self.cursor.execute("""
            INSERT INTO Destinations (AirportCode, CityName, Country, TimeZone) 
            VALUES (?, ?, ?, ?)""", (airport.upper(), city.title(), country.title(), timezone.upper()))

        self.connect.commit()
        print("Destination added! Please find your added flight on the table below: ")
        self.view_destination()

    def remove_destination(self):
        self.view_destination()
        selection = input("Please choose a DESTINATION airport code you would like to remove (e.g. LHR): ")
        deletion = selection.upper()

        self.cursor.execute("""
                SELECT COUNT(*) FROM Flights 
                WHERE Destination = ? AND Status NOT IN ('Completed', 'Cancelled')
            """, (selection,))

        flights_count = self.cursor.fetchone()[0]

        if flights_count > 0:
            print(f"Error: Destination '{selection}' cannot be deleted as it has active flights.")

        elif flights_count == 0:
            self.cursor.execute("""
                           SELECT COUNT(*) FROM Flights 
                           WHERE Destination = ? AND (Status = 'Completed' OR Status = 'Cancelled')
                       """, (selection,))
            complete_cancel_count = self.cursor.fetchone()[0]

            if complete_cancel_count >0:
                confirm = input("Please enter \"CHECK\" to view all flight data and to then update the route: ")
                if confirm.upper() == "CHECK":
                    print("Here are all the flights:")
                    self.view_all_flights()
                    choice = input("Would you like to proceed? Enter Y for yes or N for no: ")
                    if choice.upper() == 'Y':
                        self.deleted_table_insertion(deletion)
                        self.cursor.execute(""" DELETE FROM Destinations WHERE AirportCode = ?""", (deletion,))
                        self.connect.commit()
                        print("Destination now deleted! Here are all the available destinations & flights:")
                        self.view_destination()

                    else:
                        self.remove_destination()



            else:
                self.deleted_table_insertion(deletion)
                self.cursor.execute(""" DELETE FROM Destinations WHERE AirportCode = ?""", (deletion,))
                self.connect.commit()
                print("Destination now deleted! Here are all the available destinations")
                self.view_destination()


        self.update_flight_data()
        self.view_all_flights()
    #method added to stop the deletion of the airport code where flights are in transit
    def update_flight_data(self):
        self.cursor.execute("""
            UPDATE Flights 
            SET Destination = '-'
            WHERE Destination NOT IN (
                SELECT AirportCode 
                FROM Destinations
            )
            AND (Status IN ('Completed', 'Cancelled') OR Status IS NULL)
        """)
        self.connect.commit()



    def deleted_table_insertion(self, airport_code):
        self.cursor.execute("""
                INSERT INTO DeletedDestinations (AirportCode, CityName, Country, TimeZone)
                SELECT AirportCode, CityName, Country, TimeZone 
                FROM Destinations 
                WHERE AirportCode = ?
            """, (airport_code,))

        self.connect.commit()



    def view_destination(self):
        self.cursor.execute(''' SELECT * FROM Destinations''')
        all_updated_destinations = self.cursor.fetchall()

        print("\nAll Available Destinations Information:")
        print("-" * 85)
        print(f"{'ID#':<10} {'Code':<10} {'City':<20} {'Country':<20} {'Timezone':<10}")
        print("-" * 85)

        for destination in all_updated_destinations:

            print(f"{destination[0]:<10} {destination[1]:<10} {destination[2]:<20} {destination[3]:<20} {destination[4]:<10}")

        print("-" * 85)


    def view_deleted_destinations(self):
        self.cursor.execute('''SELECT * FROM DeletedDestinations''')
        deleted_destinations = self.cursor.fetchall()

        print("\nDeleted Destinations:")
        print("-" * 100)
        print(f"{'ID#':<10} {'Code':<10} {'City':<20} {'Country':<20} {'Timezone':<10} ")
        print("-" * 100)

        for dest in deleted_destinations:
            print(f"{dest[0]:<10} {dest[1]:<10} {dest[2]:<20} {dest[3]:<20} {dest[4]:<10} ")

        print("-" * 100)




    def add_new_pilot(self):
        self.view_all_pilots()
        while True:
            print("\nAdd New Pilot:")
            first = input("Enter first name: ")
            last = input("Enter last name: ")
            license_num = input("Enter license number (e.g. LIC123456): ")

            #logic to check if pilot already in data assuming all licensce numbers are unique
            self.cursor.execute(""" SELECT COUNT (*) FROM Pilots WHERE LicenseNumber = ?""", (license_num,))
            count = self.cursor.fetchone()[0]
            if count>0:
                print("Pilot license number already exists, please try again!")
                continue

            self.cursor.execute("""
                   INSERT INTO Pilots (FirstName, LastName, LicenseNumber) 
                   VALUES (?, ?, ?)""", (first.title(), last.title(), license_num.upper()))
            self.connect.commit()
            print("Pilot added! Here is the updated list of all pilots")
            self.view_all_pilots()




    def add_new_flight(self):
        print("\nAdd New Flight:")

        # Check flight number doesnt already exist
        while True:
            flight_num = input("Enter new flight number (e.g. BA123): ").upper()
            self.cursor.execute("SELECT COUNT(*) FROM Flights WHERE FlightNumber = ?", (flight_num,))
            if self.cursor.fetchone()[0] > 0:
                print("Flight number already exists. Please try again.")
            else:
                break

        # Show available destinations and check it exists, ensuring that origin isnt the same as destination aswell
        print("\nAvailable Destinations:")
        self.view_destination()

        while True:
            origin = input("Enter origin airport code from above (e.g. LHR): ").upper()
            self.cursor.execute("SELECT COUNT(*) FROM Destinations WHERE AirportCode = ?", (origin,))
            if self.cursor.fetchone()[0] == 0:
                print("Origin airport does not exist in our listings. Please try again.")
            else:
                break

        while True:
            destination = input("Enter destination airport code from above: ").upper()
            if destination == origin:
                print("Destination cannot be the same as origin!")
                continue

            self.cursor.execute("SELECT COUNT(*) FROM Destinations WHERE AirportCode = ?", (destination,))
            if self.cursor.fetchone()[0] == 0:
                print("Destination airport does not exist in our listings. Please try again.")
            else:
                break

        # Get departure time
        print("Please now follow the date format to insert the departure time: ")
        departure = self.get_datetime_input()

        # Check pilot availability
        print("\nCurrent Pilots:")
        self.view_all_pilots()

        #select pilot
        pilot_id = self.select_available_pilot_only(departure)
        if pilot_id is None:
            print("Flight creation cancelled")
            return

        # Insert the new flight
        self.cursor.execute("""
            INSERT INTO Flights (FlightNumber, Origin, Destination, DepartureTime, Status, PilotID) 
            VALUES (?, ?, ?, ?, 'Scheduled', ?)
        """, (flight_num, origin, destination, departure, pilot_id))

        self.connect.commit()
        print("Flight added! Here are all current flights:")
        self.view_all_flights()




    def amend_flight(self):
        print("Here are all the current flights: ")
        self.view_all_flights()

        # check if flight number exists
        while True:
            flight_number = input("\nEnter Flight Number to change (e.g. XX123): ").upper()
            self.cursor.execute("SELECT COUNT(*) FROM Flights WHERE FlightNumber = ?", (flight_number,))
            if self.cursor.fetchone()[0] > 0:
                break
            print("Flight number not found. Please try again.")

        # change flight number
        if input("Do you want to change the Flight Number? (Y/N): ").upper() == 'Y':
            while True:
                new_number = input("New flight number: ").upper()
                if 2 <= len(new_number) <= 6:  # Basic validation
                    self.cursor.execute("UPDATE Flights SET FlightNumber = ? WHERE FlightNumber = ?",(new_number, flight_number))
                    flight_number = new_number  # Update reference for subsequent changes
                    break
                print("Flight number must be 2-6 characters.") #change so its 2 letters followed by 4 numbers

        # change origin as long as it exists in list
        if input("Do you want to Change Origin? (Y/N): ").upper() == 'Y':
            print("\nCurrent destinations:")
            self.view_destination()
            while True:
                new_origin = input("New origin airport code: ").upper()
                self.cursor.execute("SELECT COUNT(*) FROM Destinations WHERE AirportCode = ?", (new_origin,))
                if self.cursor.fetchone()[0] > 0:
                    self.cursor.execute("UPDATE Flights SET Origin = ? WHERE FlightNumber = ?",(new_origin, flight_number))
                    break
                print("Airport code not found. Please choose from the list above.")

        # change destination
        if input("Do you want to change Destination? (Y/N): ").upper() == 'Y':
            print("\nCurrent destinations:")
            self.view_destination()
            while True:
                new_dest = input("New destination airport code: ").upper()
                self.cursor.execute("SELECT COUNT(*) FROM Destinations WHERE AirportCode = ?", (new_dest,))
                if self.cursor.fetchone()[0] > 0:
                    self.cursor.execute("UPDATE Flights SET Destination = ? WHERE FlightNumber = ?",
                                        (new_dest, flight_number))
                    break
                print("Airport code not found. Please choose from the list above.")

        # change departure time
        if input("Do you want to change Departure Time? (Y/N): ").upper() == 'Y':
            new_time = self.get_datetime_input()
            self.cursor.execute("UPDATE Flights SET DepartureTime = ? WHERE FlightNumber = ?",
                                (new_time, flight_number))

        # change pilot
        if input("Do you want to Change Pilot? (Y/N): ").upper() == 'Y':
            # Get current flight's departure time again to apply to function
            self.cursor.execute("SELECT DepartureTime FROM Flights WHERE FlightNumber = ?", (flight_number,))
            departure_time = self.cursor.fetchone()[0]

            new_pilot = self.select_available_pilot_only(departure_time)
            if new_pilot is not None:
                self.cursor.execute("UPDATE Flights SET PilotID = ? WHERE FlightNumber = ?",
                                    (new_pilot, flight_number))

        # change flight status
        if input("Change Flight Status? (Y/N): ").upper() == 'Y':
            print("\nValid statuses: Scheduled, Delayed, Cancelled, Completed")
            while True:
                new_status = input("Enter new status: ").title()
                if new_status in ['Scheduled', 'Delayed', 'Cancelled', 'Completed']:
                    self.cursor.execute("UPDATE Flights SET Status = ? WHERE FlightNumber = ?",
                                        (new_status, flight_number))
                    break
                print("Invalid status. Please choose from the list above.")

        self.connect.commit()
        print("\nFlight updated successfully! Updated flight details:")
        self.cursor.execute("""
            SELECT f.*, p.FirstName, p.LastName 
            FROM Flights f 
            LEFT JOIN Pilots p ON f.PilotID = p.PilotID 
            WHERE f.FlightNumber = ?
        """, (flight_number,))
        print("Here are the updated flights")
        self.view_all_flights()

    def select_available_pilot_only (self, departure_time):

        print("\nCurrent Pilots:")
        self.view_all_pilots()

        while True:
            pilot_id = input("Enter pilot ID from list above: ")

            # Check if pilot exists
            self.cursor.execute("SELECT COUNT(*) FROM Pilots WHERE PilotID = ?", (pilot_id,))
            if self.cursor.fetchone()[0] == 0:
                print("Invalid pilot ID. Please try again.")
                continue

            # to check if pilot has conflicting flights
            self.cursor.execute("""
                SELECT COUNT(*) FROM Flights WHERE PilotID = ? 
                AND Status IN ('Scheduled', 'Delayed')
                AND (
                    datetime(DepartureTime, '-12 hours') <= datetime(?)
                    AND datetime(DepartureTime, '+12 hours') >= datetime(?)
                )
            """, (pilot_id, departure_time, departure_time))

            if self.cursor.fetchone()[0] > 0:
                print("Pilot is not available as they are flying 12 hours of this flight time: ")
                self.cursor.execute("""
                    SELECT FlightNumber, DepartureTime, Status FROM Flights WHERE PilotID = ? 
                    AND Status IN ('Scheduled', 'Delayed')
                    ORDER BY DepartureTime
                """, (pilot_id,))
                conflicts = self.cursor.fetchall()
                print("\nPilot's current schedule:")
                for flight in conflicts:
                    print(f"Flight {flight[0]}: {flight[1]} ({flight[2]})")
                print("Would you like ti choose a different pilot.")

                if input("(Y/N): ").upper() != 'Y':
                    return None
            else:
                return pilot_id

    def get_datetime_input(self):
        while True:
            try:
                year = int(input("Enter year (YYYY): "))
                month = int(input("Enter month (1-12): "))
                day = int(input("Enter day (1-31): "))
                hour = int(input("Enter hour (0-23): "))
                minute = int(input("Enter minute (0-59): "))

                # format datetime for user
                year_digits = str(year).zfill(4)
                month_digits = str(month).zfill(2)
                day_digits = str(day).zfill(2)
                hour_digits = str(hour).zfill(2)
                minute_digits = str(minute).zfill(2)


                date_str =  year_digits + "-" + month_digits + "-" + day_digits + " " + hour_digits + ":" +  minute_digits + ":00"

                datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

                # Return the formatted date string
                return date_str

            except ValueError:
                print("Invalid date/time. Please try again.")

    def search_flight_via_status(self):
        print("Would you like to: ")
        print("1. View flights via Flight Number")
        print("2. View flights via Origin airport")
        print("3. View flights via Destination")
        print("4. View flights via Status")

        criteria = input("Please choose from the options 1-4: ")

        if criteria == "1":
            while True:
                flight_no = input("Please enter a flight number (e.g. BA123): ").upper()
                self.cursor.execute("SELECT COUNT(*) FROM Flights WHERE FlightNumber = ?", (flight_no,))
                count = self.cursor.fetchone()[0]
                if count == 0:
                    print("Flight Number does not exist, please try again!")
                    continue
                break

            self.cursor.execute("SELECT * FROM Flights WHERE FlightNumber = ?", (flight_no,))
            flights = self.cursor.fetchall()
            self.display_selection_results(flights)

        elif criteria == "2":
            while True:
                origin = input("Please enter an origin airport code (e.g. LHR): ").upper()
                self.cursor.execute("SELECT COUNT(*) FROM Flights WHERE Origin = ?", (origin,))
                count = self.cursor.fetchone()[0]
                if count == 0:
                    print("Origin does not exist in current flights, please try again!")
                    continue
                break

            self.cursor.execute("SELECT * FROM Flights WHERE Origin = ?", (origin,))
            flights = self.cursor.fetchall()
            self.display_selection_results(flights)

        elif criteria == "3":
            while True:
                destination = input("Please enter destination airport code (e.g. LHR): ").upper()
                self.cursor.execute("SELECT COUNT(*) FROM Flights WHERE Destination = ?", (destination,))
                count = self.cursor.fetchone()[0]
                if count == 0:
                    print("Destination does not exist in current flights, please try again!")
                    continue
                break

            self.cursor.execute("SELECT * FROM Flights WHERE Destination = ?", (destination,))
            flights = self.cursor.fetchall()
            self.display_selection_results(flights)

        elif criteria == "4":
            print("1. View all SCHEDULED flights")
            print("2. View all DELAYED flights")
            print("3. View all CANCELLED flights")
            print("4. View all COMPLETED flights")
            choice = input("Please select an option (1-4): ")

            if choice == "1":
                self.cursor.execute("SELECT * FROM Flights WHERE Status = 'Scheduled'")
            elif choice == "2":
                self.cursor.execute("SELECT * FROM Flights WHERE Status = 'Delayed'")
            elif choice == "3":
                self.cursor.execute("SELECT * FROM Flights WHERE Status = 'Cancelled'")
            elif choice == '4':
                self.cursor.execute("SELECT * FROM Flights WHERE Status = 'Completed")
            else:
                print("Invalid option")
                return

            flights = self.cursor.fetchall()
            self.display_selection_results(flights)

        else:
            print("Invalid option")

    def display_selection_results(self, flights):
        #in case of search errors
        if not flights:
            print("No flights found")
            return
        #print in table format
        print("\nFlight Results:")
        print("-" * 60)
        print("FlightID  Number  From  To    Departure Time    Status")
        print("-" * 60)
        for flight in flights:
            print(f"{flight[0]:<9} {flight[1]:<7} {flight[2]:<5} {flight[3]:<5} {flight[4]:<16} {flight[5]}")
        print("-" * 60)








def main():
    db = FlightManager()
#option menu
    while True:
        print("\nFlight Management API Menu:")
        print("-*-" * 6)
        print("1. View All Flights Information")
        print("2. View All Pilots")
        print("3. View All Destination")
        print("4. Add Destination")
        print("5. Delete Destination")
        print("6. View Deleted Destinations")
        print("7. Add New Pilot")
        print("8. Add New Flight Route")
        print("9. Amend Flight Route")
        print("10. Search for Flights via: ")
        print("-*-" * 6)



        choice = input("Please choose an option(1-9): ")

        if choice == "1":
            db.view_all_flights()
        elif choice == "2":
            db.view_all_pilots()
        elif choice == "3":
            db.view_destination()
        elif choice == "4":
            db.add_destination()
        elif choice == '5':
            db.remove_destination()
        elif choice == '6':
            db.view_deleted_destinations()
        elif choice == '7':
            db.add_new_pilot()
        elif choice == '8':
            db.add_new_flight()
        elif choice == '9':
            db.amend_flight()
        elif choice == '10':
            db.search_flight_via_status()
        else:
            print("Incorrect selection, please choose a number between 1-9")

#allow code to run
if __name__ == "__main__":
    main()