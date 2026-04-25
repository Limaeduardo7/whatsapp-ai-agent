from src.marketing_automation import _detect_language, _find_sequence_for_product


def test_detect_language_from_product_name():
    assert _detect_language({}, "La Clave del Poder") == "es"
    assert _detect_language({}, "The Key to Power") == "en"
    assert _detect_language({}, "A Chave do Poder") == "pt-BR"


def test_detect_language_from_payload_for_ambiguous_product():
    payload = {"data": {"buyer": {"language": "es"}}}
    assert _detect_language(payload, "Energy Hack 8D") == "es"


def test_find_sequence_prefers_matching_language_for_ambiguous_product():
    sequence = _find_sequence_for_product("Energy Hack 8D", "en")
    assert sequence is not None
    assert sequence["id"] == "seq_en_energy_para_quantum"
