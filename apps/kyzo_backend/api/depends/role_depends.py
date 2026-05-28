"""
Role-based access control dependencies for FastAPI routes.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status

from apps.kyzo_backend.api.depends.auth_depends import get_current_active_user
from apps.kyzo_backend.config import UserRole
from apps.kyzo_backend.data import User


class RoleChecker:
    """
    A reusable dependency provider for role-based access control (RBAC).

    This class allows endpoints to restrict access based on a user's role.
    Since it implements `__call__`, instances of this class can be passed
    directly into FastAPI's `Depends()`.

    Attributes:
        allowed_roles (list[UserRole]): The collection of roles authorized
                                         to access the resource.
    """

    def __init__(self, allowed_roles: list[UserRole]):
        """
        Initializes the RoleChecker with a specific set of allowed roles.

        Args:
            allowed_roles (list[UserRole]): Roles that are granted access.
        """
        self.allowed_roles = allowed_roles

    def __call__(
            self,
            current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        """
        Validates the authenticated user's role against the allowed roles.

        This method is automatically executed by FastAPI during dependency injection.

        Args:
            current_user (User): The currently authenticated and active user
                                  resolved from the bearer token.

        Returns:
            User: The validated user instance if their role matches.

        Raises:
            HTTPException: 403 (Forbidden) if the user's role is not contained
                           within the allowed roles.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
        return current_user


def require_admin(
        user: Annotated[User, Depends(RoleChecker([
            UserRole.ADMIN
        ]))]
) -> User:
    """
    Dependency to enforce that the requesting user has administrative privileges.

    This acts as a shorthand alias that permits access to administrators
    It ensures the user is authenticated, active, and holds the ADMIN role.

    Args:
        user (User): The authenticated user validated by the RoleChecker.

    Returns:
        User: The authenticated administrator's user record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but not an admin.
    """
    return user


def require_student(
        user: Annotated[User, Depends(RoleChecker([
            UserRole.STUDENT
        ]))]
) -> User:
    """
    Dependency to enforce that the requesting user is a student.

    This acts as a shorthand alias that permits access to students
    It ensures the user is authenticated, active, and holds the STUDENT role.

    Args:
        user (User): The authenticated user validated by the RoleChecker.

    Returns:
        User: The authenticated administrator's user record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated but not an admin.
    """
    return user


def require_teacher_or_admin(
        user: Annotated[User, Depends(RoleChecker([
            UserRole.TEACHER,
            UserRole.ADMIN
        ]))]
) -> User:
    """
    Dependency to restrict access to teachers and administrators.

    This acts as a shorthand alias that permits access to teacher and administrators.
    It permits access only if the authenticated user holds either the TEACHER or
    ADMIN role, effectively blocking student accounts.

    Args:
        user (User): The authenticated user validated by the RoleChecker.

    Returns:
        User: The authenticated teacher's or administrator's user record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is authenticated (e.g., a student)
              but lacks required privileges.
    """
    return user


def require_student_or_admin(
        user: Annotated[User, Depends(RoleChecker([
            UserRole.STUDENT,
            UserRole.ADMIN
        ]))]
) -> User:
    """
    Dependency to ensure the user belongs to any of the standard application roles.

    This acts as a shorthand alias that permits access to students and
    administrators. It permits access only if the authenticated user holds either
    the STUDENT or ADMIN role, effectively blocking teacher accounts.

    Args:
        user (User): The authenticated user validated by the RoleChecker.

    Returns:
        User: The authenticated user's record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is active but does not match any
              of the defined system roles.
    """
    return user


def require_student_teacher_or_admin(
        user: Annotated[User, Depends(RoleChecker([
            UserRole.STUDENT,
            UserRole.TEACHER,
            UserRole.ADMIN
        ]))]
) -> User:
    """
    Dependency to ensure the user belongs to any of the standard application roles.

    This acts as a shorthand alias that permits access to students, teachers,
    and administrators. While it functionally mirrors `get_current_active_user`,
    it explicitly documents that all core roles are authorized for the endpoint.

    Args:
        user (User): The authenticated user validated by the RoleChecker.

    Returns:
        User: The authenticated user's record.

    Raises:
        HTTPException:
            - 401 (Unauthorized): If the token is missing or invalid.
            - 403 (Forbidden): If the user is active but does not match any
              of the defined system roles.
    """
    return user
