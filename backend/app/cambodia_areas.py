import json
from pathlib import Path

from typing_extensions import TypedDict


class Area(TypedDict):
    code: int
    name: str
    name_km: str


class Province(Area):
    districts: list[Area]


with Path(__file__).with_name("cambodia_areas.json").open(encoding="utf-8") as source:
    provinces: list[Province] = json.load(source)["provinces"]

provinces_by_code = {province["code"]: province for province in provinces}
districts_by_code = {district["code"]: district for province in provinces for district in province["districts"]}


def validate_province_code(code: int) -> int:
    if code not in provinces_by_code:
        raise ValueError("Choose a valid Cambodian province or capital.")
    return code


def validate_district_code(code: int) -> int:
    if code not in districts_by_code:
        raise ValueError("Choose a valid Cambodian district, municipality, or khan.")
    return code
