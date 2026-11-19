## PYTHON PROJECT

## Community Waste Reporting System

A web-based platform for reporting waste problems

and tracking cleanup progress

## REPORT • REVIEW • TRACK • RESOLVE

Student name: ______________________________

Class / Section: ______________________________

Lecturer: _____________________________________

Submission date: _____________________________


## 1. Project Overview

The Community Waste Reporting System is a Python-based web application that allows residents to report improperly discarded waste in their neighborhoods. Residents can submit a report with a description, category, location, and optional photo. An administrator reviews reports and updates their status as the issue moves from pending to in progress and finally resolved.

The project aims to make waste reports easier to submit, organize, and track. It is intended as an academic prototype; it does not automatically dispatch municipal cleanup teams or guarantee that a reported issue will be resolved.

## 2. Problem Statement

Improperly discarded rubbish, plastic waste, and overflowing waste containers can reduce the cleanliness of public spaces. Residents may lack a convenient way to report these issues, while administrators may have difficulty organizing reports, prioritizing work, and communicating progress. A centralized system can help record each issue and provide a transparent status history.

## 3. Project Aim and Objectives

Aim: To design and implement a web-based system for reporting community waste problems and monitoring cleanup progress.

- Provide a simple form for residents to submit waste reports.

- Store report details, categories, locations, and optional photos.

- Allow administrators to review, filter, and manage submitted reports.

- Track report status changes and record who made each change.

- Display summary statistics to help administrators understand report volume and progress.

- Apply basic security measures to protect accounts and uploaded files.

## 4. Target Users and Roles

| Role Responsibilities Permissions |
| --- |
| Submit and track personal waste Create reports; view own reports and Resident reports. their status. Review reports and coordinate status View all reports; update status; manage Administrator updates. categories; view dashboard. |

## 5. Functional Requirements

| ID Requirement Description |
| --- |
| Residents can create an account and FR-01 User registration and login sign in securely. A resident can submit a title, FR-02 Create waste report description, category, and location. A resident can attach a photo of the FR-03 Optional photo upload reported waste. FR-04 View report status Residents can see the current status of |


| ID Requirement Description |
| --- |
| their own reports. Administrators can view, search, and FR-05 Manage reports filter all reports. Administrators can set a report to FR-06 Update status Pending, In Progress, or Resolved. The system records status changes, the FR-07 Status history actor, timestamp, and optional note. Administrators can see totals by status FR-08 Dashboard and category. Administrators can add or edit waste FR-09 Manage categories categories. The system validates input and checks FR-10 Validation and access control role permissions. |

## 6. Non-Functional Requirements

- Usability: Forms and navigation should be clear for users with basic computer skills.

- Security: Passwords must be hashed; administrator-only pages must require authorization.

- Reliability: Invalid input should produce helpful errors without corrupting stored data.

- Maintainability: Organize code into routes, models, templates, and configuration.

- Privacy: Avoid exposing residents' personal details or exact location information unnecessarily.

- Performance: The prototype should respond quickly for a modest class demonstration dataset.

## 7. Recommended Technology Stack

| Component Technology / Purpose |
| --- |
| Language Python 3 Web framework Flask — lightweight routing and request handling Frontend HTML, CSS, Bootstrap Database SQLite for a simple local assignment ORM Flask-SQLAlchemy for database models and queries Forms / validation Flask-WTF and server-side validation Charts Chart.js for dashboard statistics (optional) Image handling Flask file uploads with file type, size, and filename checks |

## 8. Database Design

The proposed database contains four core tables. The following fields are a starting design and can be adjusted during implementation.

## users

| Field Description |
| --- |
| id Integer, primary key full_name String, required email String, required, unique |


| Field Description |
| --- |
| password_hash String, required role String, e.g. resident or admin created_at DateTime |

## categories

| Field Description |
| --- |
| id Integer, primary key name String, required, unique description String, optional |

## waste_reports

| Field Description |
| --- |
| id Integer, primary key user_id Foreign key → users.id category_id Foreign key → categories.id title String, required description Text, required location_text String, required latitude / longitude Optional coordinates photo_path String, optional status Pending / In Progress / Resolved created_at / updated_at DateTime |

## status_history

| Field Description |
| --- |
| id Integer, primary key report_id Foreign key → waste_reports.id changed_by Foreign key → users.id old_status / new_status Status values note String, optional changed_at DateTime |

## 9. Main Workflow

- 1. Resident registers or signs in.

- 2. Resident opens the report form and enters the waste description, category, and location.

- 3. The system validates the submitted data and stores the report with Pending status.

- 4. Administrator reviews the report and changes its status when work begins.

- 5. The system records the status change in status_history.

- 6. Administrator marks the report Resolved after cleanup is reported as complete.

- 7. Resident checks the report page to see the latest status.


## 10. Suggested Pages

- Public home page: Project introduction, reporting guidance, and basic statistics.

- Register / Login: Account creation and authentication.

- Submit report: Waste report form with optional photo.

- My reports: Resident's report list and status.

- Report details: Description, location, photo, and status history.

- Admin dashboard: Summary cards and charts.

- Admin report management: Search, filters, report details, and status update controls.

- Category management: Create and edit waste categories.

## 11. Security and Validation

- Store password hashes, never plaintext passwords.

- Use role-based authorization on every administrator route.

- Validate required fields and limit description lengths.

- Restrict uploads to permitted image formats, enforce a size limit, and generate safe server-side filenames.

- Do not trust a filename extension alone; verify uploaded content where practical.

- Prevent residents from viewing or modifying other residents' private reports unless explicitly allowed.

- Use CSRF protection for form submissions and keep secrets out of source control.

## 12. Testing Plan

| Test Expected result |
| --- |
| Report submission Valid report saves successfully with Pending status. Required fields Missing title, description, category, or location is rejected. Valid image is accepted; disallowed type or oversized file is Photo upload rejected. Resident cannot open admin pages or update another user's Authorization report. Admin update changes current status and creates a history Status updates record. Dashboard counts Displayed totals match records in the database. Login Valid credentials work and invalid credentials are rejected. |

## 13. Development Schedule

| Step Deliverable |
| --- |
| Step 1 Project setup, database, and models Step 2 Authentication and role permissions Step 3 Create reports and safely upload photos Step 4 Administrator report management and status history Step 5 Dashboard, filters, and charts Step 6 Testing, bug fixes, screenshots, and presentation |


## 14. Future Enhancements

- Interactive map showing report locations.

- Email or in-app notifications when report status changes.

- Duplicate-report detection for nearby issues.

- Report priority levels and administrative assignment.

- Export reports to CSV or PDF.

- Khmer and English interface support.

## 15. Expected Outcome

The expected outcome is a working Python web application that demonstrates how community waste issues can be submitted, stored, reviewed, and tracked through a clear workflow. The prototype should include role-based access, a relational database, report status history, and a basic administrative dashboard.

## 16. Conclusion

The Community Waste Reporting System is a manageable and socially relevant Python assignment. Its modular design allows the student to complete the essential reporting workflow first and add features such as maps, notifications, and bilingual support only when time permits.
