"""
Data Loader & CSV Validator

Loads payment lifecycle CSVs and validates their schema.
"""
import pandas as pd

REQUIRED_SCHEMAS = {
    "orders": ["order_id", "amount", "currency", "status", "created_at"],
    "payments": ["payment_id", "order_id", "amount", "currency", "status", "method", "created_at"],
    "refunds": ["refund_id", "payment_id", "order_id", "amount", "status", "created_at"],
    "settlements": ["settlement_id", "payment_id", "order_id", "amount", "batch_id", "status", "settled_at"],
    "finance_records": ["finance_id", "payment_id", "order_id", "type", "amount", "created_at"],
}


def validate_dataframe(df: pd.DataFrame, name: str) -> list[str]:
    """Validate a DataFrame against the expected schema. Returns list of errors."""
    errors = []
    if name not in REQUIRED_SCHEMAS:
        errors.append(f"Unknown data type: {name}")
        return errors

    expected_cols = REQUIRED_SCHEMAS[name]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        errors.append(f"{name}: missing columns {missing}")

    if df.empty:
        errors.append(f"{name}: DataFrame is empty")

    return errors


def load_csvs(file_dict: dict) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """
    Load CSVs from a dict of {name: file_path_or_buffer}.

    Returns:
        (data_dict, errors) where data_dict maps name → DataFrame.
    """
    data = {}
    all_errors = []

    for name, source in file_dict.items():
        try:
            df = pd.read_csv(source)
            errors = validate_dataframe(df, name)
            if errors:
                all_errors.extend(errors)
            else:
                data[name] = df
        except Exception as e:
            all_errors.append(f"{name}: failed to load — {e}")

    return data, all_errors


def load_sample_data(sample_dir: str = "data/sample") -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Load the pre-generated sample data."""
    import os
    file_dict = {
        "orders": os.path.join(sample_dir, "orders.csv"),
        "payments": os.path.join(sample_dir, "payments.csv"),
        "refunds": os.path.join(sample_dir, "refunds.csv"),
        "settlements": os.path.join(sample_dir, "settlements.csv"),
        "finance_records": os.path.join(sample_dir, "finance_records.csv"),
    }
    return load_csvs(file_dict)
