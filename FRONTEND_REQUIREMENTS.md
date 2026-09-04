# FRONTEND_REQUIREMENTS.md
# Landlord–Tenant Direct Connect Platform
## Frontend Requirements, Visual Design & Branding Brief

**Document status:** Authoritative frontend implementation specification  
**Audience:** OpenCode implementation agent and project developer  
**Backend:** Django 6.1 + Django REST Framework  
**Database:** PostgreSQL 18  
**ML:** Weighted K-Nearest Neighbour (Weighted KNN)  
**Frontend approach:** Django Templates + HTML5 + CSS3 + JavaScript  
**API base:** `/api/v1/`

---

# 1. Purpose

Build a complete, responsive, professional frontend for the Landlord–Tenant Direct Connect Platform.

The frontend MUST be implemented against the existing Django backend, API endpoints, serializers, permissions, authentication flow, database models and Weighted KNN recommendation services.

The frontend is not a separate product. It is the presentation layer of the existing system.

Do not invent backend endpoints or database fields. Inspect the actual repository before implementation and use the implemented API contracts.

---

# 2. Authoritative Documents

Before making frontend changes, read completely:

1. `AGENTS.md`
2. `SYSTEM_REQUIREMENTS.md`
3. `TECH_STACK_AND_IMPLEMENTATION_PLAN.md`
4. `FRONTEND_REQUIREMENTS.md`

If these documents conflict, follow the priority defined by `AGENTS.md`; otherwise preserve the system requirements and existing backend implementation.

The frontend MUST remain consistent with:

- Agile development methodology
- OOAD as the system design approach
- Django/Python implementation
- PostgreSQL database
- Django REST Framework APIs
- JWT authentication
- Tenant/Landlord/Admin roles
- Weighted KNN recommendation algorithm
- Existing security and validation rules

---

# 3. Non-Negotiable Frontend Rules

1. Do not replace Django Templates with React, Vue, Angular, Next.js or another frontend framework unless explicitly authorized.
2. Do not create a second backend.
3. Do not duplicate business logic that belongs in Django.
4. Do not bypass API permissions.
5. Do not expose JWT secrets, database credentials, Django secrets or environment variables in frontend source.
6. Do not hard-code authentication credentials.
7. Do not invent API endpoints.
8. Inspect existing URLs, serializers, views and response structures before connecting UI components.
9. Do not change backend models merely to make the frontend easier.
10. Do not change Weighted KNN into another recommendation algorithm.
11. Do not introduce payment processing or unrelated property-management features.
12. All pages must work on desktop, tablet and mobile.
13. All forms must have validation and clear error states.
14. All asynchronous operations must have loading, success and failure states.
15. Empty states must be intentionally designed.
16. Navigation must change according to authenticated role.
17. Admin functionality must never be exposed to tenants or landlords.
18. Landlords must only access functionality permitted by backend authorization.
19. Tenants must only access tenant functionality.
20. Preserve accessibility, semantic HTML, keyboard navigation and readable contrast.

---

# 4. Product Identity

## 4.1 Product concept

The platform connects prospective tenants directly with landlords through verified apartment listings, structured property information, preference-based search, Weighted KNN recommendations and direct messaging.

The visual identity should communicate:

- Trust
- Transparency
- Modern housing technology
- Simplicity
- Local relevance
- Professionalism
- Safety
- Direct connection
- Intelligent recommendations

The design should feel like a serious Nigerian PropTech platform, not a generic school-project dashboard.

---

# 5. Visual Design / Branding Brief

## 5.1 Overall visual direction

Create a distinctive visual language inspired by modern property-search platforms, but do NOT clone any existing site's branding, layout, logo, icons, colors or copyrighted assets.

Design direction:

**Modern African PropTech + premium property marketplace + trustworthy SaaS dashboard.**

Use:

