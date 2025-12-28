import pdfplumber
import re
from typing import Dict, List, Optional, TypedDict

# Compile patterns once (performance + clarity)
DATE_RE = re.compile(r'^\d{2}/[A-Z]{3}$')
AMOUNT_RE = re.compile(r'^\d{1,3}(?:,\d{3})*\.\d{2}$')


# Type definitions for transaction structure
class TransactionDict(TypedDict, total=False):
    """Type definition for a parsed transaction dictionary."""
    date: str
    date_liquidacion: str
    description: str
    detail: Optional[str]  # Optional detail line for disambiguation
    amount_abs: float
    amount: Optional[float]
    movement_type: Optional[str]
    needs_review: bool
    saldo_operacion: Optional[float]
    saldo_liquidacion: Optional[float]


class SummaryDict(TypedDict, total=False):
    """Type definition for statement summary dictionary."""
    starting_balance: float
    deposits_amount: float
    charges_amount: float
    final_balance: float
    n_deposits: int
    n_charges: int


class ParserResult(TypedDict):
    """Type definition for the main parser result."""
    transactions: List[TransactionDict]
    warnings: List[str]
    summary: Optional[SummaryDict]


def extract_transaction_lines(pdf_path: str) -> List[Dict[str, Optional[str]]]:
    """
    Extract raw transaction lines from a BBVA bank statement PDF.

    Scans all pages and returns only primary transaction lines found inside
    the "Detalle de Movimientos" section. Lines starting with two dates
    (DD/MMM DD/MMM) are considered transactions; headers and detail lines
    (RFC, references, metadata) are ignored.

    This function returns raw text lines only. Parsing amounts, balances,
    and descriptions is intentionally handled in later processing steps.

    Args:
        pdf_path: Path to the BBVA PDF statement.

    Returns:
        List of dicts with 'main_line' and optional 'detail_line' for context.
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
            i = 0

            while i < len(lines):
                line_clean = lines[i].rstrip()
                line_lower = line_clean.lower()

                # Start of transactions
                if "detalle de movimientos" in line_lower:
                    inside_transactions = True
                    i += 1
                    continue

                # End of transactions
                if inside_transactions and "total de movimientos" in line_lower:
                    inside_transactions = False
                    i += 1
                    continue

                # Skip if not in transaction section
                if not inside_transactions:
                    i += 1
                    continue

                # Skip detail lines (start with space)
                if line_clean.startswith(" "):
                    i += 1
                    continue

                # Skip header lines
                if "fecha" in line_lower or "oper" in line_lower:
                    i += 1
                    continue

                # Real transaction (must match date pattern)
                if re.match(pattern, line_clean):
                    # Capture optional detail line (immediate next non-empty line that's not a transaction)
                    detail_line = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].rstrip()
                        next_line_lower = next_line.lower()

                        # Check if next line is a valid detail line:
                        # - Not empty
                        # - Not another transaction (doesn't start with date pattern)
                        # - Not a header/section marker
                        if (next_line and
                            not re.match(pattern, next_line) and
                            "fecha" not in next_line_lower and
                            "oper" not in next_line_lower and
                            "detalle de movimientos" not in next_line_lower and
                            "total de movimientos" not in next_line_lower):
                            detail_line = next_line.strip()

                    transaction_lines.append({
                        'main_line': line_clean,
                        'detail_line': detail_line
                    })

                i += 1

    return transaction_lines


def parse_transaction_line(line: str, detail_line: Optional[str] = None, debug: bool = False) -> Optional[TransactionDict]:
    """
    Parse a single BBVA transaction line into structured data.

    Strategy:
    - Amounts are ALWAYS at the end of the line
    - Parse from right to left to avoid false positives
    - Don't determine cargo/abono yet (requires context)

    Args:
        line: Raw transaction line
        detail_line: Optional detail line for disambiguation context
        debug: If True, print debug information during parsing

    Returns:
        Parsed transaction or None if invalid
    """

    if debug:
        print(f"\nParsing: {line}")
        if detail_line:
            print(f"Detail: {detail_line}")

    # Split by spaces
    tokens = line.strip().split()
    if debug:
        print(f"Tokens: {tokens}")

    # Validate minimum length: date date description amount
    if len(tokens) < 4:
        if debug:
            print("Not enough tokens")
        return None

    # Validate first two tokens are dates
    if not (DATE_RE.fullmatch(tokens[0]) and DATE_RE.fullmatch(tokens[1])):
        if debug:
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
        if debug:
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
        if debug:
            print(f"Unexpected amount count: {len(amounts)}")
        return None

    result: TransactionDict = {
        'date': fecha_operacion,
        'date_liquidacion': fecha_liquidacion,
        'description': description,
        'detail': detail_line,
        'amount_abs': amount_abs,
        'movement_type': None,
        'needs_review': True,  # Default to True, will be updated by determine_transaction_type()
        'saldo_operacion': saldo_operacion,
        'saldo_liquidacion': saldo_liquidacion
    }

    if debug:
        print(f"Parsed successfully: {result}")
    return result


def extract_account_holder_key(pdf_path: str) -> Optional[str]:
    """
    Extract account holder name key from PDF header for disambiguation.

    Scans first page for the account holder's full name (uppercase line).
    Returns a compact key like "DIEGO F" for matching in detail lines.

    Args:
        pdf_path: Path to the BBVA PDF statement.

    Returns:
        Compact account holder key (first name + first initial of surname) or None.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                return None

            # Check first page only
            text = pdf.pages[0].extract_text()
            if not text:
                return None

            lines = text.split('\n')
            for line in lines[:20]:  # Only check first 20 lines
                line_clean = line.strip()
                # Look for uppercase name pattern (e.g., "DIEGO FERRA LOPEZ")
                # Typically 2-4 uppercase words, at least 10 chars
                if (len(line_clean) >= 10 and
                    line_clean.isupper() and
                    not any(x in line_clean for x in ['BBVA', 'CUENTA', 'PERIODO', 'SALDO', 'PAGINA']) and
                    ' ' in line_clean):
                    # Extract first name + first char of first surname
                    parts = line_clean.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        surname_initial = parts[1][0] if len(parts[1]) > 0 else ''
                        return f"{first_name} {surname_initial}"
    except Exception:
        pass

    return None


