import json

def save_request(data, file_name):
    with open(file_name, "w") as write_file:
        json.dump(data, write_file, indent=4)
        return "Data saved to file."

def read_data(file_name):
    with open(file_name, "r") as read_file:
        data = json.load(read_file)
        return data
