from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Element:
    atomic_number: int
    symbol: str
    name: str
    atomic_mass: float


ELEMENTS: List[Element] = [
    Element(1, "H", "Hydrogen", 1.008),
    Element(2, "He", "Helium", 4.0026),
    Element(3, "Li", "Lithium", 6.94),
    Element(4, "Be", "Beryllium", 9.0122),
    Element(5, "B", "Boron", 10.81),
    Element(6, "C", "Carbon", 12.011),
    Element(7, "N", "Nitrogen", 14.007),
    Element(8, "O", "Oxygen", 15.999),
    Element(9, "F", "Fluorine", 18.998),
    Element(10, "Ne", "Neon", 20.180),
    Element(11, "Na", "Sodium", 22.990),
    Element(12, "Mg", "Magnesium", 24.305),
    Element(13, "Al", "Aluminium", 26.982),
    Element(14, "Si", "Silicon", 28.085),
    Element(15, "P", "Phosphorus", 30.974),
    Element(16, "S", "Sulfur", 32.06),
    Element(17, "Cl", "Chlorine", 35.45),
    Element(18, "Ar", "Argon", 39.948),
    Element(19, "K", "Potassium", 39.098),
    Element(20, "Ca", "Calcium", 40.078),
    Element(21, "Sc", "Scandium", 44.956),
    Element(22, "Ti", "Titanium", 47.867),
    Element(23, "V", "Vanadium", 50.942),
    Element(24, "Cr", "Chromium", 51.996),
    Element(25, "Mn", "Manganese", 54.938),
    Element(26, "Fe", "Iron", 55.845),
    Element(27, "Co", "Cobalt", 58.933),
    Element(28, "Ni", "Nickel", 58.693),
    Element(29, "Cu", "Copper", 63.546),
    Element(30, "Zn", "Zinc", 65.38),
    Element(31, "Ga", "Gallium", 69.723),
    Element(32, "Ge", "Germanium", 72.630),
    Element(33, "As", "Arsenic", 74.922),
    Element(34, "Se", "Selenium", 78.971),
    Element(35, "Br", "Bromine", 79.904),
    Element(36, "Kr", "Krypton", 83.798),
    Element(37, "Rb", "Rubidium", 85.468),
    Element(38, "Sr", "Strontium", 87.62),
    Element(39, "Y", "Yttrium", 88.906),
    Element(40, "Zr", "Zirconium", 91.224),
    Element(41, "Nb", "Niobium", 92.906),
    Element(42, "Mo", "Molybdenum", 95.95),
    Element(43, "Tc", "Technetium", 98.0),
    Element(44, "Ru", "Ruthenium", 101.07),
    Element(45, "Rh", "Rhodium", 102.91),
    Element(46, "Pd", "Palladium", 106.42),
    Element(47, "Ag", "Silver", 107.868),
    Element(48, "Cd", "Cadmium", 112.414),
    Element(49, "In", "Indium", 114.818),
    Element(50, "Sn", "Tin", 118.710),
    Element(51, "Sb", "Antimony", 121.760),
    Element(52, "Te", "Tellurium", 127.60),
    Element(53, "I", "Iodine", 126.904),
    Element(54, "Xe", "Xenon", 131.293),
    Element(55, "Cs", "Caesium", 132.905),
    Element(56, "Ba", "Barium", 137.327),
    Element(57, "La", "Lanthanum", 138.905),
    Element(58, "Ce", "Cerium", 140.116),
    Element(59, "Pr", "Praseodymium", 140.908),
    Element(60, "Nd", "Neodymium", 144.242),
    Element(61, "Pm", "Promethium", 145.0),
    Element(62, "Sm", "Samarium", 150.36),
    Element(63, "Eu", "Europium", 151.964),
    Element(64, "Gd", "Gadolinium", 157.25),
    Element(65, "Tb", "Terbium", 158.925),
    Element(66, "Dy", "Dysprosium", 162.500),
    Element(67, "Ho", "Holmium", 164.930),
    Element(68, "Er", "Erbium", 167.259),
    Element(69, "Tm", "Thulium", 168.934),
    Element(70, "Yb", "Ytterbium", 173.045),
    Element(71, "Lu", "Lutetium", 174.967),
    Element(72, "Hf", "Hafnium", 178.49),
    Element(73, "Ta", "Tantalum", 180.948),
    Element(74, "W", "Tungsten", 183.84),
    Element(75, "Re", "Rhenium", 186.207),
    Element(76, "Os", "Osmium", 190.23),
    Element(77, "Ir", "Iridium", 192.217),
    Element(78, "Pt", "Platinum", 195.084),
    Element(79, "Au", "Gold", 196.967),
    Element(80, "Hg", "Mercury", 200.592),
    Element(81, "Tl", "Thallium", 204.38),
    Element(82, "Pb", "Lead", 207.2),
    Element(83, "Bi", "Bismuth", 208.980),
    Element(84, "Po", "Polonium", 209.0),
    Element(85, "At", "Astatine", 210.0),
    Element(86, "Rn", "Radon", 222.0),
    Element(87, "Fr", "Francium", 223.0),
    Element(88, "Ra", "Radium", 226.0),
    Element(89, "Ac", "Actinium", 227.0),
    Element(90, "Th", "Thorium", 232.038),
    Element(91, "Pa", "Protactinium", 231.036),
    Element(92, "U", "Uranium", 238.029),
    Element(93, "Np", "Neptunium", 237.0),
    Element(94, "Pu", "Plutonium", 244.0),
    Element(95, "Am", "Americium", 243.0),
    Element(96, "Cm", "Curium", 247.0),
    Element(97, "Bk", "Berkelium", 247.0),
    Element(98, "Cf", "Californium", 251.0),
    Element(99, "Es", "Einsteinium", 252.0),
    Element(100, "Fm", "Fermium", 257.0),
    Element(101, "Md", "Mendelevium", 258.0),
    Element(102, "No", "Nobelium", 259.0),
    Element(103, "Lr", "Lawrencium", 266.0),
    Element(104, "Rf", "Rutherfordium", 267.0),
    Element(105, "Db", "Dubnium", 270.0),
    Element(106, "Sg", "Seaborgium", 271.0),
    Element(107, "Bh", "Bohrium", 270.0),
    Element(108, "Hs", "Hassium", 277.0),
    Element(109, "Mt", "Meitnerium", 278.0),
    Element(110, "Ds", "Darmstadtium", 281.0),
    Element(111, "Rg", "Roentgenium", 282.0),
    Element(112, "Cn", "Copernicium", 285.0),
    Element(113, "Nh", "Nihonium", 286.0),
    Element(114, "Fl", "Flerovium", 289.0),
    Element(115, "Mc", "Moscovium", 290.0),
    Element(116, "Lv", "Livermorium", 293.0),
    Element(117, "Ts", "Tennessine", 294.0),
    Element(118, "Og", "Oganesson", 294.0),
]