def extract_statement_summary(pdf_path: str) -> SummaryDict:
    """
    Extracts the financial summary from a BBVA bank statement.

    Args:
        pdf_path: Path to the BBVA PDF statement.

    Returns:
        Summary with starting_balance, deposits_amount, charges_amount, etc.

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


def determine_transaction_type(
    transactions: List[TransactionDict],
    summary: SummaryDict,
    account_holder_key: Optional[str] = None,
    debug: bool = False
) -> List[TransactionDict]:
    """
    Classify each transaction as CARGO, ABONO, or UNKNOWN.

    Args:
        transactions: List of parsed transactions to classify
        summary: Statement summary with totals for validation
        account_holder_key: Optional account holder key for disambiguation (e.g., "DIEGO F")
        debug: If True, print debug information during classification

    Returns:
        The same transactions list with movement_type and amount fields populated

    Note:
        UNKNOWN transactions require manual user review.
    """
    # 1. initialize
    previous_balance = summary["starting_balance"]

    # Compile transfer detection patterns once for performance
    TRANSFER_TO_PATTERN = re.compile(
        r'\b(TRANSF(?:ERENCIA)?|TRASP(?:ASO)?)\s+A\b',
        re.IGNORECASE
    )

    # keywords (expanded for better coverage)
    # Note: "PAGO CUENTA DE TERCERO" removed from CARGO - it's ambiguous
    ABONO_KEYWORDS = [
        "SPEI RECIBIDO",
        "DEPOSITO",
        "DEPOSITO DE TERCERO",
        "ABONO",
        "REEMBOLSO",
        "DEVOLUC",
        "INTERESES",
        "BECAS",
        "BECA",
        "PAGO BECAS"
    ]

    CARGO_KEYWORDS = [
        "SPEI ENVIADO",
        "RETIRO CAJERO",
        "RETIRO CAJERO AUTOMATICO",
        "PAGO TARJETA DE CREDITO",
        "COMISION",
        "IVA",
        "EFECTIVO SEGURO",
        "ATT"
    ]

    # Ambiguous keywords that need detail line context
    AMBIGUOUS_KEYWORDS = [
        "PAGO CUENTA DE TERCERO"
    ]

    # Helper function to normalize description for classification
    def normalize_for_classification(desc: str) -> str:
        """Normalize description text for more robust keyword matching."""
        # Convert to uppercase
        norm = desc.upper()
        # Fix stuck words: RECIBIDO/ENVIADO followed immediately by letters
        norm = re.sub(r'(RECIBIDO)([A-Z]+)', r'\1 \2', norm)
        norm = re.sub(r'(ENVIADO)([A-Z]+)', r'\1 \2', norm)
        # Normalize transfer variations to standard form
        norm = re.sub(r'\b(TRANSFERENCIA|TRANSF)\b', 'TRANSF', norm)
        norm = re.sub(r'\b(TRASPASO|TRASP)\b', 'TRASP', norm)
        # Collapse multiple spaces to single space
        norm = re.sub(r'\s+', ' ', norm)
        return norm.strip()

    # Helper function to disambiguate using detail line
    def disambiguate_with_detail(description: str, detail: Optional[str], holder_key: Optional[str]) -> Optional[str]:
        """
        Disambiguate ambiguous transactions using detail line context.

        Returns: "ABONO", "CARGO", or None if can't disambiguate.
        """
        if not detail or not holder_key:
            return None

        desc_norm = normalize_for_classification(description)
        detail_norm = normalize_for_classification(detail)

        # Check if this is an ambiguous transfer
        is_ambiguous = any(kw in desc_norm for kw in AMBIGUOUS_KEYWORDS)
        if not is_ambiguous:
            return None

        # Check if detail shows transfer TO the account holder using compiled regex
        # Pattern: "TRANSF A", "TRANSFERENCIA A", "TRASP A", "TRASPASO A"
        if TRANSFER_TO_PATTERN.search(detail_norm):
            if holder_key in detail_norm:
                return "ABONO"  # Incoming transfer to account holder
            else:
                return "CARGO"  # Outgoing transfer to someone else

        return None

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
                if debug:
                    print("abono case a")

            elif current_balance < previous_balance:
                # balance went down: expense
                transaction["movement_type"] = "CARGO"
                transaction["amount"] = -amount_abs
                if debug:
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
                        if debug:
                            print("abono case a igual (saldo_operacion)")
                    else:  # saldo_op < previous_balance
                        transaction["movement_type"] = "CARGO"
                        transaction["amount"] = -amount_abs
                        if debug:
                            print("cargo case a igual (saldo_operacion)")
                else:
                    # Can't use saldo_operacion - try disambiguation first, then fall back to keywords
                    description_norm = normalize_for_classification(description)

                    # Check if this is an ambiguous transaction that can be disambiguated
                    is_ambiguous = any(kw in description_norm for kw in AMBIGUOUS_KEYWORDS)
                    detail = transaction.get("detail")

                    if is_ambiguous:
                        # Try disambiguation first for ambiguous keywords
                        disambiguated = disambiguate_with_detail(description, detail, account_holder_key)
                        if disambiguated:
                            transaction["movement_type"] = disambiguated
                            transaction["amount"] = amount_abs if disambiguated == "ABONO" else -amount_abs
                            if debug:
                                print(f"{disambiguated.lower()} case a igual (disambiguated)")
                            previous_balance = current_balance
                            continue

                    is_abono = False
                    for keyword in ABONO_KEYWORDS:
                        if keyword in description_norm:
                            is_abono = True
                            break

                    if is_abono:
                        transaction["movement_type"] = "ABONO"
                        transaction["amount"] = amount_abs
                        if debug:
                            print("abono case a igual (keywords)")
                    else:
                        # Check CARGO keywords
                        is_cargo = False
                        for keyword in CARGO_KEYWORDS:
                            if keyword in description_norm:
                                is_cargo = True
                                break

                        if is_cargo:
                            transaction["movement_type"] = "CARGO"
                            transaction["amount"] = -amount_abs
                            if debug:
                                print("cargo case a igual (keywords)")
                        else:
                            # ✅ UNKNOWN - user must decide
                            transaction["movement_type"] = "UNKNOWN"
                            transaction["amount"] = None
                            transaction["needs_review"] = True
                            if debug:
                                detail = transaction.get("detail")
                                print(f"unknown case a igual (no keywords) - Amount: {amount_abs}, Detail: {detail if detail else 'N/A'}")

            previous_balance = current_balance
                    
        # case B: No balance (use keywords + disambiguation)
        else:
            # Try disambiguation first for ambiguous transfers
            detail = transaction.get("detail")
            disambiguated = disambiguate_with_detail(description, detail, account_holder_key)

            if disambiguated:
                transaction["movement_type"] = disambiguated
                transaction["amount"] = amount_abs if disambiguated == "ABONO" else -amount_abs
                if debug:
                    print(f"{disambiguated.lower()} case b (disambiguated via detail)")
            else:
                # normalize description for classification
                description_norm = normalize_for_classification(description)

                # check abono keywords first
                is_abono = False
                for keyword in ABONO_KEYWORDS:
                    if keyword in description_norm:
                        is_abono = True
                        break

                if is_abono:
                    transaction["movement_type"] = "ABONO"
                    transaction["amount"] = amount_abs
                    if debug:
                        print("abono case b")
                else:
                    # Check CARGO keywords
                    is_cargo = False
                    for keyword in CARGO_KEYWORDS:
                        if keyword in description_norm:
                            is_cargo = True
                            break

                    if is_cargo:
                        transaction["movement_type"] = "CARGO"
                        transaction["amount"] = -amount_abs
                        if debug:
                            print("cargo case b")
                    else:
                        # ✅ UNKNOWN - user must decide
                        transaction["movement_type"] = "UNKNOWN"
                        transaction["amount"] = None
                        transaction["needs_review"] = True
                        if debug:
                            print(f"unknown case b (no keywords) - Amount: {amount_abs}, Detail: {detail if detail else 'N/A'}")

    # 3. validation (skip UNKNOWN transactions)
    
    # calculate totals 
    total_abonos = 0
    total_cargos = 0
    count_abonos = 0
    count_cargos = 0
    count_unknown = 0

    unknown_amount_total = 0.0
    for transaction in transactions:
        if transaction["movement_type"] == "ABONO":
            total_abonos += transaction["amount"]
            count_abonos += 1
        elif transaction["movement_type"] == "CARGO":
            total_cargos += abs(transaction["amount"])
            count_cargos += 1
        else:  # UNKNOWN
            count_unknown += 1
            unknown_amount_total += transaction["amount_abs"]

    # compare with summary
    expected_abonos = summary["deposits_amount"]
    expected_cargos = summary["charges_amount"]
    expected_count_abonos = summary["n_deposits"]
    expected_count_cargos = summary["n_charges"]

    # Calculate deltas
    deposits_delta = expected_abonos - total_abonos
    charges_delta = total_cargos - expected_cargos

    # Report classification results
    if debug:
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

        # Print mathematically correct deltas and unknown info
        print(f"INFO: Deposits delta (expected - calculated) = {deposits_delta:+,.2f}")
        print(f"INFO: Charges delta (calculated - expected) = {charges_delta:+,.2f}")
        print(f"INFO: Unknown transactions = {count_unknown} (total UNKNOWN amount = {unknown_amount_total:,.2f})")

        # Show UNKNOWN transaction descriptions for debugging
        if count_unknown > 0:
            print(f"\n{'='*70}")
            print(f"UNKNOWN TRANSACTION DESCRIPTIONS ({count_unknown} total)")
            print(f"{'='*70}")
            for i, t in enumerate(transactions, 1):
                if t.get('movement_type') == 'UNKNOWN':
                    print(f"{i}. {t['date']} | {t['description']}")
            print(f"{'='*70}\n")

        # Reconciliation audit - running balance validation
        print(f"\n{'='*70}")
        print("RECONCILIATION AUDIT")
        print(f"{'='*70}")

        running = summary["starting_balance"]
        print(f"Running balance starts at: {running:,.2f}")

        balance_breaks = []
        high_risk_transactions = []

        for i, t in enumerate(transactions):
            movement_type = t.get('movement_type')
            amount_abs = t['amount_abs']
            saldo_liquidacion = t.get('saldo_liquidacion')
            saldo_operacion = t.get('saldo_operacion')
            description = t['description']
            date = t['date']
            detail = t.get('detail', '')

            # Track classification method for high-risk detection
            has_balance = saldo_liquidacion is not None
            is_unknown = movement_type == 'UNKNOWN'
            is_ambiguous = any(kw in normalize_for_classification(description) for kw in AMBIGUOUS_KEYWORDS)

            # Update running balance based on classification
            running_before = running
            if movement_type == 'ABONO':
                running += amount_abs
            elif movement_type == 'CARGO':
                running -= amount_abs
            # UNKNOWN: don't change running (unresolved)

            # Check for balance breaks (only if we have saldo_liquidacion)
            if saldo_liquidacion is not None:
                running_rounded = round(running, 2)
                saldo_rounded = round(saldo_liquidacion, 2)
                diff = abs(running_rounded - saldo_rounded)

                if diff > 0.01:  # Mismatch detected
                    balance_breaks.append({
                        'index': i + 1,
                        'date': date,
                        'description': description,
                        'movement_type': movement_type,
                        'amount_abs': amount_abs,
                        'running_expected': running_rounded,
                        'saldo_actual': saldo_rounded,
                        'diff': diff,
                        'case': 'A' if has_balance else 'B'
                    })

            # Identify high-risk transactions
            risk_reasons = []
            if not has_balance:
                risk_reasons.append('NO_BALANCE')
            if is_unknown:
                risk_reasons.append('UNKNOWN')
            if is_ambiguous:
                risk_reasons.append('AMBIGUOUS')
            # Detect keyword-only classification (equal balance fallback)
            if has_balance and saldo_operacion is not None:
                prev_saldo = transactions[i-1].get('saldo_liquidacion') if i > 0 else summary["starting_balance"]
                if prev_saldo and abs(saldo_liquidacion - prev_saldo) < 0.01:
                    risk_reasons.append('KEYWORD_ONLY')

            if risk_reasons:
                high_risk_transactions.append({
                    'index': i + 1,
                    'date': date,
                    'description': description,
                    'movement_type': movement_type,
                    'amount_abs': amount_abs,
                    'reasons': risk_reasons,
                    'detail': detail[:50] if detail else 'N/A'
                })

        # Report balance breaks
        print(f"Number of BALANCE_BREAK flags: {len(balance_breaks)}")
        if balance_breaks:
            print(f"\nTop {min(10, len(balance_breaks))} Balance Breaks:")
            print(f"{'-'*70}")
            for brk in balance_breaks[:10]:
                print(f"{brk['index']:3}. {brk['date']} | {brk['description'][:40]}")
                print(f"     Type: {brk['movement_type']:7} | Amount: {brk['amount_abs']:>10,.2f}")
                print(f"     Running: {brk['running_expected']:>10,.2f} | Actual: {brk['saldo_actual']:>10,.2f} | Diff: {brk['diff']:>8,.2f}")
                print(f"     Case: {brk['case']}")
                print()

        # Report high-risk transactions
        print(f"\nHigh-Risk Transactions: {len(high_risk_transactions)}")
        if high_risk_transactions:
            print(f"Top {min(10, len(high_risk_transactions))}:")
            print(f"{'-'*70}")
            for risk in high_risk_transactions[:10]:
                reasons_str = ', '.join(risk['reasons'])
                print(f"{risk['index']:3}. {risk['date']} | {risk['description'][:35]}")
                print(f"     Type: {risk['movement_type']:7} | Amount: {risk['amount_abs']:>10,.2f}")
                print(f"     Risks: {reasons_str}")
                print(f"     Detail: {risk['detail']}")
                print()

        print(f"{'='*70}\n")

    return transactions


def parse_bbva_debit_statement(pdf_path: str, debug: bool = False) -> ParserResult:
    """
    Main public entry point for parsing a BBVA debit statement PDF.

    This function orchestrates the complete parsing pipeline:
    1. Extracts raw transaction lines from the PDF
    2. Parses each line into structured data
    3. Extracts the statement summary (totals, balances)
    4. Classifies transactions as CARGO/ABONO/UNKNOWN

    Args:
        pdf_path: Path to the BBVA debit statement PDF file
        debug: If True, print detailed debug information during parsing

    Returns:
        Dictionary with:
            - transactions: List of parsed and classified transactions
            - warnings: List of warning messages encountered during parsing
            - summary: Statement summary with totals and balances (or None if extraction failed)

    Example:
        >>> result = parse_bbva_debit_statement("/path/to/statement.pdf")
        >>> print(f"Found {len(result['transactions'])} transactions")
        >>> print(f"Warnings: {len(result['warnings'])}")
        >>> if result['summary']:
        ...     print(f"Final balance: ${result['summary']['final_balance']:,.2f}")
    """
    warnings: List[str] = []

    # Step 0: Extract account holder key for disambiguation
    account_holder_key = None
    try:
        account_holder_key = extract_account_holder_key(pdf_path)
        if debug and account_holder_key:
            print(f"Account holder key: {account_holder_key}")
    except Exception:
        pass  # Not critical, continue without it

    # Step 1: Extract raw transaction lines with detail context
    try:
        transaction_lines = extract_transaction_lines(pdf_path)
        if debug:
            print(f"\n{'='*70}")
            print(f"FOUND {len(transaction_lines)} RAW TRANSACTION LINES")
            print(f"{'='*70}\n")
    except Exception as e:
        warnings.append(f"Failed to extract transaction lines: {str(e)}")
        return {
            "transactions": [],
            "warnings": warnings,
            "summary": None
        }

    # Step 2: Parse each transaction line with detail context
    parsed_transactions: List[TransactionDict] = []
    failed_count = 0
    for trans_data in transaction_lines:
        main_line = trans_data['main_line']
        detail_line = trans_data.get('detail_line')
        parsed = parse_transaction_line(main_line, detail_line, debug=debug)
        if parsed:
            parsed_transactions.append(parsed)
        else:
            failed_count += 1
            if debug:
                print(f"Failed to parse line: {main_line}")

    if failed_count > 0:
        warnings.append(f"Failed to parse {failed_count} transaction line(s)")

    if debug:
        print(f"\n{'='*70}")
        print(f"SUCCESSFULLY PARSED: {len(parsed_transactions)}/{len(transaction_lines)}")
        print(f"{'='*70}\n")

    # Step 3: Extract statement summary
    summary: Optional[SummaryDict] = None
    try:
        summary = extract_statement_summary(pdf_path)
        if debug:
            print(f"Summary extracted successfully: {summary}")
    except ValueError as e:
        warnings.append(f"Summary extraction issue: {str(e)}")
        summary = None
    except Exception as e:
        warnings.append(f"Failed to extract summary: {str(e)}")
        summary = None

    # Step 4: Classify transactions (only if we have summary)
    if summary and parsed_transactions:
        try:
            parsed_transactions = determine_transaction_type(
                parsed_transactions,
                summary,
                account_holder_key,
                debug=debug
            )
            # Count transactions needing manual review
            unknown_count = sum(1 for t in parsed_transactions if t.get('movement_type') == 'UNKNOWN')
            if unknown_count > 0:
                warnings.append(f"{unknown_count} transactions need manual review (movement_type=UNKNOWN)")
        except Exception as e:
            warnings.append(f"Transaction classification failed: {str(e)}")
    elif not summary:
        warnings.append("Skipping transaction classification due to missing summary")

    return {
        "transactions": parsed_transactions,
        "warnings": warnings,
        "summary": summary
    }


if __name__ == "__main__":
    """
    Smoke test runner for BBVA debit statement parser.

    Usage:
        python backend/app/utils/pdf_parser.py <path_to_pdf>

    Or edit the pdf_path variable below and run:
        python backend/app/utils/pdf_parser.py
    """
    import sys

    # Default test PDF (edit this path for quick testing)
    pdf_path = "/Users/diegoferra/Documents/ASTRAFIN/STATEMENTS/BBVA_debit_dic25_diego.pdf"

    # Allow CLI argument to override
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

    # Run the parser
    result = parse_bbva_debit_statement(pdf_path, debug=True)

    # Display minimal results
    print(f"Transactions: {len(result['transactions'])}")
    print(f"Warnings: {len(result['warnings'])}")

    if result['summary']:
        summary = result['summary']
        print(f"Starting balance: {summary['starting_balance']:.2f}")
        print(f"Deposits: {summary['deposits_amount']:.2f}")
        print(f"Charges: {summary['charges_amount']:.2f}")
        print(f"Final balance: {summary['final_balance']:.2f}")
    else:
        print("No summary available")

