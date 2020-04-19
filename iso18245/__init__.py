import csv
import os.path
from collections import namedtuple
from typing import Dict, List

from pkg_resources import resource_filename


class MCCNotFound(KeyError):
	pass


class InvalidMCC(ValueError):
	pass


MCC = namedtuple(
	"MCC",
	("range", "iso_description", "usda_description", "stripe_description", "stripe_code"),
)
MCCRange = namedtuple("MCCRange", ("start", "end", "description", "reserved"))

_cached_csv: Dict[str, object] = {}


def _load_csv(path: str):
	full_path = resource_filename("iso18245", os.path.join("data", path))
	if path not in _cached_csv:
		with open(full_path, "r") as f:
			reader = csv.reader(f)
			_cached_csv[path] = list(reader)[1:]

	return _cached_csv[path]


def _find_mcc_in_csv(mcc: str, path: str) -> List[str]:
	for row in _load_csv(path):
		if row[0] == mcc:
			return row[1:]
	return []


def validate_mcc(mcc: str) -> int:
	mcc_as_num = int(mcc)
	if mcc_as_num < 0 or mcc_as_num > 9999:
		raise InvalidMCC(mcc)

	return mcc_as_num


def get_mcc(mcc: str) -> MCC:
	mcc_range = get_mcc_range(mcc)
	found = False
	iso_description = ""
	usda_description = ""
	stripe_description = ""
	stripe_code = ""

	if not mcc_range.reserved:
		data = _find_mcc_in_csv(mcc, "iso18245_official_list.csv")
		if data:
			iso_description, found = data[0], True

	usda_data = _find_mcc_in_csv(mcc, "usda_list.csv")
	if usda_data:
		usda_description, found = usda_data[0], True

	stripe_info = _find_mcc_in_csv(mcc, "stripe_list.csv")
	if stripe_info:
		stripe_description, stripe_code, found = stripe_info[0], stripe_info[1], True

	if not found:
		raise MCCNotFound(mcc)

	return MCC(
		range=mcc_range,
		iso_description=iso_description,
		usda_description=usda_description,
		stripe_description=stripe_description,
		stripe_code=stripe_code,
	)


def get_mcc_range(mcc: str):
	mcc_as_num = validate_mcc(mcc)
	range_data = _load_csv("iso18245_ranges.csv")
	for range_start, range_end, description in range_data:
		start_num, end_num = int(range_start), int(range_end)
		if start_num <= mcc_as_num <= end_num:
			return MCCRange(
				range_start, range_end, description, reserved=description.startswith("Reserved")
			)

		if end_num > mcc_as_num:
			break

	raise RuntimeError(f"Could not find correct MCC range for {mcc} (likely a bug)")