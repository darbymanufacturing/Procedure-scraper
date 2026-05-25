"""Official manufacturer owner-manual portals.

These portals provide free owner's manuals directly from the automaker.
For mechanical repair tasks (clutch, engine, brakes, etc.) the confidence
score is automatically reduced because owner's manuals don't contain
workshop/repair procedures — a service manual is needed instead.
"""

from __future__ import annotations

from typing import FrozenSet, List

from scraper.models import ManualResult
from scraper.sources.base import Source

# Maps make (lowercase) → (portal_name, portal_url, notes)
_MANUFACTURER_PORTALS = {
    "toyota": (
        "Toyota Owners Portal",
        "https://www.toyota.com/owners/resources/manuals-warranties",
        "Free owner's manual from Toyota — select your vehicle on the page",
    ),
    "honda": (
        "Honda Owners Portal",
        "https://owners.honda.com/vehicles/information/manuals",
        "Free owner's manual from Honda",
    ),
    "ford": (
        "Ford Owner's Manual Portal",
        "https://owner.ford.com/tools/account/how-tos/owner-manuals.html",
        "Free owner's manual from Ford — searchable by year/model",
    ),
    "chevrolet": (
        "Chevrolet Owner Center",
        "https://www.chevrolet.com/support/content/pages/owner-center",
        "Free owner's manual from Chevrolet",
    ),
    "gmc": (
        "GMC Owner Center",
        "https://www.gmc.com/support/content/pages/owner-center",
        "Free owner's manual from GMC",
    ),
    "buick": (
        "Buick Owner Center",
        "https://www.buick.com/support/content/pages/owner-center",
        "Free owner's manual from Buick",
    ),
    "cadillac": (
        "Cadillac Owner Center",
        "https://www.cadillac.com/support/content/pages/owner-center",
        "Free owner's manual from Cadillac",
    ),
    "dodge": (
        "Mopar Owner Connect",
        "https://www.mopar.com/en-us/my-vehicle/owner-manuals.html",
        "Free owner's manual via Mopar/Stellantis",
    ),
    "chrysler": (
        "Mopar Owner Connect",
        "https://www.mopar.com/en-us/my-vehicle/owner-manuals.html",
        "Free owner's manual via Mopar/Stellantis",
    ),
    "jeep": (
        "Jeep Owner Connect",
        "https://www.mopar.com/en-us/my-vehicle/owner-manuals.html",
        "Free owner's manual via Mopar/Stellantis",
    ),
    "ram": (
        "Mopar Owner Connect",
        "https://www.mopar.com/en-us/my-vehicle/owner-manuals.html",
        "Free owner's manual via Mopar/Stellantis",
    ),
    "fiat": (
        "Mopar Owner Connect",
        "https://www.mopar.com/en-us/my-vehicle/owner-manuals.html",
        "Free owner's manual via Mopar/Stellantis",
    ),
    "nissan": (
        "Nissan Owner Portal",
        "https://owners.nissan.com/resource-center/owner-manuals",
        "Free owner's manual from Nissan",
    ),
    "infiniti": (
        "INFINITI Owner Portal",
        "https://owners.infinitiusa.com/ownercenter/oc/home",
        "Free owner's manual from INFINITI",
    ),
    "hyundai": (
        "Hyundai Owner's Manual",
        "https://owners.hyundaiusa.com/us/en/index.html",
        "Free owner's manual from Hyundai",
    ),
    "kia": (
        "Kia Owner Center",
        "https://www.kia.com/us/en/vehicle-manuals",
        "Free owner's manual from Kia",
    ),
    "subaru": (
        "Subaru Owner's Manual",
        "https://www.subaru.com/owners/index.html",
        "Free owner's manual from Subaru",
    ),
    "mazda": (
        "Mazda Owner's Manual",
        "https://www.mazdausa.com/owners/manuals",
        "Free owner's manual from Mazda",
    ),
    "mitsubishi": (
        "Mitsubishi Owner Manual",
        "https://www.mitsubishicars.com/support/owner-manuals",
        "Free owner's manual from Mitsubishi",
    ),
    "volkswagen": (
        "Volkswagen Owner's Manual",
        "https://www.vw.com/content/dam/vwag/us/owners/manuals/",
        "Free owner's manual from Volkswagen (search on vw.com)",
    ),
    "audi": (
        "Audi Online Owner's Manual",
        "https://www.audiusa.com/us/web/en/tools/owner-s-manuals.html",
        "Free owner's manual from Audi",
    ),
    "bmw": (
        "BMW Owner's Manual Portal",
        "https://www.bmwusa.com/service-and-support/my-bmw-app/bmw-owner-s-manual.html",
        "Free owner's manual from BMW",
    ),
    "mercedes-benz": (
        "Mercedes-Benz Interactive Owner's Manual",
        "https://www.mercedes-benz.com/en/vehicles/owner-s-manual/",
        "Free interactive owner's manual from Mercedes-Benz",
    ),
    "mercedes": (
        "Mercedes-Benz Interactive Owner's Manual",
        "https://www.mercedes-benz.com/en/vehicles/owner-s-manual/",
        "Free interactive owner's manual from Mercedes-Benz",
    ),
    "volvo": (
        "Volvo Car Owner's Manual",
        "https://www.volvocars.com/en-us/support/manuals",
        "Free owner's manual from Volvo",
    ),
    "tesla": (
        "Tesla Owner's Manual",
        "https://www.tesla.com/ownersmanual",
        "Free online owner's manual from Tesla",
    ),
    "lexus": (
        "Lexus Owner's Manual",
        "https://www.lexus.com/owners/resources/manuals",
        "Free owner's manual from Lexus",
    ),
    "acura": (
        "Acura Owner's Manual",
        "https://owners.acura.com/resource-center/owner-manuals",
        "Free owner's manual from Acura",
    ),
    "porsche": (
        "Porsche Digital Owner's Manual",
        "https://tequipment.porsche.com/en/US/support/owner-manual/",
        "Free digital owner's manual from Porsche",
    ),
    "land rover": (
        "Land Rover Owner's Manual",
        "https://www.landroverusa.com/ownership/digital-owner-s-manual.html",
        "Free owner's manual from Land Rover",
    ),
    "jaguar": (
        "Jaguar InControl Owner's Manual",
        "https://www.jaguarusa.com/support/owners-manual.html",
        "Free owner's manual from Jaguar",
    ),
    "saab": (
        "Saab Owners Club Manual Archive",
        "https://www.saabownersclub.co.uk/forum/index.php/board,15.0.html",
        "Saab is discontinued — community forum hosts scanned manuals",
    ),
}

