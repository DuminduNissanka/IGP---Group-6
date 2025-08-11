import pandas as pd

def load_excel(file_path):
    """
    Load an Excel file and return all sheets combined with a 'Week' column.
    """
    xls = pd.ExcelFile(file_path)
    all_data = pd.concat(
        [xls.parse(sheet).assign(Week=sheet) for sheet in xls.sheet_names],
        ignore_index=True
    )
    return all_data, xls.sheet_names

def get_dataset_by_selection(selection):
    """
    Return dataset and sheet names based on sidebar selection.
    """
    if selection == "Individual Based Engagement":
        return load_excel("C:/Users/DuminduS/Desktop/UWE/IGP/Project/Code/DatasetforStreamlit/cleaned_new2_revised_2.xlsx")
    elif selection == "Group Based Engagement":
        return load_excel("C:/Users/DuminduS/Desktop/UWE/IGP/Project/Code/DatasetforStreamlit/cleaned_Newdata01.xlsx")
    else:
        return None, None
