# Account Settings Backend Implementation

## Overview
Implemented a complete backend handler for staff members to save their account settings, including profile updates and password changes.

## Components Implemented

### 1. Backend URL Route
**File**: `hello/urls.py`
- **Route**: `path('staff/account/save/', views.save_account_settings, name='save_account_settings')`
- **Purpose**: Endpoint that receives account settings updates from the frontend

### 2. Backend View Handler
**File**: `hello/views.py` (Lines 2501-2610)
- **Function**: `save_account_settings(request)`
- **Authentication**: Requires login (`@login_required`)
- **HTTP Method**: POST only

#### What It Does:
1. **Validates Input**:
   - First Name, Last Name, Email (required)
   - Gender selection (M/F)
   - Password validation if changing password

2. **Security Checks**:
   - Verifies current password before allowing password change
   - Validates password length (minimum 6 characters)
   - Prevents duplicate emails
   - Basic email format validation

3. **Database Updates**:
   - Updates Faculty model (first_name, last_name, email, gender)
   - Updates User model (first_name, last_name, email)
   - Updates password using Django's secure `set_password()` method
   - Returns appropriate success/error messages

### 3. Frontend Form Submission
**File**: `hello/templates/hello/staff_dashboard.html`
- **Added**: CSRF token to account form (`{% csrf_token %}`)
- **Updated**: Save button click handler to:
  - Collect all form data (names, email, gender, passwords)
  - Validate required fields before submission
  - Create FormData object for file upload support
  - Send POST request to `/staff/account/save/`
  - Handle success/error responses from backend

### 4. Frontend-Backend Communication
**Protocol**: AJAX/Fetch API with JSON responses

#### Request Format:
```javascript
POST /staff/account/save/
Headers: {
    'X-CSRFToken': '<csrf_token>'
}
Body (FormData): {
    firstName: string,
    lastName: string,
    email: string,
    gender: 'M' | 'F',
    currentPassword: string (optional),
    newPassword: string (optional),
    profilePicture: File (optional)
}
```

#### Response Format:
```json
// Success Response
{
    "success": true,
    "message": "Account settings saved successfully"
}

// Error Response
{
    "success": false,
    "errors": ["Error message 1", "Error message 2"]
}
```

## Features

### Working Features ✅
1. **Profile Update**
   - Update first name, last name, email
   - Change gender selection
   - All changes persist to database

2. **Password Management**
   - Change password securely
   - Requires current password verification
   - Uses Django's secure password hashing

3. **Form Validation**
   - Client-side validation (required fields)
   - Server-side validation (email uniqueness, password strength)
   - Detailed error messages returned to user

4. **Security**
   - CSRF token protection
   - Login requirement
   - Current password verification for password changes
   - Secure password hashing with `set_password()`

### Future Features 🚀
1. **Profile Picture Upload**
   - Add `ImageField` to Faculty model
   - Store images in media directory
   - Backend handler prepared but commented for future implementation

2. **Avatar Generation**
   - Generate avatar from user initials
   - Display profile picture in dashboard header

## Error Handling

The backend returns detailed error messages for:
- Missing required fields
- Invalid email format
- Duplicate email addresses
- Incorrect current password
- Password too short
- Faculty profile not found
- Server errors during save

## Testing Checklist

### Manual Testing Steps:
1. Log in to staff dashboard
2. Click "Account Settings" in dropdown
3. Try modifying:
   - [ ] First name
   - [ ] Last name
   - [ ] Email
   - [ ] Gender
4. Try password change:
   - [ ] Without current password (should error)
   - [ ] With wrong current password (should error)
   - [ ] With correct current password (should succeed)
5. Verify changes persist after logout/login

### Edge Cases:
- [ ] Leave required fields empty (should error)
- [ ] Use invalid email format (should error)
- [ ] Try duplicate email (should error)
- [ ] Set very short password (should error)

## Database Changes
**No migrations required** - Uses existing Faculty and User models:
- Faculty: `first_name`, `last_name`, `email`, `gender`
- User: `first_name`, `last_name`, `email`, `password`

## Files Modified
1. `hello/urls.py` - Added new route
2. `hello/views.py` - Added `save_account_settings()` view
3. `hello/templates/hello/staff_dashboard.html`:
   - Added `{% csrf_token %}` to form
   - Updated Save button handler with fetch API call

## Security Considerations
✅ CSRF protection via middleware and X-CSRFToken header
✅ Password verified before change allowed
✅ Passwords hashed using Django's secure method
✅ Login required for all operations
✅ Input validation on server-side
✅ Email uniqueness enforcement

## API Documentation

### POST /staff/account/save/
Save account settings for logged-in staff member.

**Required**: Login session

**Parameters** (FormData):
- `firstName` (string, required): First name
- `lastName` (string, required): Last name
- `email` (string, required): Email address
- `gender` (string, optional): 'M' or 'F'
- `currentPassword` (string, optional): Current password (required if setting new password)
- `newPassword` (string, optional): New password (minimum 6 characters)
- `profilePicture` (file, optional): Profile picture file

**Success Response** (200):
```json
{
    "success": true,
    "message": "Account settings saved successfully"
}
```

**Error Response** (400/404/500):
```json
{
    "success": false,
    "errors": ["Error description"]
}
```

## Notes
- Profile picture upload prepared for future implementation with ImageField
- All changes log to console for debugging
- Django messages framework used for server-side notifications
- Uses secure password verification with `check_password()`
