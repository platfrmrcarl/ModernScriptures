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
    # When Task 4 adds saith/cometh/... the \b in those rules must keep Elizabeth safe.
    assert quick_modernize("Elizabeth bare a son.") == "Elizabeth bare a son."


def test_word_boundary_does_not_mutate_other_words():
    # Forward-looking guardrail: any future rule looking for 'the' or 'art' must respect \b so 'Other' stays intact.
    assert quick_modernize("Other men also.") == "Other men also."


def test_art_as_noun_is_not_mutated():
    # "art" is only a verb after a pronoun; the noun must survive.
    assert quick_modernize("an ointment after the art of the apothecary.") == \
        "an ointment after the art of the apothecary."


def test_wilt_as_verb_is_not_mutated():
    # "wilt" without an adjacent thou/you is not the auxiliary verb.
    assert quick_modernize("The flowers wilt in the sun.") == \
        "The flowers wilt in the sun."


def test_art_thou_and_thou_art_still_modernized():
    # The two valid auxiliary contexts must still fire.
    assert quick_modernize("Where art thou? Thou art mine.") == \
        "Where are you? You are mine."


def test_wilt_thou_and_thou_wilt_still_modernized():
    assert quick_modernize("Wilt thou go? Thou wilt see.") == \
        "Will you go? You will see."


def test_explicit_eth_endings():
    assert quick_modernize(
        "He saith. He cometh. He goeth. He knoweth. He doeth."
    ) == "He says. He comes. He goes. He knows. He does."


def test_explicit_est_endings():
    assert quick_modernize(
        "Thou knowest. Thou sayest. Thou doest. Thou believest."
    ) == "You know. You say. You do. You believe."


def test_eth_est_does_not_overreach():
    # No generic -eth/-est rule -- only the explicit list. Words not on
    # the list stay as-is. This is a conscious tradeoff.
    assert quick_modernize("He doubteth not.") == "He doubteth not."
