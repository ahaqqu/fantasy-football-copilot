"""Player fitness and status assessment."""


def assess_fitness_status(player: dict) -> dict[str, str]:
    """Assess player fitness status based on appearances and injuries."""
    apps = player.get("appearances", {})
    last_6_months = apps.get("last_6_months", 0)
    injuries = apps.get("injuries", 0)
    suspended = apps.get("suspended", False)

    if suspended:
        return {"status": "Suspended", "color": "red", "details": "Currently suspended"}

    if injuries >= 2:
        return {"status": "Doubtful", "color": "red", "details": f"{injuries} injuries in last 6 months"}

    if injuries == 1 and last_6_months < 8:
        return {"status": "Injury Risk", "color": "yellow", "details": f"{injuries} injury, {last_6_months} apps"}

    if last_6_months < 5:
        return {"status": "Rotation Risk", "color": "yellow", "details": f"Only {last_6_months} appearances"}

    return {"status": "Healthy", "color": "green", "details": f"{last_6_months} appearances, no issues"}


def get_fitness_color(status: str) -> str:
    """Get color for fitness status."""
    color_map = {
        "Healthy": "green",
        "Rotation Risk": "yellow",
        "Injury Risk": "yellow",
        "Doubtful": "red",
        "Suspended": "red",
    }
    return color_map.get(status, "gray")
