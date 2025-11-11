# Account Settings - Testing Guide

## Quick Start Testing

### Prerequisites
- Django server running at http://127.0.0.1:8000
- Logged in as a staff member with faculty profile

### Test Scenario 1: Update Basic Profile Information

1. **Open Account Settings Modal**
   - Click on your name in the top right
   - Click "Account Settings" in dropdown
   - Modal should appear with your current information pre-filled

2. **Modify First Name**
   - Change first name to a new value
   - Click Save
   - Observe: Modal closes, success message appears
   - Reload page and verify name persists

3. **Modify Last Name**
   - Similar to first name test
   - Verify change persists

4. **Modify Email**
   - Change email to a new valid email
   - Click Save
   - Verify success and persistence

5. **Change Gender**
   - Select different gender from dropdown
   - Click Save
   - Verify change persists

### Test Scenario 2: Password Change

1. **Open Account Settings Modal** (as above)

2. **Try Password Change Without Current Password**
   - Leave "Current password" blank
   - Enter something in "New password"
   - Click Save
   - Expected: Error message "Please enter your current password to set a new password"

3. **Try Wrong Current Password**
   - Enter wrong password in "Current password"
   - Enter valid new password in "New password"
   - Click Save
   - Expected: Error message "Current password is incorrect"

4. **Successful Password Change**
   - Enter correct current password
   - Enter new password (at least 6 characters)
   - Click Save
   - Expected: Success message
   - Logout and try logging back in with new password
   - Verify new password works

5. **Try Short Password**
   - Enter current password
   - Enter password less than 6 characters in "New password"
   - Click Save
   - Expected: Error message "New password must be at least 6 characters long"

### Test Scenario 3: Validation

1. **Empty Required Fields**
   - Clear first name field
   - Click Save
   - Expected: Error "Please fill in all required fields"

2. **Invalid Email**
   - Enter invalid email format (e.g., "notanemail")
   - Click Save
   - Expected: Error "Invalid email format"

3. **Duplicate Email**
   - Try to save with another staff member's email
   - Click Save
   - Expected: Error "This email is already in use"

### Test Scenario 4: UI Functionality

1. **Cancel Button**
   - Open modal
   - Make changes
   - Click Cancel
   - Expected: Modal closes, changes not saved

2. **Password Visibility Toggle**
   - Open modal
   - Click eye icon on password field
   - Expected: Password becomes visible
   - Click again
   - Expected: Password hidden again

3. **Upload Picture Button** (Future Feature)
   - Click "Upload new picture"
   - Currently opens file selector (functionality coming soon)

### Test Scenario 5: Form Data Persistence

1. **Partial Update**
   - Change only first name
   - Click Save
   - Expected: Only first name updated, other fields unchanged

2. **Multiple Changes**
   - Change first name, last name, and email
   - Click Save
   - Expected: All three changes saved

3. **Password Change with Other Updates**
   - Change name, email, AND password all together
   - Click Save
   - Expected: All changes saved
   - Logout and login with new credentials
   - Verify all changes persisted

## Browser Developer Tools Testing

### Console Debugging

1. Open Browser DevTools (F12)
2. Go to Console tab
3. Open Account Settings modal
4. Click Save button
5. Observe console output:
   - "Save button clicked!" message
   - "Form data: {firstName, lastName, email, ...}" with values
   - "Response from server:" with success/error response

### Network Debugging

1. Open Browser DevTools (F12)
2. Go to Network tab
3. Open Account Settings modal
4. Click Save button
5. Observe POST request to `/staff/account/save/`
   - Status: 200 (success) or 400 (validation error)
   - Response preview shows JSON response
   - Request payload shows submitted form data

## Expected Results Summary

| Test Case | Expected Outcome |
|-----------|------------------|
| Update name | Changes saved, persist after reload |
| Update email | Changes saved, duplicate prevented |
| Change gender | Selection saved correctly |
| Change password | Old password stops working, new password works |
| Empty fields | Error message shown |
| Invalid email | Validation error shown |
| Duplicate email | Conflict error shown |
| Short password | Password requirement error shown |
| Password without current | Requirement error shown |
| Wrong current password | Authentication error shown |
| Eye toggle | Password visibility toggles |
| Cancel button | Modal closes, no changes saved |

## Troubleshooting

### If Save button doesn't work:
- Check browser console (F12) for JavaScript errors
- Verify form fields are not empty
- Check Network tab to see if request is being sent
- Check server logs for errors

### If changes don't persist:
- Check server logs for save errors
- Verify database connection is working
- Try logging out and back in

### If email validation fails:
- Ensure email format is valid (contains @)
- Check if email is already used by another faculty member
- Verify no duplicate in database

### If password change fails:
- Ensure correct current password entered
- Verify new password is at least 6 characters
- Check server logs for authentication errors

## Expected HTTP Responses

### Success (200):
```json
{
    "success": true,
    "message": "Account settings saved successfully"
}
```

### Validation Error (400):
```json
{
    "success": false,
    "errors": ["First name is required", "Email is already in use"]
}
```

### Not Found (404):
```json
{
    "success": false,
    "error": "Faculty profile not found"
}
```

### Server Error (500):
```json
{
    "success": false,
    "errors": ["Error saving account settings: [details]"]
}
```
