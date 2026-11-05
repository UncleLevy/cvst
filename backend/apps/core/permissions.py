def is_admin(user) -> bool:
    """True for superusers and users whose role is 'admin'."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, "role", "") == "admin")
    )
