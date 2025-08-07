from tika import parser
import re
import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta


common_cost_data = {
        "Common Cost": None,
        "int_Common Cost": None,
        "Service fee": 0,
        "Hot Water": {
            "Price/m3": None,
            "Previous standing": None,
            "Current standing": None,
            "Consumption": None,
            "Price": 0,
        },
        "Heating": {
            "Price/KWh": None,
            "Previous standing": None,
            "Current standing": None,
            "Consumption": None,
            "Price": 0,
        }
    }

electricity_data = {
    "Previous standing": None,
    "Current standing": None,
    "Consumption": None,
    "Price": 0,      
}

garbage_data = {
    "Garbage": 0,
}

internet_data = {
    "Internet": 0,
}

sewer_data = {
    "Sewer": 0,
}

water_data = {
    "Cold water": 0,
}


def get_pdf_contents(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            pdf_text = parser.from_file(file_path)
            if "common_cost" in filename:
                process_common_cost(pdf_text, filename)
            elif "garbage" in filename:
                process_garbage(pdf_text, filename)
            elif "electricity" in filename:
                process_electricity(pdf_text, filename)
            elif "water" in filename:
                process_water(pdf_text, filename)
            elif "sewer" in filename:
                process_sewer(pdf_text, filename)
            elif "internet" in filename:
                process_internet(pdf_text, filename)
            else:
                print(f"Unknown file type for {filename}. Skipping...\n")


def process_sewer(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "Fizetendő összeg" in line:
                val = get_water_data(line)
                if val:
                    sewer_data['Sewer'] = val
        print("="*150)


def process_water(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "Fizetendő összeg" in line:
                val = get_water_data(line)
                if val:
                    water_data['Cold water'] = val
        print("="*150)


def process_electricity(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "9901121662" in line:          
                vals = get_electricity_data(line)
                electricity_data['Previous standing'] = vals[0]
                electricity_data['Current standing'] = vals[1]
                electricity_data['Consumption'] = vals[2]
            elif "Fizetendő összeg összesen" in line:
                vals = get_electricity_data(line)
                if vals:
                    electricity_data['Price'] = vals[0]
        print("="*150)


def process_garbage(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "Fizetési mód" in line:
                val = get_garbage_data(line)
                if val:
                    garbage_data['Garbage'] = val
        print("="*150)
                

def process_common_cost(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "Közös költség" in line:
                val = get_parsed_line_val(line)
                if val:
                    common_cost_data['Common Cost'] = val
            elif "Rendelkezésre állási díj" in line:
                val = get_parsed_line_val(line)
                if val:
                    common_cost_data['Service fee'] = val
            elif "Melegvíz egységár" in line:
                set_detailed_vals(line, column="Hot Water", unit="Price/m3")
            elif "Fűtési egységár" in line:
                set_detailed_vals(line, column="Heating", unit="Price/KWh")
        print("="*150)


def process_internet(text, filename):
    print(f"Processing {filename}...")
    if text.get('content'):
        lines = [line.strip() for line in text['content'].split('\n') if line.strip()]
        for line in lines:
            if "Mindösszesen" in line:
                val = get_internet_data(line)
                if val:
                    internet_data['Internet'] = val
        print("="*150)


def set_detailed_vals(line, column, unit):
    parts = re.split(r'\s{2,}', line)
    if len(parts) == 2:
        common_cost_data[column][unit] = parts[1]
    elif len(parts) == 5:
        common_cost_data[column]['Previous standing'] = (parts[1])
        common_cost_data[column]['Current standing'] = (parts[2])
        common_cost_data[column]['Consumption'] = (parts[3])
        common_cost_data[column]['int_Price'] = int(parts[4].replace(' ', ''))  # Remove spaces in price
        common_cost_data[column]['Price'] = parts[4]


def get_parsed_line_val(line):
    parts = re.split(r'\s{2,}', line)
    if len(parts) == 4:
        val = parts[2]
        return val


def get_electricity_data(line):
    parts = line.split()
    if len(parts) == 8:
        vals = [parts[2].replace('.',' '), parts[3].replace('.',' '), parts[-1]]
        return vals
    elif len(parts) == 4:
        vals = [parts[-1].replace('.',' ')]
        return vals


def get_garbage_data(line):
    parts = line.split("FtFizetési mód")
    if len(parts) == 2:
        val = parts[0]
        return val    


def get_internet_data(line):
    parts = line.split()
    if len(parts) == 3:
        val = parts[-1].replace('.', ' ')
        return val
        

def get_water_data(line):
    parts = line.split(':')
    if len(parts) == 2:
        parts[-1] = parts[-1].replace(' Ft', '').strip()
        val = parts[-1]
        return val
    

def write_summary_to_file(filename="summary.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            # Common cost
            f.write("Common cost:\n")
            f.write(f"  Price: {common_cost_data.get('Common Cost', '')}\n\n")
            f.write("Service fee:\n")
            f.write(f"  Price: {common_cost_data.get('Service fee', '')}\n\n")
            # Hot water
            f.write("Hot water:\n")
            for key in ["Price/m3", "Previous standing", "Current standing", "Consumption", "Price"]:
                val = common_cost_data["Hot Water"].get(key, "")
                if val is not None:
                    f.write(f"  {key}: {val}\n")
                else:
                    f.write(f"  {key}: N/A\n")
            f.write("\n")
            # Heating
            f.write("Heating:\n")
            for key in ["Price/KWh", "Previous standing", "Current standing", "Consumption", "Price"]:
                val = common_cost_data["Heating"].get(key, "")
                if val is not None:
                    f.write(f"  {key}: {val}\n")
                else:
                    f.write(f"  {key}: N/A\n")
            f.write("\n")
            # Electricity
            f.write("Electricity:\n")
            for key in ["Previous standing", "Current standing", "Consumption", "Price"]:
                val = electricity_data.get(key, "")
                if val is not None:
                    f.write(f"  {key}: {val}\n")
                else:
                    f.write(f"  {key}: N/A\n")
            f.write("\n")
            # All together
            f.write("All together:\n")
            all_costs = [
                ("  Common cost", common_cost_data.get("Common Cost", 0)),
                ("  Service fee", common_cost_data.get("Service fee", 0)),
                ("  Hot water", common_cost_data["Hot Water"].get("Price", 0)),
                ("  Heating", common_cost_data["Heating"].get("Price", 0)),
                ("  Electricity", electricity_data.get("Price", 0)),
                ("  Garbage", garbage_data.get("Garbage", 0)),
                ("  Internet", internet_data.get("Internet", 0)),
                ("  Cold water", water_data.get("Cold water", 0)),
                ("  Sewer", sewer_data.get("Sewer", 0)),
            ]
            total = 0
            for label, value in all_costs:
                try:
                    int_val = int(str(value).replace(" ", "")) if value else 0
                except ValueError:
                    int_val = 0
                total += int_val
                f.write(f"{label}: {value}\n")
            # Write the total in bold using Markdown syntax
            f.write("\n**Summa: {:,}**\n".format(total).replace(",", " "))



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python pdf_parser.py <folder_path>")
        sys.exit(1)
    folder = sys.argv[1]
    get_pdf_contents(folder)
    print("Processing completed.")
    current_month = (datetime.now() - relativedelta(months=1)).strftime("%Y-%m")
    write_summary_to_file(folder + '/' + current_month + "_summary.txt")

    