- Clean layouts
- Large property photography
- Generous whitespace
- Strong visual hierarchy
- Rounded but restrained cards
- Professional typography
- Clear calls to action
- Subtle shadows
- Soft borders
- Consistent iconography
- Responsive image galleries
- Clear status badges
- Modern dashboard cards
- Polished empty/loading/error states

Avoid:

- Excessive gradients
- Overly bright colors
- Cartoonish graphics
- Excessive animation
- Cluttered dashboards
- Tiny text
- Excessive rounded/pill UI
- Copying Airbnb's distinctive branding
- Copying PropertyPro's branding
- Generic Bootstrap-looking pages without customization

---

# 6. Recommended Brand System

The implementation agent may refine exact values while preserving the visual direction.

## 6.1 Primary brand

Use a sophisticated deep teal/blue-green family as the primary identity to communicate trust and technology.

Suggested design tokens:

- `--color-primary: #0F766E`
- `--color-primary-dark: #115E59`
- `--color-primary-light: #CCFBF1`
- `--color-accent: #F59E0B`
- `--color-background: #F8FAFC`
- `--color-surface: #FFFFFF`
- `--color-text: #0F172A`
- `--color-text-muted: #64748B`
- `--color-border: #E2E8F0`
- `--color-success: #16A34A`
- `--color-warning: #D97706`
- `--color-danger: #DC2626`

These are design guidance, not backend requirements.

## 6.2 Typography

Prefer a modern sans-serif stack such as:

- Inter
- Manrope
- system sans-serif fallback

Use clear hierarchy:

- Large hero heading
- Medium section headings
- Compact card headings
- Readable body text
- Clearly distinguish metadata from primary information

Do not use decorative fonts for functional UI.

---

# 7. Visual Reference Websites

These are inspiration/reference sources only. Do not reproduce their branding or copyrighted assets.

### Airbnb
Use for:
- property imagery
- search-first experience
- listing cards
- visual hierarchy
- clean property details

Reference:
https://www.airbnb.com/

Design examples:
https://www.airbnb.com/stays/design

### PropertyPro Nigeria
Use for:
- Nigerian property-search context
- rental/property categories
- search/filter concepts
- Nigerian currency and property presentation

Reference:
https://propertypro.ng/

Login/register flows can also be inspected for general UX patterns:
https://propertypro.ng/login
https://propertypro.ng/register

### Reference rule

The final platform must be visually ORIGINAL.

The agent may study information architecture and UX patterns from these references, but must create a new brand identity, layout system, components, colors, typography and interaction design.

Do not copy logos, trademarks, proprietary illustrations or distinctive trade dress.

---

# 8. Frontend Information Architecture

Implement role-aware navigation.

## Public

- Home
- Browse Apartments
- Apartment Details
- Login
- Register
- About/How It Works
- Contact/Help where supported

## Tenant

- Tenant Dashboard
- Apartment Search
- Recommendations
- Saved/Preferred properties where supported by backend
- My Preferences
- Messages
- Profile
- Logout

## Landlord

- Landlord Dashboard
- My Apartments
- Add Apartment
- Edit Apartment
- Apartment Media
- Verification
- Messages
- Profile
- Logout

## Administrator

- Admin Dashboard
- Users
- Apartments
- Verification Requests
- Messages/Monitoring where permitted
- System statistics
- Profile
- Logout

Do not display unavailable features as functional controls.

---

# 9. Home Page

The homepage should immediately explain the platform.

Required sections:

1. Navigation bar
2. Hero section
3. Primary apartment search
4. Search filters
5. Featured/recent apartments
6. How the platform works
7. Tenant benefits
8. Landlord benefits
9. Verification/trust section
10. Intelligent recommendation explanation
11. Direct landlord-to-tenant communication explanation
12. Call-to-action
13. Footer

Hero message should communicate the central proposition:

**Find the right home. Connect directly with the landlord.**

Do not use misleading claims such as guaranteed fraud elimination or legal property verification.

---

