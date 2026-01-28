#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def _list_files(directory: Path) -> set[str]:
	if not directory.exists():
		return set()
	return {path.name for path in directory.iterdir() if path.is_file()}


def main() -> None:
	repo_root = Path(__file__).resolve().parent.parent
	logos_dir = repo_root / "logos_old"
	logos_2x_dir = repo_root / "logos_2x"
	logos_3x_dir = repo_root / "logos_3x"

	logos = _list_files(logos_dir)
	logos_2x = _list_files(logos_2x_dir)
	logos_3x = _list_files(logos_3x_dir)

	missing_2x = sorted(logo for logo in logos if logo not in logos_2x)
	missing_3x = sorted(logo for logo in logos if logo not in logos_3x)

	print(f"Logos in {logos_dir}: {len(logos)}")
	print(f"Logos in {logos_2x_dir}: {len(logos_2x)}")
	print(f"Logos in {logos_3x_dir}: {len(logos_3x)}")
	print("-")

	if missing_2x:
		print(f"Missing from {logos_2x_dir} ({len(missing_2x)}):")
		for logo in missing_2x:
			print(f"  {logo}")
	else:
		print(f"No missing logos in {logos_2x_dir}.")

	print("-")

	if missing_3x:
		print(f"Missing from {logos_3x_dir} ({len(missing_3x)}):")
		for logo in missing_3x:
			print(f"  {logo}")
	else:
		print(f"No missing logos in {logos_3x_dir}.")


if __name__ == "__main__":
	main()
