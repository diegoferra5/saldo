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
    """
    Extracts the financial summary from a BBVA bank statement.
    
    Returns:
        dict: Summary with starting_balance, deposits_amount, charges_amount, etc.
    
    Raises:
        FileNotFoundError: If the PDF doesn't exist
        ValueError: If information is missing or mathematical validation fails
        Exception: Other parsing errors
    """
    summary = {}
    inside_summary = False
    
    # LEVEL 1: Main try-except for PDF errors
    try:
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
                        inside_summary = True
                        continue

                    if inside_summary and "saldo promedio mínimo mensual" in line_lower:
                        inside_summary = False
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
                        tokens = deposits.split()
                        n_deposits = int(tokens[8].strip())
                        deposits_amount = float(tokens[9].strip().replace(",",""))
                        summary["n_deposits"] = n_deposits
                        summary["deposits_amount"] = deposits_amount
                        continue
                        
                    if "retiros / cargos" in line_lower:
                        charges = line_lower
                        tokens = charges.split()
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
    
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    # LEVEL 2: Validate that summary has all required keys
    required_keys = ["starting_balance", "deposits_amount", "charges_amount", "final_balance"]
    missing_keys = [key for key in required_keys if key not in summary]
    
    if missing_keys:
        raise ValueError(
            f"Incomplete summary extracted. Missing fields: {', '.join(missing_keys)}. "
            f"The PDF may not have the 'Comportamiento' section or it's formatted differently."
        )
    
    # LEVEL 3: Mathematical validation
    try:
        calculated_final = summary["starting_balance"] + summary["deposits_amount"] - summary["charges_amount"]
        actual_final = summary["final_balance"]
        
        if round(calculated_final, 2) != round(actual_final, 2):
            raise ValueError(
                f"Summary validation failed! "
                f"Calculated final balance: {calculated_final:.2f}, "
                f"but PDF shows: {actual_final:.2f}. "
                f"Difference: {abs(calculated_final - actual_final):.2f}"
            )
    except KeyError as e:
        raise ValueError(f"Missing required field in summary: {str(e)}")
    
    return summary