# 10. Authentication UI

Implement:

- Login
- Registration
- Logout
- Authentication errors
- Session/token handling consistent with backend
- Role-aware redirect
- Unauthorized state
- Forbidden state

Registration must clearly allow the supported user roles.

Never display or expose passwords.

---

# 11. Tenant Experience

## Tenant dashboard

Show:

- Welcome message
- Search shortcut
- Recommended apartments
- Recent listings
- Preference completion status
- Recent conversations
- Profile summary

## Preference page

Provide structured controls for all backend-supported preference fields.

Examples where supported:

- Location
- Property type
- Minimum/maximum rent
- Bedrooms
- Amenities
- Other supported apartment attributes

The UI must reflect the actual serializer/model fields.

## Recommendations

Present:

- Recommended apartment
- Match/relevance score where returned by backend
- Important matching attributes
- Property image
- Rent
- Location
- Property type
- Availability
- View details
- Contact landlord

Do not calculate a different recommendation score in JavaScript.

The backend Weighted KNN implementation remains the authoritative recommendation engine.

---

# 12. Landlord Experience

Dashboard should show:

- Listing count
- Available apartments
- Verification status
- Recent messages
- Listing management shortcuts

Apartment management:

- Create
- View
- Edit
- Delete where authorized
- Upload/manage images
- Availability
- Structured property information

Use clear verification badges:

- Pending
- Approved
- Rejected

Rejection remarks must be visible where returned by the backend.

---

# 13. Administrator Experience

The admin interface must provide clear operational views for:

- Users
- Apartments
- Verification requests
- Verification status
- Approval/rejection workflow
- System-level summaries where supported

Use tables on desktop and responsive cards on mobile.

Admin actions must require confirmation where destructive or consequential.

---

# 14. Apartment Search UI

Search must support the backend's actual capabilities.

Recommended layout:

Desktop:
- Search/filter panel
- Results grid/list
- Sort controls
- Pagination

Mobile:
- Search bar
- Filter button/drawer
- Results list
- Compact sorting control

Apartment cards should display:

- Main image
- Property type
- Location
- Rent
- Bedrooms
- Availability
- Verification status where appropriate
- Recommendation/match information where available
- View details CTA

---

# 15. Apartment Details Page

Use a high-quality property presentation.

Required where backend data exists:

- Image gallery
- Property title
- Description
- Location
- Rent
- Property type
- Bedrooms
- Bathrooms
- Amenities
- Availability
- Verification information
- Landlord information permitted by backend
- Contact/message landlord CTA

Do not expose private landlord information that the API does not authorize.

---

# 16. Messaging UI

Implement the existing messaging API.

Required UI:

- Conversation list
- Conversation detail
- Message history
- Message composer
- Sent/read status where available
- Empty state
- Loading state
- Error state

Use a clean chat layout.

Do not create a WebSocket implementation unless the backend actually supports it.

---

# 17. Verification UI

Landlords:

- Verification submission form
- Submission status
- Pending state
- Approved state
- Rejected state
- Remarks where available

Administrators:

- Verification request list
- Filter by status
- Review details
- Approve
- Reject with remarks

Never imply that the platform performs legal title verification unless explicitly implemented.

---

# 18. Reusable Component System

Create reusable Django template components/partials for:

- Navbar
- Footer
- Buttons
- Form fields
- Cards
- Apartment cards
- Status badges
- Alerts
- Modals
- Pagination
- Search controls
- Filter controls
- Loading skeletons
- Empty states
- Error states
- Image gallery
- Dashboard statistic cards
- Message bubbles
- Breadcrumbs

Avoid duplicating HTML unnecessarily.

---

# 19. Responsive Requirements

Minimum target widths:

- Mobile: 320px+
- Tablet: 768px+
- Desktop: 1024px+
- Large desktop: 1440px+

Requirements:

