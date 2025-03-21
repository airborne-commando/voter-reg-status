import csv
import sys
from datetime import datetime, timedelta

def generate_csv(data, output_path='output.csv'):
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')  # Use tab as delimiter
        writer.writerow(["City", "Zip", "First Name", "Last Name", "DOB"])
        for row in data:
            writer.writerow(row)
    print(f"CSV file '{output_path}' has been generated.")

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        print("Invalid date format. Please use MM/DD/YYYY.")
        return None

def generate_dates(start_date, num_rows):
    dates = []
    for i in range(num_rows):
        dates.append((start_date + timedelta(days=i)).strftime("%m/%d/%Y"))
    return dates

def read_from_file(filename):
    data = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                # Expected format: City,Zip,First Name,Last Name,Start DOB,Num Rows
                parts = line.strip().split(',')
                if len(parts) != 6:
                    print(f"Skipping invalid line: {line}")
                    continue
                city, zip_code, first_name, last_name, dob_str, num_rows = parts
                start_date = parse_date(dob_str)
                if not start_date:
                    continue
                num_rows = int(num_rows)

                # Generate the list of dates
                dates = generate_dates(start_date, num_rows)

                # Prepare data for CSV
                for date in dates:
                    data.append([city, zip_code, first_name, last_name, date])
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        sys.exit(1)
    return data

def show_help():
    print("""
    Usage:
    - To read from a file: python csv-gen.py -file <filename>
    - To manually input data: python csv-gen.py

    File for (comma-separated):
    city,zip,first_name,last_name,start_dob(MM/DD/YYYY),num_rows
    Example:
    Cityname,00000,John,Doe,10/01/1990,6
    or two
    Cityname,00000,John,Doe,10/01/1990,6
    Cityname,00000,John,Doe,10/01/1990,24
    """)

def main():
    if len(sys.argv) == 3 and sys.argv[1] == '-file':
        # Read from file
        filename = sys.argv[2]
        data = read_from_file(filename)
        generate_csv(data)
    elif len(sys.argv) == 1:
        # Interactive mode
        print("CSV Generator Script")
        print("Type 'help' for instructions.")
        data = []
        while True:
            command = input("> ").strip().lower()
            if command == 'input':
                city = input("Enter city: ")
                zip_code = input("Enter zip code: ")
                first_name = input("Enter first name: ")
                last_name = input("Enter last name: ")
                dob_str = input("Enter starting DOB (MM/DD/YYYY): ")
                start_date = parse_date(dob_str)
                if not start_date:
                    continue
                num_rows = int(input("Enter number of rows to generate: "))
                dates = generate_dates(start_date, num_rows)
                for date in dates:
                    data.append([city, zip_code, first_name, last_name, date])
            elif command == 'help':
                show_help()
            elif command == 'exit':
                if data:
                    generate_csv(data)
                break
            else:
                print("Invalid command. Type 'help' for instructions.")
    else:
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
