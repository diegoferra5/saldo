import pdfplumber
import re

# Compile patterns once (performance + clarity)
DATE_RE = re.compile(r'^\d{2}/[A-Z]{3}$')
AMOUNT_RE = re.compile(r'^\d{1,3}(?:,\d{3})*\.\d{2}$')


def extract_transaction_lines(pdf_path):
    """
    Extract raw transaction lines from a BBVA bank statement PDF.

    Scans all pages and returns only primary transaction lines found inside
    the "Detalle de Movimientos" section. Lines starting with two dates
    (DD/MMM DD/MMM) are considered transactions; headers and detail lines
    (RFC, references, metadata) are ignored.

    This function returns raw text lines only. Parsing amounts, balances,
    and descriptions is intentionally handled in later processing steps.

    Args:
        pdf_path (str): Path to the BBVA PDF statement.

    Returns:
        list[str]: Raw transaction lines in document order.
    """
    transaction_lines = []
    inside_transactions = False
    pattern = r'^\d{2}/[A-Z]{3}\s+\d{2}/[A-Z]{3}'
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                line_clean = line.rstrip()
                line_lower = line_clean.lower()
                
                # Start of transactions
                if "detalle de movimientos" in line_lower:
                    inside_transactions = True
                    continue
                
                # End of transactions
                if inside_transactions and "total de movimientos" in line_lower:
                    inside_transactions = False
                    continue
                
                # Skip if not in transaction section
                if not inside_transactions:
                    continue
                
                # Skip detail lines (start with space)
                if line_clean.startswith(" "):
                    continue
                
                # Skip header lines
                if "fecha" in line_lower or "oper" in line_lower:
                    continue
                
                # Real transaction (must match date pattern)
                if re.match(pattern, line_clean):
                    transaction_lines.append(line_clean)
    
    return transaction_lines


def parse_transaction_line(line):
    """
    Parse a single BBVA transaction line into structured data.
    
    Strategy:
    - Amounts are ALWAYS at the end of the line
    - Parse from right to left to avoid false positives
    - Don't determine cargo/abono yet (requires context)
    
    Args:
        line (str): Raw transaction line
        
    Returns:
        dict | None: Parsed transaction or None if invalid
    """
    
    print(f"\nParsing: {line}")
    
    # Split by spaces
    tokens = line.strip().split()
    print(f"Tokens: {tokens}")
    
    # Validate minimum length: date date description amount
    if len(tokens) < 4:
        print("Not enough tokens")
        return None
    
    # Validate first two tokens are dates
    if not (DATE_RE.fullmatch(tokens[0]) and DATE_RE.fullmatch(tokens[1])):
        print("First two tokens are not dates")
        return None
    
    # Extract dates
    fecha_operacion = tokens[0]
    fecha_liquidacion = tokens[1]
    
    # Parse from the END to extract amounts (they're always last)
    rest_tokens = tokens[2:]
    amounts = []
    
    for token in reversed(rest_tokens):
        if AMOUNT_RE.fullmatch(token):
            # Convert to float (remove commas)
            clean_amount = token.replace(',', '')
            amounts.insert(0, float(clean_amount))
        else:
            # Stop when we hit non-amount (beginning of description)
            break
    
    # Description is everything between dates and amounts
    description_end_index = len(rest_tokens) - len(amounts)
    description_parts = rest_tokens[:description_end_index]
    description = " ".join(description_parts)
    
    # Validate we found amounts
    if len(amounts) == 0:
        print("No amounts found")
        return None
    
    # Structure based on amount count
    if len(amounts) == 3:
        # Full: [amount, saldo_operacion, saldo_liquidacion]
        amount_abs = amounts[0]
        saldo_operacion = amounts[1]
        saldo_liquidacion = amounts[2]
    elif len(amounts) == 1:
        # Incomplete: [amount only]
        amount_abs = amounts[0]
        saldo_operacion = None
        saldo_liquidacion = None
    else:
        # Unexpected - likely parsing error
        print(f"Unexpected amount count: {len(amounts)}")
        return None
    
    result = {
        'date': fecha_operacion,
        'date_liquidacion': fecha_liquidacion,
        'description': description,
        'amount_abs': amount_abs,
        'movement_type': None,
        'saldo_operacion': saldo_operacion,
        'saldo_liquidacion': saldo_liquidacion
    }
    
    print(f"Parsed successfully: {result}")
    return result

    def extract_statement_summary(pdf_path):
        summary = []

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

                    if "saldo anterior" in line_lower:
                        saldo_anterior = line_lower
                        continue
                    
                    if "depósitos / abonos" in line_lower:
                        n_depositos = line_lower


    def transaction_type(transaction, prev_balance):
        pass


if __name__ == "__main__":
    pdf_path = "/Users/diegoferra/Documents/ASTRAFIN/STATEMENTS/BBVA_debit_dic25_diego.pdf"
    pdf_path2023 = "/Users/diegoferra/Documents/ASTRAFIN/STATEMENTS/BBVA_debit_2023.pdf"

    # Extract raw lines
    transaction_lines = extract_transaction_lines(pdf_path)
    
    print(f"\n{'='*70}")
    print(f"FOUND {len(transaction_lines)} TRANSACTIONS")
    print(f"{'='*70}\n")
    
    # Parse all transactions
    parsed_transactions = []
    for i, trans in enumerate(transaction_lines, 1):
        print(f"\n{i:2d}. {trans}")
        parsed = parse_transaction_line(trans)
        if parsed:
            parsed_transactions.append(parsed)
    
    #shitty
    print(f"{'='*70}\n")
    print(parsed_transactions[0])


    # Summary
    print(f"\n{'='*70}")
    print(f"SUCCESSFULLY PARSED: {len(parsed_transactions)}/{len(transaction_lines)}")
    print(f"{'='*70}\n")

    '''
    # Show first 10 in clean format
    print("\nFirst 10 transactions:")
    for i, trans in enumerate(parsed_transactions[:10], 1):
        balance = f"${trans['saldo_liquidacion']:,.2f}" if trans['saldo_liquidacion'] else "N/A"
        print(f"{i}. {trans['date']} | {trans['description']:<35} | ${trans['amount_abs']:>10,.2f} | Balance: {balance:>12}")
    
    # Validation checks
    print(f"\n{'='*70}")
    print("VALIDATION CHECKS")
    print(f"{'='*70}")
    
    empty_descriptions = sum(1 for t in parsed_transactions if not t['description'])
    complete_transactions = sum(1 for t in parsed_transactions if t['saldo_liquidacion'] is not None)
    incomplete_transactions = sum(1 for t in parsed_transactions if t['saldo_liquidacion'] is None)
    
    print(f"Empty descriptions: {empty_descriptions}")
    print(f"Complete transactions (with balance): {complete_transactions}")
    print(f"Incomplete transactions (no balance): {incomplete_transactions}")
    '''