BY_SYMBOL: Dict[str, Element] = {e.symbol: e for e in ELEMENTS}
BY_NUMBER: Dict[int, Element] = {e.atomic_number: e for e in ELEMENTS}

_TOKEN_RE = re.compile(r"([A-Z][a-z]?|\d+|[()\[\]{}])")


def _parse_tokens(tokens: List[str], i: int = 0) -> Tuple[Counter, int]:
    out = Counter()

    while i < len(tokens):
        t = tokens[i]

        if t in ")]}":
    from typing import Optional
            return out, i + 1

        if t in "([{":
            inner, i = _parse_tokens(tokens, i + 1)
            mult = 1
            if i < len(tokens) and tokens[i].isdigit():
                mult = int(tokens[i])
                i += 1
            for k, v in inner.items():
        state: Optional[str] = None
        melting_point: Optional[float] = None  # °C
        boiling_point: Optional[float] = None  # °C
        hardness: Optional[float] = None       # Mohs
        durability: Optional[str] = None       # Descriptor
        stability: Optional[str] = None        # Categorical
                out[k] += v * mult
            continue

        if re.match(r"[A-Z][a-z]?", t):
            if t not in BY_SYMBOL:
                raise ValueError(f"Unknown element symbol: {t}")
            qty = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                qty = int(tokens[i + 1])
                i += 1
            out[t] += qty
            i += 1
            continue

        raise ValueError(f"Unexpected token: {t}")

    return out, i


def parse_formula(formula: str) -> Counter:
    """Return element quantities from a chemical formula.

    Supports nested parentheses and hydrate-style split by '.' or '·'.
    Example: Al2(SO4)3, CuSO4·5H2O
    """
    total = Counter()
    formula = formula.replace(" ", "")
    if not formula:
        raise ValueError("Formula cannot be empty")

    parts = re.split(r"[·.]", formula)
    for part in parts:
        if not part:
            continue

        lead = re.match(r"^(\d+)(.*)$", part)
        multiplier = 1
        core = part
        if lead:
            multiplier = int(lead.group(1))
            core = lead.group(2)

        tokens = _TOKEN_RE.findall(core)
        if "".join(tokens) != core:
        Element(43, "Tc", "Technetium", 98.0, state=None, melting_point=None, boiling_point=None, hardness=None, durability=None, stability=None),

        parsed, idx = _parse_tokens(tokens)
        if idx != len(tokens):
            raise ValueError(f"Unparsed token remains in segment: {part}")

        for sym, qty in parsed.items():
            total[sym] += qty * multiplier

    return total