# Keywords that indicate a hands-on mechanical repair task.
# Owner's manuals don't cover these — only FSMs/workshop manuals do.
_MECHANICAL_KEYWORDS: FrozenSet[str] = frozenset({
    "clutch", "transmission", "gearbox", "engine", "timing belt", "timing chain",
    "head gasket", "brake", "brakes", "caliper", "rotor", "pad", "pads",
    "suspension", "alternator", "starter", "water pump", "fuel pump",
    "radiator", "thermostat", "cv joint", "axle", "differential",
    "valve", "piston", "camshaft", "crankshaft", "turbo", "supercharger",
    "exhaust", "catalytic", "ignition", "spark plug", "injector", "carburetor",
    "strut", "shock", "ball joint", "tie rod", "steering rack", "power steering",
    "compressor", "serpentine belt", "drive belt", "flywheel", "pressure plate",
    "throw-out bearing", "release bearing", "oil seal", "gasket", "replace",
    "replacement", "rebuild", "overhaul", "disassemble", "repair",
})


def _is_mechanical(task: str) -> bool:
    """Return True if the task description implies a hands-on mechanical repair."""
    task_lower = task.lower()
    return any(kw in task_lower for kw in _MECHANICAL_KEYWORDS)


class ManufacturerSource(Source):
    name = "Manufacturer Portal"

    def search(self, make: str, model: str, year: int, task: str = "") -> List[ManualResult]:
        results: List[ManualResult] = []
        try:
            make_key = make.strip().lower()
            if make_key not in _MANUFACTURER_PORTALS:
                return results

            portal_name, portal_url, base_notes = _MANUFACTURER_PORTALS[make_key]

            mechanical = _is_mechanical(task)

            if mechanical:
                # Owner's manuals don't contain workshop repair procedures.
                # Demote the result so service manual sources rank above it.
                confidence = 0.25
                notes = (
                    f"{base_notes}. "
                    "⚠️  Owner's manuals do NOT cover mechanical repairs like this — "
                    "use the Haynes, AutoZone, or archive.org results above instead."
                )
            else:
                confidence = 0.7
                notes = base_notes

            results.append(
                ManualResult(
                    title=f"{portal_name}: {year} {make} {model} Owner's Manual",
                    source=self.name,
                    url=portal_url,
                    format="pdf",
                    confidence=confidence,
                    notes=notes,
                )
            )
        except Exception:
            pass
        return results