- No horizontal overflow
- Navigation adapts to mobile
- Cards resize cleanly
- Forms become single-column on small screens
- Tables become cards or horizontally scrollable where necessary
- Images remain correctly cropped
- Touch targets are sufficiently large
- Modals remain usable on mobile

---

# 20. Accessibility

Use:

- Semantic HTML
- Labels for form fields
- Keyboard navigation
- Visible focus states
- Appropriate ARIA attributes where necessary
- Meaningful alt text
- Sufficient contrast
- Error messages associated with fields
- Accessible modal behavior

Do not communicate important information through color alone.

---

# 21. Frontend State Requirements

Every API-driven component must consider:

1. Initial state
2. Loading state
3. Success state
4. Empty state
5. Validation error
6. Authentication error
7. Permission error
8. Server error
9. Network failure

Avoid blank screens when an API request fails.

---

# 22. API Integration

Before implementing a page, inspect:

- Django URL configuration
- API URL configuration
- serializers
- views
- permissions
- response formats
- authentication mechanism

Use the actual API.

The frontend must not assume fields that are not returned.

Centralize API calls where practical rather than scattering raw fetch logic throughout templates.

---

# 23. Security

Frontend implementation must:

- Never contain secrets
- Never contain database credentials
- Respect CSRF requirements
- Respect JWT authentication requirements
- Handle expired authentication
- Prevent unsafe HTML injection
- Avoid rendering untrusted content as raw HTML
- Use secure form handling
- Respect backend authorization

Security is enforced by the backend; frontend restrictions are supplementary.

---

# 24. Performance

Use:

- Optimized images
- Lazy loading for non-critical images
- Minimal JavaScript
- Reusable CSS
- Pagination for large result sets
- Efficient API requests
- Avoid unnecessary polling
- Avoid duplicate API calls

Do not introduce a large frontend framework merely for visual effects.

---

# 25. Frontend File Organization

Follow the existing repository architecture.

A suitable Django presentation structure may include:

```text
templates/
    base.html
    public/
    accounts/
    tenant/
    landlord/
    admin/
    apartments/
    messaging/
    verification/
    components/

static/
    css/
    js/
    images/
```

Adapt this to the actual repository rather than creating conflicting structures.

---

# 26. Required Pages / Screens

At minimum, verify the existence and functionality of:

### Public
- Home
- Login
- Registration
- Apartment search
- Apartment details

### Tenant
- Dashboard
- Preferences
- Recommendations
- Messages
- Profile

### Landlord
- Dashboard
- Apartment list
- Create apartment
- Edit apartment
- Apartment details
- Verification
- Messages
- Profile

### Admin
- Dashboard
- User management
- Apartment management
- Verification management
- Messages/monitoring where supported

---

# 27. Branding Assets

Create a simple original text/logo treatment for the platform.

Do not copy third-party logos.

Use an original platform name treatment such as:

**Landlord–Tenant Direct Connect**

Possible short brand mark:

**LT Direct**

The implementation may choose a final name only if consistent with the authoritative system documents.

Use original icons from an appropriate open-source icon library if the project already permits one. Do not download copyrighted icon packs without permission.

---

# 28. Photography / Property Images

Use realistic apartment/property imagery in development/demo data.

Do not hotlink copyrighted third-party images in production.

Prefer:

- project-owned images
- properly licensed images
- generated placeholder property imagery
- local development assets

Use consistent image aspect ratios.

---

# 29. UX Quality Standard

The final result must look like a real production-oriented PropTech application.

It must NOT look like:

- a raw Django admin site
- a collection of unstyled forms
- a school-project prototype
- a default Bootstrap template
- disconnected pages
- an API testing interface

The visual experience must be coherent from homepage through authentication, search, apartment details, dashboards, messaging and verification.

---

# 30. Frontend Implementation Workflow

Before implementation:

