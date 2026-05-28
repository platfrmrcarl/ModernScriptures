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


def test_art_not_you_inverted_question():
    assert quick_modernize("Art not thou God in heaven?") == \
        "Are not you God in heaven?"


def test_relative_clause_art():
    # "Our Father which art in heaven" -- common KJV relative-clause form.
    assert quick_modernize(
        "Our Father which art in heaven, hallowed be thy name."
    ) == "Our Father which are in heaven, hallowed be your name."


def test_wilt_not_thou_inverted_question():
    assert quick_modernize("Wilt not thou possess it?") == \
        "Will not you possess it?"


def test_and_wilt_deferred_subject():
    # "if thou ... and wilt do" -- subject "thou" is several clauses back.
    assert quick_modernize(
        "If thou hearken, and wilt do what is right."
    ) == "If you hearken, and will do what is right."


def test_art_as_noun_still_safe_with_relative_clause_rule():
    # The new "who/which/that art" rule must not mutate "art of the perfumer".
    assert quick_modernize(
        "compounded according to the art of the perfumer."
    ) == "compounded according to the art of the perfumer."


def test_additional_archaic_aux_and_pronoun():
    assert quick_modernize(
        "Thou wast there. Thou didst speak. Thy God spake. Know thyself."
    ) == "You were there. You did speak. Your God spoke. Know yourself."


def test_but_wilt_and_and_art():
    # Continuation conjunctions where the subject "thou" was earlier.
    assert quick_modernize(
        "Remember me, but wilt give. Be patient, and art confident."
    ) == "Remember me, but will give. Be patient, and are confident."


def test_thyself_art():
    assert quick_modernize("Thou thyself art a guide.") == \
        "You yourself are a guide."


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


def test_archaic_adverbs():
    assert quick_modernize(
        "Wherefore I come hither. Whither shall I go? Whence came he?"
    ) == "Therefore I come here. Where shall I go? From where came he?"


def test_unto_and_verily():
    assert quick_modernize("Verily I say unto thee.") == \
        "Truly I say to you."


def test_howbeit_and_thither():
    assert quick_modernize("Howbeit he went thither.") == \
        "However he went there."


def test_full_archaic_verse_end_to_end():
    # A representative un-modernized Matthew verse.
    original = (
        "Thou shalt not tempt the Lord thy God. Verily I say unto thee, "
        "he that cometh unto me, I will in no wise cast out."
    )
    expected = (
        "You will not tempt the Lord your God. Truly I say to you, "
        "he that comes to me, I will in no wise cast out."
    )
    assert quick_modernize(original) == expected
