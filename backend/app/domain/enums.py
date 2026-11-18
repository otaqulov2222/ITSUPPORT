from enum import StrEnum


class RoleCode(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    NETWORK_ADMIN = "NETWORK_ADMIN"
    IT_SUPPORT = "IT_SUPPORT"
    REGIONAL_ADMIN = "REGIONAL_ADMIN"
    BRANCH_MANAGER = "BRANCH_MANAGER"
    PHARMACIST = "PHARMACIST"
    AUDITOR = "AUDITOR"


class ScopeType(StrEnum):
    GLOBAL = "GLOBAL"
    REGION = "REGION"
    BRANCH = "BRANCH"


class PermissionCode(StrEnum):
    BRANCHES_READ = "branches.read"
    BRANCHES_WRITE = "branches.write"
    EMPLOYEES_READ = "employees.read"
    EMPLOYEES_WRITE = "employees.write"
    USERS_READ = "users.read"
    USERS_WRITE = "users.write"
    AUDIT_READ = "audit.read"
    TICKETS_READ = "tickets.read"
    TICKETS_ASSIGN = "tickets.assign"
    CONVERSATIONS_READ = "conversations.read"
    CONVERSATIONS_REPLY = "conversations.reply"
    AUTOMATION_APPROVE = "automation.approve"
    SETTINGS_WRITE = "settings.write"