def determine_transaction_type(transactions, summary):
    """
    Classify each transaction as CARGO, ABONO, or UNKNOWN.
    
    UNKNOWN transactions require manual user review.
    """
    # 1. initialize
    previous_balance = summary["starting_balance"]
        
    # keywords
    ABONO_KEYWORDS = [
        "SPEI RECIBIDO",
        "DEPOSITO",
        "ABONO",
        "REEMBOLSO",
        "DEVOLUC",
        "INTERESES",
        "BECAS",
        "BECA"
    ]

    CARGO_KEYWORDS = [
        "SPEI ENVIADO",
        "RETIRO CAJERO",
        "RETIRO CAJERO AUTOMATICO",
        "PAGO TARJETA DE CREDITO",
        "COMISION",
        "IVA",
        "EFECTIVO SEGURO"
    ]

    # 2. classify each transaction
    for transaction in transactions:
        current_balance = transaction["saldo_liquidacion"]
        amount_abs = transaction["amount_abs"]
        description = transaction["description"]
        
        # Initialize review flag
        transaction["needs_review"] = False

        # case A: Has balance (more reliable)
        if current_balance is not None:

            # compare with previous balance
            if current_balance > previous_balance:
                # balance went up: income
                transaction["movement_type"] = "ABONO"
                transaction["amount"] = amount_abs
                print("abono case a")

            elif current_balance < previous_balance:
                # balance went down: expense
                transaction["movement_type"] = "CARGO"
                transaction["amount"] = -amount_abs
                print("cargo case a")
            
            else:
                # current balance == previous balance (rare edge case)
                # Try saldo_operacion first, then keywords
                
                saldo_op = transaction["saldo_operacion"]
                
                if saldo_op is not None and saldo_op != previous_balance:
                    # Use saldo_operacion to determine type
                    if saldo_op > previous_balance:
                        transaction["movement_type"] = "ABONO"
                        transaction["amount"] = amount_abs
                        print("abono case a igual (saldo_operacion)")
                    else:  # saldo_op < previous_balance
                        transaction["movement_type"] = "CARGO"
                        transaction["amount"] = -amount_abs
                        print("cargo case a igual (saldo_operacion)")
                else:
                    # Can't use saldo_operacion - fall back to keywords
                    description_upper = description.upper()
                    
                    is_abono = False
                    for keyword in ABONO_KEYWORDS:
                        if keyword in description_upper:
                            is_abono = True
                            break
                    
                    if is_abono:
                        transaction["movement_type"] = "ABONO"
                        transaction["amount"] = amount_abs
                        print("abono case a igual (keywords)")
                    else:
                        # Check CARGO keywords
                        is_cargo = False
                        for keyword in CARGO_KEYWORDS:
                            if keyword in description_upper:
                                is_cargo = True
                                break
                        
                        if is_cargo:
                            transaction["movement_type"] = "CARGO"
                            transaction["amount"] = -amount_abs
                            print("cargo case a igual (keywords)")
                        else:
                            # ✅ UNKNOWN - user must decide
                            transaction["movement_type"] = "UNKNOWN"
                            transaction["amount"] = None
                            transaction["needs_review"] = True
                            print("unknown case a igual (no keywords)")

            previous_balance = current_balance
                    
        # case B: No balance (use keywords)
        else:
            # convert description to uppercase for comparison
            description_upper = description.upper()

            # check abono keywords first
            is_abono = False
            for keyword in ABONO_KEYWORDS:
                if keyword in description_upper:
                    is_abono = True
                    break
            
            if is_abono:
                transaction["movement_type"] = "ABONO"
                transaction["amount"] = amount_abs
                print("abono case b")
            else:
                # Check CARGO keywords
                is_cargo = False
                for keyword in CARGO_KEYWORDS:
                    if keyword in description_upper:
                        is_cargo = True
                        break
                
                if is_cargo:
                    transaction["movement_type"] = "CARGO"
                    transaction["amount"] = -amount_abs
                    print("cargo case b")
                else:
                    # ✅ UNKNOWN - user must decide
                    transaction["movement_type"] = "UNKNOWN"
                    transaction["amount"] = None
                    transaction["needs_review"] = True
                    print("unknown case b (no keywords)")

    # 3. validation (skip UNKNOWN transactions)
    
    # calculate totals 
    total_abonos = 0
    total_cargos = 0
    count_abonos = 0
    count_cargos = 0
    count_unknown = 0

    for transaction in transactions:
        if transaction["movement_type"] == "ABONO":
            total_abonos += transaction["amount"]
            count_abonos += 1
        elif transaction["movement_type"] == "CARGO":
            total_cargos += abs(transaction["amount"])
            count_cargos += 1
        else:  # UNKNOWN
            count_unknown += 1

    # compare with summary
    expected_abonos = summary["deposits_amount"]
    expected_cargos = summary["charges_amount"]
    expected_count_abonos = summary["n_deposits"]
    expected_count_cargos = summary["n_charges"]

    # Report classification results
    print(f"\n{'='*70}")
    print("CLASSIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Abonos classified: {count_abonos}")
    print(f"✅ Cargos classified: {count_cargos}")
    print(f"⚠️  Unknown (need review): {count_unknown}")
    print(f"{'='*70}\n")

    # validate amounts (only for classified transactions)
    if abs(total_abonos - expected_abonos) > 0.1:
        print(f"WARNING: Abonos total mismatch: calculated {total_abonos:.2f}, expected {expected_abonos:.2f}")

    if abs(total_cargos - expected_cargos) > 0.1:
        print(f"WARNING: Cargos total mismatch: calculated {total_cargos:.2f}, expected {expected_cargos:.2f}")

    # Note: counts won't match if there are UNKNOWN transactions
    missing_abonos = expected_count_abonos - count_abonos
    missing_cargos = expected_count_cargos - count_cargos
    
    if missing_abonos > 0:
        print(f"INFO: {missing_abonos} abonos pending classification (likely in UNKNOWN)")
    
    if missing_cargos > 0:
        print(f"INFO: {missing_cargos} cargos pending classification (likely in UNKNOWN)")
    
    # Check if UNKNOWN count matches expected missing
    expected_unknown = missing_abonos + missing_cargos
    if count_unknown != expected_unknown:
        print(f"WARNING: Unknown count ({count_unknown}) doesn't match expected missing ({expected_unknown})")

    return transactions


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
    print(extract_statement_summary(pdf_path))


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

    summary = extract_statement_summary(pdf_path)
    determine_transaction_type(parsed_transactions, summary)

