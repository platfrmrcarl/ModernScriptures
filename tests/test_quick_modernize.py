from modern_scriptures.quick_modernize import quick_modernize


def test_replaces_thee_thou_ye():
    assert quick_modernize("I tell thee, thou and ye shall hear.") == \
        "I tell you, you and you shall hear."


def test_replaces_thy_with_your():
    assert quick_modernize("Honour thy father and thy mother.") == \
        "Honour your father and your mother."


def test_thine_before_vowel_becomes_your():
    assert quick_modernize("Thine eye shall not pity.") == \
        "Your eye shall not pity."


def test_thine_as_pronoun_becomes_yours():
    assert quick_modernize("The kingdom is thine.") == \
        "The kingdom is yours."


def test_preserves_case_on_pronouns():
    assert quick_modernize("Thou art my Son.") == "You are my Son."


def test_replaces_auxiliaries():
    assert quick_modernize("He hath spoken. He doth know. Thou art wise.") == \
        "He has spoken. He does know. You are wise."


def test_shalt_and_wilt():
    assert quick_modernize("Thou shalt not. Wilt thou go?") == \
        "You will not. Will you go?"


def test_word_boundary_does_not_mutate_proper_name_elizabeth():
    # No -eth/-est rule should chew into Elizabeth.
    assert quick_modernize("Elizabeth bare a son.") == "Elizabeth bare a son."


def test_word_boundary_does_not_mutate_other_words():
    # "Other" contains "the" - must not be mutated.
    assert quick_modernize("Other men also.") == "Other men also."
