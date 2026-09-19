# InfraGuard-AI — User Profile & Authority Management

## 1. Overview & Architecture

The **User Profile & Authority Management System** provides secure authentication, credential inspection, contact management, and administrative role assignment for Government of India officers participating in the InfraGuard-AI platform.

Each officer is assigned a unique, immutable **Government ID** (e.g., `GOV-MOSPI-2026-0001`), which is masked in client interfaces as `GOV-****0001` for security and privacy.

---

## 2. Profile Components & Security Rules

### A. Personal & Official Details
- **Government ID**: Permanent official identifier. Read-only and cryptographically bound to the account.
- **Official Email**: Primary authentication identity. Immutable by the user.
- **Role / Authority Type**: Assigned by Super Admin or MoSPI IPMD Admin. Immutable by regular users.
- **Full Name**: Editable by the user.
- **Mobile Number**: Contact number for official project alerts. Editable by the user.
- **Designation**: Official title (e.g., *Chief Engineer*, *Director (Projects)*). Editable by the user.
- **Department**: Administrative wing (e.g., *IPMD*, *Highways Section*). Editable by the user.
- **Ministry / Organization**: Parent ministry. Editable by the user.
- **Implementing Agency**: Associated PSU / statutory body (e.g., *NHAI*, *RVNL*, *AAI*). Editable by the user.
- **State / Jurisdiction**: Territorial scope. Editable by the user.

### B. In-Page Password Management
- Allows changing credentials securely directly on `/dashboard/profile`.
- Validates current password using bcrypt hashing before accepting updates.
- Requires minimum 8-character new password with confirmation match.

### C. Super Admin User Directory & Security Controls
- **Accessible By**: `SUPER_ADMIN` and `MOSPI_IPMD_ADMIN`.
- **Searchable By**: Government ID, Full Name, Email, or Agency.
- **Role Filter**: Filter users by specific authority tiers.
- **Role Management Modal**: Assign authority tiers, toggle active status, and manage verification badges.
- **Tamper-Evident Audit Trail**: Live view of security events (login, profile changes, admin role updates, project data submissions).

---

## 3. Endpoints

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/auth/me` | Fetch authenticated officer profile with masked Gov ID | Authenticated |
| `PUT` | `/api/auth/profile` | Update personal/contact profile details | Verified User |
| `POST` | `/api/auth/change-password` | Change account password | Authenticated |
| `GET` | `/api/admin/users` | List and search registered officers | Super Admin |
| `PUT` | `/api/admin/users/{id}` | Update officer role, status, and verification | Super Admin |
| `GET` | `/api/admin/audit-logs` | Retrieve chronological security audit logs | Super Admin |

