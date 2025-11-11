# Account Settings - Code Reference

## Backend View Handler

### Location: `hello/views.py` (Lines 2501-2610)

```python
@login_required(login_url='admin_login')
def save_account_settings(request):
    """Handle account settings update for logged-in faculty member"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests are allowed'
        }, status=400)
    
    try:
        # Get the faculty profile for the logged-in user
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    
    # Get form data
    first_name = request.POST.get('firstName', '').strip()
    last_name = request.POST.get('lastName', '').strip()
    email = request.POST.get('email', '').strip()
    gender = request.POST.get('gender', '').strip()
    current_password = request.POST.get('currentPassword', '')
    new_password = request.POST.get('newPassword', '')
    profile_picture = request.FILES.get('profilePicture', None)
    
    # Validation logic here...
    # Database updates here...
    # Returns JSON response
```

### Key Features:
- `@login_required` decorator ensures only authenticated users can access
- `POST` method only - prevents accidental data exposure via GET
- Faculty profile lookup using `request.user`
- `.strip()` on string inputs to remove whitespace
- Comprehensive validation before database updates
- Secure password verification with `check_password()`
- Secure password setting with `set_password()`

### Validation Chain:
1. Check required fields (first_name, last_name, email)
2. Validate email format
3. Check email uniqueness (excluding current faculty)
4. If password change:
   - Verify current password is provided
   - Verify current password is correct
   - Verify new password is at least 6 characters

### Database Updates:
```python
# Update Faculty model
faculty.first_name = first_name
faculty.last_name = last_name
faculty.email = email
faculty.gender = gender
faculty.save()

# Update User model
request.user.first_name = first_name
request.user.last_name = last_name
request.user.email = email
if new_password:
    request.user.set_password(new_password)
request.user.save()
```

## Frontend JavaScript Handler

### Location: `hello/templates/hello/staff_dashboard.html` (Account Settings Modal JavaScript)

```javascript
// Save button click handler
if (saveBtn) {
    saveBtn.addEventListener('click', function(e) {
        console.log('Save button clicked!');
        e.preventDefault();
        e.stopPropagation();
        
        // Get form elements
        const form = document.querySelector('.account-form');
        const textInputs = form.querySelectorAll('input[type="text"]');
        const passwordInputs = form.querySelectorAll('.password-input-wrapper input[type="password"]');
        const genderSelect = form.querySelector('select');
        
        // Extract values
        const firstName = textInputs[0] ? textInputs[0].value.trim() : '';
        const lastName = textInputs[1] ? textInputs[1].value.trim() : '';
        const email = form.querySelector('input[type="email"]') ? form.querySelector('input[type="email"]').value.trim() : '';
        const gender = genderSelect ? genderSelect.value : '';
        const currentPassword = passwordInputs[0] ? passwordInputs[0].value : '';
        const newPassword = passwordInputs[1] ? passwordInputs[1].value : '';
        const profilePicInput = document.getElementById('profilePicInput');
        
        // Client-side validation
        if (!firstName || !lastName || !email) {
            alert('Please fill in all required fields');
            return;
        }
        
        if (newPassword && !currentPassword) {
            alert('Please enter your current password to set a new password');
            return;
        }
        
        // Build FormData for submission
        const formData = new FormData();
        formData.append('firstName', firstName);
        formData.append('lastName', lastName);
        formData.append('email', email);
        formData.append('gender', gender);
        if (currentPassword) formData.append('currentPassword', currentPassword);
        if (newPassword) formData.append('newPassword', newPassword);
        if (profilePicInput.files.length > 0) {
            formData.append('profilePicture', profilePicInput.files[0]);
        }
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        const token = csrfToken ? csrfToken.value : '';
        
        // Send request to backend
        fetch('/staff/account/save/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': token
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response from server:', data);
            if (data.success) {
                alert('Account settings saved successfully!');
                modal.style.display = 'none';
            } else {
                const errorMessage = data.errors ? data.errors.join('\n') : data.error || 'An error occurred';
                alert('Error saving account settings:\n' + errorMessage);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error communicating with server: ' + error.message);
        });
    }, true);
}
```

### Key Features:
- Form element selection using `querySelector` and `querySelectorAll`
- Value extraction with `.trim()` to remove whitespace
- Client-side validation for required fields
- `FormData` object for handling file uploads
- CSRF token retrieval from DOM
- Fetch API for asynchronous request
- Error handling with `.catch()` for network errors
- JSON response parsing and error extraction
- Console logging for debugging

## URL Configuration

### Location: `hello/urls.py`

```python
path('staff/account/save/', views.save_account_settings, name='save_account_settings'),
```

