from pathlib import Path

# Example script: load rules + data, run harmonization, and write output.
#
# This file is intentionally verbose and commented so a new user can
# understand the minimal steps required to use the framework.

from harmonization_framework.harmonize import harmonize_file
from harmonization_framework.rule_registry import RuleRegistry


def main() -> None:
    # Find this demo directory so all paths are absolute and stable.
    base_dir = Path(__file__).resolve().parent

    input_path = base_dir / "input.csv"
    print("input_path: ", input_path)

    rules_path = base_dir / "rules.json"
    print("rules_path: ", rules_path)

    output_path = base_dir / "output.csv"
    print("output_path: ", output_path)

    # The RuleRegistry is the in-memory container for all harmonization rules.
    # Loading the JSON file builds a registry of source/target rules that
    # harmonize values from the source column into the target column.
    rules = RuleRegistry()
    rules.load(str(rules_path), clean=True)

    # Each pair is (source_column, target_column). These names must match
    # the rules in rules.json. The framework will:
    # 1) rename the column to the target name
    # 2) apply the rule for that source/target to each value
    harmonization_pairs = [
        ("age", "age_years"),
        ("weight_lbs", "weight_kg"),
        ("name", "given_name"),
        ("name", "family_name"),
        ("visit_type_code", "visit_type_label"),
    ]

    # Run the harmonization and save the output CSV.
    # dataset_name becomes the value of the "source dataset" column.
    harmonized = harmonize_file(
        input_path=str(input_path),
        output_path=str(output_path),
        harmonization_pairs=harmonization_pairs,
        rules=rules,
        dataset_name="demo",
    )

    # Reorder columns for readability in the demo output.
    preferred_order = [
        "given_name",
        "family_name",
        "age_years",
        "weight_kg",
        "visit_type_label",
        "source dataset",
        "original_id",
    ]
    ordered = [col for col in preferred_order if col in harmonized.columns]
    ordered += [col for col in harmonized.columns if col not in ordered]
    harmonized = harmonized[ordered]
    harmonized.to_csv(output_path, index=False)

    # The output file contains the transformed columns plus:
    # - "source dataset": the dataset_name value for each row
    # - "original_id": the original row index from the input file
    print(f"Wrote harmonized CSV to: {output_path}")


if __name__ == "__main__":
    main()