1. Read all authoritative documents.
2. Inspect the current Django project.
3. Inspect existing templates.
4. Inspect static files.
5. Inspect URL routes.
6. Inspect API endpoints.
7. Inspect serializers.
8. Inspect permissions.
9. Inspect authentication.
10. Inspect existing test expectations.
11. Map backend features to frontend screens.
12. Identify missing frontend screens.

Then implement in controlled phases.

Suggested order:

### Phase F1 — Design Foundation
- base template
- CSS tokens
- typography
- navigation
- footer
- reusable components

### Phase F2 — Public Experience
- homepage
- search
- apartment cards
- apartment details
- authentication

### Phase F3 — Tenant
- dashboard
- preferences
- recommendations
- messaging
- profile

### Phase F4 — Landlord
- dashboard
- apartment management
- media
- verification
- messaging
- profile

### Phase F5 — Administrator
- dashboard
- users
- apartments
- verification
- monitoring

### Phase F6 — Responsive & Accessibility
- mobile
- tablet
- desktop
- accessibility
- error states

### Phase F7 — Integration & QA
- API integration
- authentication testing
- role testing
- responsive testing
- regression testing
- final visual review

---

# 31. Definition of Done

Frontend is complete only when:

- All required role-based pages exist.
- Pages are connected to the actual backend.
- Authentication works.
- Tenant flows work.
- Landlord flows work.
- Admin flows work.
- Apartment search works.
- Filtering works.
- Preferences work.
- Recommendations are displayed from the backend.
- Messaging works.
- Verification workflows work.
- Forms validate correctly.
- Loading/empty/error states exist.
- Responsive layouts work.
- No major horizontal overflow exists.
- No secrets are exposed.
- Browser console has no avoidable errors.
- Django checks pass.
- Relevant automated tests pass.
- Existing backend functionality remains intact.
- No unauthorized backend redesign was introduced.
- The visual design is consistent and original.

---

# 32. Visual QA Checklist

Before declaring completion, inspect at:

- 320px
- 375px
- 768px
- 1024px
- 1440px

Check:

- Navigation
- Homepage
- Search
- Filters
- Apartment cards
- Apartment details
- Login
- Registration
- Tenant dashboard
- Landlord dashboard
- Admin dashboard
- Preferences
- Recommendations
- Messaging
- Verification
- Forms
- Modals
- Alerts
- Empty states
- Error states

---

# 33. Important Instruction to OpenCode

Do not simply build pages because they appear in this document.

First inspect the actual backend and map each frontend screen to the corresponding implemented API.

For every frontend feature, record:

| Frontend Feature | Backend Endpoint | Serializer | Permission | Response/Data |
|---|---|---|---|---|
| Login | Inspect repository | Inspect repository | Public | Actual response |
| Apartment search | Inspect repository | Inspect repository | Actual permission | Actual response |
| Preferences | Inspect repository | Inspect repository | Tenant | Actual response |
| Recommendations | Inspect repository | Inspect repository | Tenant | Actual response |
| Messaging | Inspect repository | Inspect repository | Participant/Admin | Actual response |
| Verification | Inspect repository | Inspect repository | Landlord/Admin | Actual response |

Do not invent values for this table. Populate it from the repository.

---

# 34. Final Design Principle

The application should feel like:

**A trustworthy Nigerian property platform that combines the visual quality of a modern property marketplace with the clarity of a professional SaaS dashboard and the intelligence of a recommendation system.**

The result must be original, responsive, accessible, functional and fully aligned with the existing Django/PostgreSQL/DRF/Weighted-KNN architecture.

---

## Reference Sources

- Airbnb: https://www.airbnb.com/
- Airbnb Design Homes: https://www.airbnb.com/stays/design
- PropertyPro Nigeria: https://propertypro.ng/
- PropertyPro Login: https://propertypro.ng/login
- PropertyPro Registration: https://propertypro.ng/register

These references are for UX inspiration only. Do not copy their branding, trademarks, logos, colors, proprietary assets or distinctive visual identity.