def molar_mass(counts: Counter) -> float:
    return sum(BY_SYMBOL[s].atomic_mass * n for s, n in counts.items())


def mass_percentages(counts: Counter) -> Dict[str, float]:
    total = molar_mass(counts)
    if total <= 0:
        return {}
    return {
        s: (BY_SYMBOL[s].atomic_mass * n / total) * 100
        for s, n in sorted(counts.items(), key=lambda x: BY_SYMBOL[x[0]].atomic_number)
    }


def explain_math() -> str:
    return (
        "Atomic and structural math:\n"
        "1) Atomic identity: Z = number of protons.\n"
        "2) Nucleon relation: A = Z + N, so N = A - Z.\n"
        "3) Neutral atom charge balance: p = e (protons = electrons).\n"
        "4) Ion charge: q = p - e.\n"
        "5) Compound atom count: n_total = Σ n_i.\n"
        "6) Molar mass: M = Σ n_i * m_i (g/mol).\n"
        "7) Mass fraction of element i: w_i = (n_i * m_i) / M.\n"
        "8) Percent composition: %i = 100 * w_i.\n"
        "9) Empirical ratio from masses: n_i = m_i / molar_mass_i, then divide by min(n_i).\n"
        "10) Electronic structure drives chemistry: valence e- controls bonding and oxidation states.\n"
    )


def list_elements() -> str:
    header = f"{'Z':>3}  {'Sym':<3}  {'Name':<15}  {'Atomic Mass (u)':>14}"
    rows = [header, "-" * len(header)]
    for e in ELEMENTS:
        rows.append(f"{e.atomic_number:>3}  {e.symbol:<3}  {e.name:<15}  {e.atomic_mass:>14.4f}")
    return "\n".join(rows)


def build_compound_report(formula: str) -> str:
    counts = parse_formula(formula)
    mm = molar_mass(counts)
    pct = mass_percentages(counts)

    lines = [f"Compound: {formula}", "", "Element quantities:"]
    for sym, qty in sorted(counts.items(), key=lambda x: BY_SYMBOL[x[0]].atomic_number):
        e = BY_SYMBOL[sym]
        lines.append(f"- {e.name} ({sym}): {qty}")

    lines.append("")
    lines.append(f"Total atoms in formula unit: {sum(counts.values())}")
    lines.append(f"Molar mass: {mm:.5f} g/mol")
    lines.append("")
    lines.append("Mass percentages:")
    for sym, p in pct.items():
        lines.append(f"- {sym}: {p:.4f}%")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Elements table resources + compound quantity builder"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all elements")

    info = sub.add_parser("element", help="Show one element by symbol or atomic number")
    info.add_argument("value")

    qty = sub.add_parser("quantity", help="Get element quantities from formula")
    qty.add_argument("formula")

    build = sub.add_parser("build", help="Build full compound resource report")
    build.add_argument("formula")

    sub.add_parser("math", help="Show core chemistry math")

    args = parser.parse_args()

    if args.cmd == "list":
        print(list_elements())
        return

    if args.cmd == "element":
        v = args.value.strip()
        elem = None
        if v.isdigit():
            elem = BY_NUMBER.get(int(v))
        else:
            v = v[0].upper() + v[1:].lower() if len(v) > 1 else v.upper()
            elem = BY_SYMBOL.get(v)

        if not elem:
            raise SystemExit("Element not found")

        print(f"Z: {elem.atomic_number}")
        print(f"Symbol: {elem.symbol}")
        print(f"Name: {elem.name}")
        print(f"Atomic mass: {elem.atomic_mass} u")
        return

    if args.cmd == "quantity":
        counts = parse_formula(args.formula)
        for sym, qty in sorted(counts.items(), key=lambda x: BY_SYMBOL[x[0]].atomic_number):
            print(f"{sym}: {qty}")
        return

    if args.cmd == "build":
        print(build_compound_report(args.formula))
        return

    if args.cmd == "math":
        print(explain_math())


if __name__ == "__main__":
    main()
