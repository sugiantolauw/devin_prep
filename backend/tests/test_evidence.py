from apex_diligence.evidence import build_evidence_pack


def test_pack_assembles_and_grounds_numbers():
    pack = build_evidence_pack()
    # FY summary covers both entities + Group across all four years.
    entities = {r.entity for r in pack.fy_summary}
    assert {"AU", "NZ", "Group"} <= entities
    assert {r.fy for r in pack.fy_summary} == {2021, 2022, 2023, 2024}

    # The registry and material anomalies are present.
    assert len(pack.registry.values) > 50
    assert pack.anomalies, "expected the material (normalisation-driving) anomalies"
    assert any(i.kind == "one_off_addback" for i in pack.normalisation_items)

    # allowed_numbers is the guardrail's ground truth and includes the headline figures.
    nums = pack.allowed_numbers()
    assert any(abs(n - 134_506_640) < 1 for n in nums)  # AU FY2024 revenue
    assert any(abs(n - 26_072_884) < 5 for n in nums)  # AU normalised EBITDA


def test_bridges_present_for_entities():
    pack = build_evidence_pack()
    bridge_entities = {b.entity for b in pack.bridges}
    assert bridge_entities == {"AU", "NZ"}
    au = next(b for b in pack.bridges if b.entity == "AU")
    assert au.reported_ebitda > au.normalised_ebitda
