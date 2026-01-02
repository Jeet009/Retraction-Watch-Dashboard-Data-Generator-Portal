import pandas as pd

# Specify the file path

retractions_df = pd.read_csv('data_2025_jul_dec.csv')

list_of_marks = ['Supplemental','System','Research','Integrity','Serious']

for mark in list_of_marks:

    file_path = mark + '.txt'

    # Initialize an empty list to store the lines
    lines = []

    # Open the file and read its lines
    with open(file_path, 'r') as file:
        lines = [line.strip() for line in file]

    # Now, the 'lines' list contains each line of the file as an element
    print(lines)

    # Define the list of substrings you want to search for
    #substrings = ['Concerns/Issues About Data', 'Paper Mills']
    substrings = lines

    # Create a regular expression pattern to match any of the substrings
    pattern = '|'.join(substrings)


    # Extract rows where the substring is present in 'column_name'
    filtered_df = retractions_df[retractions_df['Reason'].str.contains(pattern, case=False)]

    # Add a new column 'mark' and set it to 'grave' for the filtered rows
    #retractions_df['mark'] = 'unmarked'  # Initialize all rows as 'normal'
    retractions_df.loc[filtered_df.index, 'mark'] = mark

retractions_df.to_csv('data_2025_jul_dec_with_marks.csv', index=False)