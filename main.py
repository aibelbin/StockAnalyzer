import csv
import os

def create_companies_csv(filename="companies.csv"):
    """
    Creates a CSV file with company names and placeholder descriptions.
    The descriptions can be filled in later by an LLM.
    """
    
    # List of popular companies for stock analysis
    companies = [
        "Apple Inc.",
        "Microsoft Corporation",
        "Amazon.com Inc.",
        "Alphabet Inc.",
        "Tesla Inc.",
        "Meta Platforms Inc.",
        "NVIDIA Corporation",
        "Berkshire Hathaway Inc.",
        "Johnson & Johnson",
        "JPMorgan Chase & Co.",
        "Visa Inc.",
        "Procter & Gamble Co.",
        "UnitedHealth Group Inc.",
        "Home Depot Inc.",
        "Mastercard Inc.",
        "Bank of America Corp.",
        "Pfizer Inc.",
        "Coca-Cola Co.",
        "Walt Disney Co.",
        "Netflix Inc.",
        "Adobe Inc.",
        "Salesforce Inc.",
        "PayPal Holdings Inc.",
        "Intel Corporation",
        "Cisco Systems Inc.",
        "Comcast Corporation",
        "PepsiCo Inc.",
        "Abbott Laboratories",
        "Texas Instruments Inc.",
        "Broadcom Inc."
    ]
    
    # Create the CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Company Name', 'Description'])
        
        # Write company names with empty descriptions
        for company in companies:
            writer.writerow([company, ''])  # Empty description to be filled by LLM later
    
    print(f"CSV file '{filename}' created successfully with {len(companies)} companies.")
    print(f"File location: {os.path.abspath(filename)}")
    return filename

def add_company_to_csv(filename, company_name, description=""):
    """
    Adds a new company to the existing CSV file.
    """
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([company_name, description])
        print(f"Added '{company_name}' to {filename}")
    except FileNotFoundError:
        print(f"File {filename} not found. Please create it first using create_companies_csv()")

def read_companies_csv(filename="companies.csv"):
    """
    Reads and displays the contents of the companies CSV file.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                if i == 0:
                    print(f"{'Company Name':<30} | {'Description'}")
                    print("-" * 80)
                else:
                    company = row[0] if len(row) > 0 else ""
                    description = row[1] if len(row) > 1 else ""
                    print(f"{company:<30} | {description}")
    except FileNotFoundError:
        print(f"File {filename} not found. Please create it first using create_companies_csv()")

def update_company_description(filename, company_name, description):
    """
    Updates the description for a specific company in the CSV file.
    """
    rows = []
    updated = False
    
    try:
        # Read all rows
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        # Update the specific company's description
        for i, row in enumerate(rows):
            if len(row) >= 2 and row[0] == company_name:
                rows[i][1] = description
                updated = True
                break
        
        if updated:
            # Write back to file
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
            print(f"Updated description for '{company_name}'")
        else:
            print(f"Company '{company_name}' not found in {filename}")
            
    except FileNotFoundError:
        print(f"File {filename} not found. Please create it first using create_companies_csv()")

if __name__ == "__main__":
    # Create the CSV file
    csv_filename = create_companies_csv()
    
    print("\nPreview of the CSV file:")
    read_companies_csv(csv_filename)
    
    # Example of how to add a new company
    print("\nExample: Adding a new company...")
    add_company_to_csv(csv_filename, "Oracle Corporation", "")
    
    # Example of how to update a description
    print("\nExample: Updating a company description...")
    update_company_description(csv_filename, "Apple Inc.", "Technology company that designs and manufactures consumer electronics, software, and online services.")