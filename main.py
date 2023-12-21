import os
import subprocess

import pandas as pd
from scipy.stats import spearmanr

import sys
import numpy
numpy.set_printoptions(threshold=sys.maxsize)

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


def calculate_diversity(state_machine_path, data_representation, diversity_metric, aggregation_method):
    fsm_test_suites_path = os.path.join(state_machine_path, 'FSM_test_suites')

    # Check if 'FSM_test_suites' folder exists
    if os.path.exists(fsm_test_suites_path):
        print(f"Found 'FSM_test_suites' folder in {state_machine_path}")

        test_suite_files = []
        diversity_values = []

        # Iterate over each txt file in 'FSM_test_suites' folder
        for txt_file in os.listdir(fsm_test_suites_path):
            if txt_file.endswith(".txt"):
                print(f"Found TXT File: {txt_file}")
                test_suite_files.append(txt_file)
                # Process the txt file
                # Command to run the JAR file using the Java Virtual Machine (JVM)
                if aggregation_method is not None:
                    command = ['java', '-jar', jar_file, 'compare',
                               f'{fsm_test_suites_path}/{txt_file}', f'{data_representation}', '-m',
                               f'{diversity_metric}', '-a', f'{aggregation_method}', '-r', 'RawResults']
                else:
                    command = ['java', '-jar', jar_file, 'compare',
                               f'{fsm_test_suites_path}/{txt_file}', f'{data_representation}', '-m',
                               f'{diversity_metric}', '-r', 'RawResults']
                # Run the command
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Wait for the process to finish and get the return code
                return_code = process.wait()

                # Print the output and errors
                output, error = process.communicate()
                # print("Action:", output.decode())
                # print("Result:", error.decode())

                result = output.decode().splitlines()
                diversity_value = result[-2].replace("[", "").replace("]", "")
                diversity_values.append(diversity_value)

                # Check the return code to see if the process was successful
                if return_code == 0:
                    print(f"JAR file executed successfully - {data_representation}_{diversity_metric}_{aggregation_method} calculated.")
                else:
                    print(f"Error: JAR file execution failed with return code {return_code}.")

        # Load the CSV file into a DataFrame
        csv_file_path = f'{state_machine_path}/DC_Report.csv'  # Replace with the actual path to your CSV file
        csv_df = pd.read_csv(csv_file_path)
        if aggregation_method is not None:
            diversity_info = {'Test suite file': test_suite_files,
                              f'{data_representation}_{diversity_metric}_{aggregation_method}': diversity_values}
        else:
            diversity_info = {'Test suite file': test_suite_files,
                              f'{data_representation}_{diversity_metric}': diversity_values}
        diversity_df = pd.DataFrame(diversity_info)

        merged_df = pd.merge(csv_df, diversity_df, on='Test suite file', how='left')

        try:
            merged_df.to_csv(csv_file_path, index=False)
            print(f"File '{csv_file_path}' updated successfully.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Error: 'FSM_test_suites' folder not found in {state_machine_path}")


def calculate_correlation(state_machine_path):
    csv_file_path = f'{state_machine_path}/DC_Report.csv'  # Replace with the actual path to your CSV file
    csv_df = pd.read_csv(csv_file_path)

    diversity_columns = csv_df.iloc[:, 8:50]
    pearson_correlation_coefficients = diversity_columns.apply(
        lambda col: col.astype(float).corr(csv_df['Mutation score All_Mutants OracleOutput'].astype(float)))
    # Calculate the Spearman rank correlation coefficient
    correlation_coefficients = []
    p_values = []

    # Iterate over columns and calculate Spearman correlation
    for col in diversity_columns.columns:
        data_1 = diversity_columns[col].tolist()
        data_2 = csv_df['Mutation score All_Mutants OracleOutput'].tolist()
        print(data_1, data_2)
        coef, p_value = spearmanr(data_1, data_2)
        correlation_coefficients.append(coef)
        p_values.append(p_value)
        print(coef, p_value)

    csv_df.loc['Pearson Correlation Coefficient'] = ["Pearson Correlation Coefficient", None, None, None, None, None,
                                                     None, None] + pearson_correlation_coefficients.tolist()
    csv_df.loc['Spearman Rank Correlation Coefficients'] = ["Spearman Rank Correlation Coefficients", None, None, None, None, None,
                                                     None, None] + correlation_coefficients

    # Add a row at the bottom of the DataFrame for p-values
    csv_df.loc['P-values'] = ["P-values", None, None, None, None, None,
                                                     None, None] + p_values
    csv_df.to_csv('DC_Report.csv', index=False)

    try:
        csv_df.to_csv(csv_file_path, index=False)
        print(f"File '{csv_file_path}' updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

def normalize_data(state_machine_path):
    csv_file_path = f'{state_machine_path}/DC_Report.csv'  # Replace with the actual path to your CSV file
    csv_df = pd.read_csv(csv_file_path)
    column_1 = csv_df.loc['Mutation score All_Mutants OracleOutput']
    column_2 = csv_df.loc['EventSequence_Levenshtein_AverageValue']
    csv_df['normalized_column'] = (column_1 - column_1.min()) / (
                column_1.max() - column_1.min())
    print(f'normalized_column \n {csv_df['normalized_column'].tolist()}')
    print(f'normalized_column \n {csv_df['normalized_column'].tolist()}')


def process_state_machines(root_folder):
    # Iterate over each folder in the specified root folder
    for state_machine_folder in os.listdir(root_folder):
        state_machine_path = os.path.join(root_folder, state_machine_folder)

        # Check if the item is a directory
        if os.path.isdir(state_machine_path):
            print(f"Processing State Machine Folder: {state_machine_folder}")

            # Call function to create DC_Report.csv for the current State Machine folder
            # create_dc_report(state_machine_path)

            data_representations = ["EventSequence", "EventStatePairs", "StateSequence"]
            diversity_metrics = ["Levenshtein", "SimpsonDiversity", "Hamming", "ShannonIndex", "Nei"]
            aggregation_methods = ["AverageValue", "SquaredSummation", "Manhattan", "Euclidean"]
            # for data_representation in data_representations:
            #     for diversity_metric in diversity_metrics:
            #         if diversity_metric != "ShannonIndex" and diversity_metric != "Nei":
            #             for aggregation_method in aggregation_methods:
            #                 calculate_diversity(state_machine_path, data_representation, diversity_metric,
            #                                     aggregation_method)
            #         else:
            #             calculate_diversity(state_machine_path, data_representation, diversity_metric, None)

            # calculate_correlation(state_machine_path)
            normalize_data(state_machine_path)
            break


# Specify the root folder
state_machines_container_folder = "StateMachines"
jar_file = 'ComparisonApp.jar'

# Call the function to process folders
process_state_machines(state_machines_container_folder)
