import os, re, sys
def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dirs = [os.path.join(root, "backend", "tests"), os.path.join(root, "frontend", "tests")]
    spec_dir = os.path.join(root, "docs", "specs")
    
    ac_def_regex = re.compile(r"^\s*-\s+\*\*(AC-[A-Z0-9]+-\d{3}-\d{2})\*\*", re.MULTILINE)
    ac_ref_regex = re.compile(r"\bAC-[A-Z0-9]+-\d{3}-\d{2}\b")
    
    defined_acs = set()
    for filename in os.listdir(spec_dir):
        if filename.endswith(".md") and filename != "README.md":
            with open(os.path.join(spec_dir, filename), encoding="utf-8") as f:
                defined_acs.update(ac_def_regex.findall(f.read()))

    referenced_acs = set()
    for d in test_dirs:
        for root_dir, _, files in os.walk(d):
            for f in files:
                if f.endswith(".py") or f.endswith(".ts"):
                    with open(os.path.join(root_dir, f), encoding="utf-8") as file:
                        referenced_acs.update(ac_ref_regex.findall(file.read()))

    missing = sorted(defined_acs - referenced_acs)
    stale = sorted(referenced_acs - defined_acs)
    
    if missing or stale:
        if missing:
            print("Missing test coverage for:")
            for ac in missing: print(f"  - {ac}")
        if stale:
            print("Unknown ACs referenced in tests:")
            for ac in stale: print(f"  - {ac}")
        sys.exit(1)
        
    print(f"Traceability check passed: {len(defined_acs)} acceptance criteria covered.")
    sys.exit(0)

if __name__ == "__main__":
    main()
