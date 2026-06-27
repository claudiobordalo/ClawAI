import pytest

from clawai.goals import Goal
from clawai.goals.goal_validator import ValidationError, validate_goal


def _valid_goal(gid: str = "g1", title: str = "Valid") -> Goal:
    return Goal(
        id=gid,
        title=title,
        description="desc",
        success_criteria="criteria",
        priority=2,
    )


def test_valid_goal():
    g = _valid_goal()
    validate_goal(g)


def test_empty_id():
    with pytest.raises(ValueError, match="Goal id must not be empty"):
        _valid_goal(gid="")


def test_empty_title():
    with pytest.raises(ValueError, match="Goal title must not be empty"):
        _valid_goal(title="")


def test_empty_criteria():
    with pytest.raises(ValueError, match="Goal success_criteria must not be empty"):
        Goal(id="g1", title="Valid", description="desc", success_criteria="", priority=2)


def test_duplicate_title():
    existing = [_valid_goal(gid="existing", title="Original")]
    duplicate = _valid_goal(gid="new", title="Original")
    with pytest.raises(ValidationError) as exc_info:
        validate_goal(duplicate, existing_goals=existing)
    assert any("Duplicate goal title" in e for e in exc_info.value.errors)


def test_duplicate_title_case_insensitive():
    existing = [_valid_goal(gid="existing", title="Original")]
    duplicate_gid = _valid_goal(gid="new", title="original")
    with pytest.raises(ValidationError) as exc_info:
        validate_goal(duplicate_gid, existing_goals=existing)
    assert any("Duplicate goal title" in e for e in exc_info.value.errors)


def test_same_id_skips_duplicate_check():
    existing = [_valid_goal(gid="g1", title="Original")]
    same = _valid_goal(gid="g1", title="Original")
    validate_goal(same, existing_goals=existing)


def test_multiple_errors():
    with pytest.raises(ValueError):
        _valid_goal(gid="", title="")


def test_validation_error_has_errors_list():
    g = _valid_goal(gid="g1", title="My Title")
    existing = [_valid_goal(gid="existing", title="My Title")]
    try:
        validate_goal(g, existing_goals=existing)
    except ValidationError as e:
        assert len(e.errors) >= 1
        assert "Duplicate goal title" in e.errors[0]