### Usage in Templates:
```django
<!-- In URL patterns or JavaScript -->
{% url 'save_account_settings' %}  <!-- Returns: /staff/account/save/ -->

<!-- In JavaScript (hardcoded) -->
fetch('/staff/account/save/', {...})
```

## Form Structure

### HTML Template

```html
<form class="account-form">
    {% csrf_token %}
    <div class="form-row">
        <div class="form-group">
            <label>First Name</label>
            <input type="text" value="{{ faculty.first_name }}">
        </div>
        <div class="form-group">
            <label>Last Name</label>
            <input type="text" value="{{ faculty.last_name }}">
        </div>
    </div>
    <div class="form-row">
        <div class="form-group">
            <label>Gender</label>
            <select>
                <option value="">Select Gender</option>
                <option value="M" {% if faculty.gender == 'M' %}selected{% endif %}>Male</option>
                <option value="F" {% if faculty.gender == 'F' %}selected{% endif %}>Female</option>
            </select>
        </div>
        <div class="form-group">
            <label>Email</label>
            <input type="email" value="{{ faculty.email }}">
        </div>
    </div>
    <div class="form-row">
        <div class="form-group">
            <label>Current password</label>
            <div class="password-input-wrapper">
                <input type="password" class="password-input">
                <button class="toggle-password">
                    <!-- Eye icon SVG -->
                </button>
            </div>
        </div>
        <div class="form-group">
            <label>New password</label>
            <div class="password-input-wrapper">
                <input type="password" class="password-input">
                <button class="toggle-password">
                    <!-- Eye icon SVG -->
                </button>
            </div>
        </div>
    </div>
</form>

<div class="form-actions">
    <button class="cancel-btn" id="cancelBtn">Cancel</button>
    <button class="save-btn" id="saveBtn">Save</button>
</div>
```

### Important Notes:
- Form includes `{% csrf_token %}` for CSRF protection
- Form uses `class="account-form"` for JavaScript selection
- Input fields use `value="{{ faculty.field }}"` for pre-population
- Password inputs inside `.password-input-wrapper` divs
- Gender select uses conditional `selected` attribute

## Data Flow Diagram

```
User Interface (staff_dashboard.html)
    ↓
    [Save Button Click]
    ↓
JavaScript Handler
    ├─ Extract form values
    ├─ Validate required fields
    └─ Create FormData object
    ↓
Fetch API POST Request
    ├─ URL: /staff/account/save/
    ├─ Headers: X-CSRFToken
    └─ Body: FormData
    ↓
Django Backend (save_account_settings view)
    ├─ Authenticate user
    ├─ Get faculty profile
    ├─ Validate all inputs
    ├─ Check password if changing
    └─ Update database models
    ↓
JSON Response
    ├─ Success: {"success": true, "message": "..."}
    └─ Error: {"success": false, "errors": [...]}
    ↓
JavaScript Response Handler
    ├─ Check success flag
    ├─ Display alert message
    └─ Close modal on success
    ↓
User Sees Results
```

## Security Considerations

### CSRF Protection
```javascript
// Frontend retrieves token from DOM
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
const token = csrfToken ? csrfToken.value : '';

// Frontend sends token in header
headers: {
    'X-CSRFToken': token
}

// Django middleware validates token automatically
```

### Password Security
```python
# Never send passwords in plain text over HTTP (use HTTPS in production)
current_password = request.POST.get('currentPassword', '')

# Verify password using Django's secure method
if not request.user.check_password(current_password):
    # Password incorrect - return error

# Set password using Django's secure method (hashes with PBKDF2)
request.user.set_password(new_password)
request.user.save()
```

### Input Validation
```python
# Server-side validation is ALWAYS performed
# Never trust client-side validation alone

# Validate email uniqueness
if Faculty.objects.filter(email=email).exclude(id=faculty.id).exists():
    errors.append('This email is already in use')

# Validate password strength
if len(new_password) < 6:
    errors.append('New password must be at least 6 characters long')

# Return all errors to client
if errors:
    return JsonResponse({
        'success': False,
        'errors': errors
    }, status=400)
```

## Common Modifications

### To add a new field:
1. Add field to Faculty model (if not present)
2. Update form HTML to include new input
3. Add field to JavaScript form extraction
4. Add field to FormData in JavaScript
5. Add validation in backend view
6. Add field to database update code

### To change password requirements:
1. Update validation message in JavaScript (line ~362)
2. Update validation check in backend (line ~2556)
3. Update testing guide with new requirements

### To add file upload:
1. Add ImageField to Faculty model
2. Create media directory in settings.py
3. Handle file in backend view (currently has TODO comment)
4. Add file display/preview in frontend
