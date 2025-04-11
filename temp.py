from models import Units

from repository import UnitsRepository
import json




units_data_json  = json.load(open("/home/shazib/Desktop/Folder/python/MutualFund/data/units.json"))

def read_units_json_file_and_store_it_db():

    # print(units_data_json)  # Uncommented to display the JSON data
    units_repo = UnitsRepository()
    for unit,data in units_data_json.items():
        print(unit,data)

        unit =  Units(
            mfid=unit,
            total_units=round(data[0],3),
            total_invested=round(data[1],3),
        )
        units_repo.save(unit)
    


    print("Units data has been successfully stored in the database.")

def find_all_distinct_mfids():
    units_repo = UnitsRepository()
    mfids = units_repo.find_all_distinct_mfids()
    print("Distinct MFIDs:")
    print(mfids)

if __name__ == "__main__":
    find_all_distinct_mfids()