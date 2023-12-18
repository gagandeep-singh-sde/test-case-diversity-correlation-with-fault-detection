import os
import subprocess

import pandas as pd


def create_dc_report(state_machine_folder):
    # Path to TR_Report.csv file in FSM_reports folder
    tr_report_path = os.path.join(state_machine_folder, 'FSM_reports', 'TR_Report.csv')

    # Path to DC_Report.csv file
    dc_report_path = os.path.join(state_machine_folder, 'DC_Report.csv')

    try:
        # Read TR_Report.csv into a pandas DataFrame
        tr_df = pd.read_csv(tr_report_path)

        # Extract specific columns
        dc_df = tr_df[['Test suite file', 'states', 'inputs', 'outputs', 'transitions', 'Number of All_Mutants',
                       'Number of killed All_Mutants OracleOutput', 'Mutation score All_Mutants OracleOutput']]

        # Write the extracted data to DC_Report.csv
        dc_df.to_csv(dc_report_path, index=False)

        print(f"DC_Report.csv created successfully for {state_machine_folder}")

    except FileNotFoundError:
        print(f"Error: TR_Report.csv not found in FSM_reports folder for {state_machine_folder}")


def calculate_diversity(state_machine_path):
    fsm_test_suites_path = os.path.join(state_machine_path, 'FSM_test_suites')

    # Check if 'FSM_test_suites' folder exists
    if os.path.exists(fsm_test_suites_path):
        print(f"Found 'FSM_test_suites' folder in ========== {state_machine_path}")

        test_suite_files = []
        diversity_values = []

        # Iterate over each txt file in 'FSM_test_suites' folder
        for txt_file in os.listdir(fsm_test_suites_path):
            if txt_file.endswith(".txt"):
                test_suite_files.append(txt_file)
                # Process the txt file
                # Command to run the JAR file using the Java Virtual Machine (JVM)
                command = ['java', '-jar', jar_file, 'compare',
                           f'{fsm_test_suites_path}/{txt_file}', 'EventSequence', '-m',
                           'Nei', '-a', 'Summation', '-r', 'RawResults']
                # Run the command
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Wait for the process to finish and get the return code
                return_code = process.wait()

                # Print the output and errors
                output, error = process.communicate()
                print("Action:", output.decode())
                print("Result:", error.decode())

                result = output.decode().splitlines()
                diversity_value = result[-2].replace("[", "").replace("]", "")

                print("DV:", diversity_value)
                diversity_values.append(diversity_value)

                # Check the return code to see if the process was successful
                if return_code == 0:
                    print("JAR file executed successfully.")
                else:
                    print(f"Error: JAR file execution failed with return code {return_code}.")
                print(f"Found TXT File: {txt_file}")

        # Load the CSV file into a DataFrame
        csv_file_path = f'{state_machine_path}/DC_Report.csv'  # Replace with the actual path to your CSV file
        csv_df = pd.read_csv(csv_file_path)

        diversity_info = {'Test suite file': test_suite_files, 'Diversity': diversity_values}
        diversity_df = pd.DataFrame(diversity_info)

        merged_df = pd.merge(csv_df, diversity_df, on='Test suite file', how='left')

        # Print the resulting DataFrame
        print(merged_df)

        # Save the updated DataFrame back to the CSV file
        # merged_df.to_csv('DC_Report.csv', index=False)
        try:
            merged_df.to_csv(csv_file_path, index=False)
            print(f"File '{csv_file_path}' updated successfully.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Error: 'FSM_test_suites' folder not found in {state_machine_path}")


def process_state_machines(root_folder):
    # Iterate over each folder in the specified root folder
    for state_machine_folder in os.listdir(root_folder):
        state_machine_path = os.path.join(root_folder, state_machine_folder)

        # Check if the item is a directory
        if os.path.isdir(state_machine_path):
            print(f"Processing State Machine Folder: {state_machine_folder}")

            # Call function to create DC_Report.csv for the current State Machine folder
            create_dc_report(state_machine_path)
            calculate_diversity(state_machine_path)
        break


# Specify the root folder
state_machines_container_folder = "StateMachines"
jar_file = 'ComparisonApp.jar'

# Call the function to process folders
process_state_machines(state_machines_container_folder)
