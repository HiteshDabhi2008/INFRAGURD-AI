# InfraGuard-AI — Dashboard & Navigation Enhancements

## 1. Top Navigation Bar Updates (`Header.tsx`)

- **Notification Bell Removal**:
  - The bell icon and red notification badge have been completely removed from the top navigation.
  - The unused `Bell` import and associated state were purged.
  - All early warning and risk detection subsystems throughout the dashboard and risk intelligence pages remain fully active.
- **MoSPI / IPMD National Infrastructure Badge**:
  - Prominently displays the official portal badge with a shield icon.
- **User Profile Quick-Access**:
  - Displays user avatar and name with role subtitle.
  - Clickable action navigates directly to the official profile management page (`/dashboard/profile`).
- **Logout Action**:
  - Dedicated sign-out button with clear icon and tooltip.

---

## 2. Sidebar Navigation Updates (`Sidebar.tsx`)

- Added **User Profile** navigation item (`/dashboard/profile`) with `UserCircle` icon.
- Added **Users & Roles** link under the Administration section for Super Admins.

---

## 3. Project Directory & Details Updates

- **Project Directory (`ProjectList.tsx`)**:
  - Added primary `[ + Add Monthly Update ]` action button at the top of the directory.
  - Opens the `MonthlyProjectUpdateModal` with autocomplete search.
- **Project Intelligence (`ProjectIntelligence.tsx`)**:
  - Added `[ + Add Monthly Update ]` action button in the project header actions.
  - Opens the `MonthlyProjectUpdateModal` pre-filled with the current project's metadata.
  - Upon snapshot submission, automatically refreshes project details, history table, and risk assessments.

