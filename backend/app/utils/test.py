import pdfplumber 

def extract_statement_summary(pdf_path):
    summary = {}
    inside_summary = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text: 
                continue

            lines = text.split('\n')
            for line in lines:
                line_clean = line.strip()
                line_lower = line_clean.lower()

                if "comportamiento" in line_lower:
                    inside_summary= True
                    continue

                if inside_summary and "saldo promedio mínimo mensual" in line_lower:
                    inside_summary= False
                    continue
                         
                if not inside_summary:
                    continue

                if "saldo anterior" in line_lower:
                    prev_balance = line_lower

                    tokens = prev_balance.split() 
                    prev_balance = float(tokens[5].strip().replace(",", ""))
                    summary["starting_balance"] = prev_balance
                    continue
                    
                if "depósitos / abonos" in line_lower:
                    deposits = line_lower

                    tokens= deposits.split()
                    n_deposits = int(tokens[8].strip())
                    deposits_amount = float(tokens[9].strip().replace(",",""))
                    summary["n_deposits"] = n_deposits
                    summary["deposits_amount"] = deposits_amount
                    continue
                    
                if "retiros / cargos" in line_lower:
                    charges= line_lower

                    tokens= charges.split()
                    n_charges = int(tokens[9].strip())
                    charges_amount = float(tokens[10].strip().replace(",",""))
                    summary["n_charges"] = n_charges
                    summary["charges_amount"] = charges_amount
                    continue

                if "saldo final" in line_lower:
                    final_balance = line_lower

                    tokens = final_balance.split() 
                    final_balance = float(tokens[6].strip().replace(",", ""))
                    summary["final_balance"] = final_balance
                    continue

    return summary
                
pdf_path= "/Users/diegoferra/Documents/ASTRAFIN/STATEMENTS/BBVA_debit_dic25_diego.pdf"
print(extract_statement_summary(pdf_path))
