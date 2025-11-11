# 🧪 Auto-Schedule Generation - Test Scenarios

**Version:** 2.0  
**Date:** November 11, 2025  
**Purpose:** Validate auto-schedule generation behavior

---

## Test Environment Setup

### Prerequisites
```
✅ Django server running: python manage.py runserver
✅ Database populated with:
   - At least 1 curriculum
   - At least 5-10 courses with various lecture/lab hours
   - At least 3-5 faculty members (with specializations if possible)
   - At least 4-6 rooms (mix of lecture and lab types)
   - At least 1 section
```

### Access Point
```
URL: http://localhost:8000/admin/schedule/
Or: /admin/dashboard/ → Schedule Management → Auto-Generate
```

---

## Test Cases

### TC-001: Single 1-Hour Lecture Course

**Objective:** Verify 1-hour lectures schedule on Monday only (online)

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=1, laboratory_hours=0
```

**Test Steps:**
1. Select section
2. Click "Generate Schedule"
3. Wait for completion
4. Review generated schedule

**Expected Result:**
```
✅ Exactly 1 schedule entry created
✅ Day: Monday (0)
✅ Duration: 1 hour (e.g., 07:30-08:30)
✅ Room: Lecture room
✅ Faculty: Any available faculty (prefer specialist)
✅ Notes: None (or info about alternatives)
```

**Pass/Fail:** _____

---

### TC-002: Single 2-Hour Lecture Course

**Objective:** Verify 2-hour lectures schedule on Tue/Thu (1 hour each)

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=2, laboratory_hours=0
```

**Test Steps:**
1. Generate schedule
2. Review results

**Expected Result:**
```
✅ Exactly 2 schedule entries created
✅ Entry 1: Tuesday (1), 1 hour
✅ Entry 2: Thursday (3), 1 hour
✅ Same room type or different (both lecture rooms)
✅ Faculty may be same or different
✅ No notes (or preference info)
```

**Pass/Fail:** _____

---

### TC-003: Single 3-Hour Lecture Course (Test Default Option)

**Objective:** Verify 3-hour lectures default to Mon/Wed/Fri (1 hour each)

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=3, laboratory_hours=0
```

**Test Steps:**
1. Generate schedule
2. Review schedule grid
3. Check confirmation modal notes

**Expected Result:**
```
✅ Exactly 3 schedule entries created
✅ Entry 1: Monday (0), 1 hour
✅ Entry 2: Wednesday (2), 1 hour
✅ Entry 3: Friday (4), 1 hour
✅ All lecture rooms
✅ Blue notes box shows: "Can also be Tuesday/Thursday (1.5 hrs each)"
```

**Pass/Fail:** _____

---

### TC-004: Single 3-Hour Lecture (Verify Alternative Note)

**Objective:** Verify alternative scheduling option is noted for 3-hour courses

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=3, laboratory_hours=0
```

**Test Steps:**
1. Generate schedule
2. Look at confirmation modal
3. Check browser console logs (press F12)

**Expected Result:**
```
✅ Modal shows blue "Scheduling Notes" section
✅ Contains text: "MANUAL OPTION: [Course] can also be scheduled as Tuesday/Thursday (1.5 hrs each)"
✅ Console logs: "📌 MANUAL OPTION: ..."
✅ Schedule still shows Mon/Wed/Fri
```

**Pass/Fail:** _____

---

### TC-005: Single 4-Hour Lecture Course

**Objective:** Verify 4-hour lectures schedule on Mon/Tue/Thu/Fri

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=4, laboratory_hours=0
```

**Test Steps:**
1. Generate schedule
2. Review all 4 entries

**Expected Result:**
```
✅ Exactly 4 schedule entries created
✅ Entry 1: Monday (0), 1 hour
✅ Entry 2: Tuesday (1), 1 hour
✅ Entry 3: Thursday (3), 1 hour
✅ Entry 4: Friday (4), 1 hour
✅ All lecture rooms
✅ No Wednesday (intentionally skipped)
```

**Pass/Fail:** _____

---

### TC-006: Laboratory Only (3 Hours)

**Objective:** Verify laboratory never schedules on Monday, always 3 hours

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=0, laboratory_hours=3
Faculty: Assign at least 1 specialist
Rooms: Ensure at least 1 lab room exists
```

**Test Steps:**
1. Generate schedule
2. Check the lab schedule entry
3. Check notes

**Expected Result:**
```
✅ Exactly 1 schedule entry created
✅ Day: NOT Monday (should be 1-5: Tue-Sat)
✅ Preferred: Tuesday-Friday (1-4)
✅ Duration: 3 hours (e.g., 13:00-16:00)
✅ Room: Laboratory type (not lecture)
✅ Notes: "lab: 3 hours scheduled. Admin can manually split if needed."
```

**Pass/Fail:** _____

---

### TC-007: Mixed Lecture + Lab Course

**Objective:** Verify combined lecture and lab scheduling

**Setup:**
```
Section: Any section
Course: Create with lecture_hours=2, laboratory_hours=3
```

**Test Steps:**
1. Generate schedule
2. Count total entries
3. Review each entry

**Expected Result:**
```
✅ Exactly 3 schedule entries total
✅ Lecture entries (2):
   - Entry 1: Tuesday (1), 1 hour, Lecture room
   - Entry 2: Thursday (3), 1 hour, Lecture room
✅ Lab entry (1):
   - Entry 3: NOT Monday, 3 hours, Lab room
✅ Combined notes for lab split option
```

**Pass/Fail:** _____

---

### TC-008: Conflict Prevention - Faculty

**Objective:** Verify system prevents faculty from teaching overlapping times

**Setup:**
```
Section: Create a section
Courses: Create 2 courses with 3 lecture hours each
Faculty: Create or assign 1 faculty member to both courses
Rooms: Ensure enough lecture rooms available
```

**Test Steps:**
1. Generate schedule for this section
2. Check if any faculty has overlapping times

**Expected Result:**
```
✅ All schedules created successfully
✅ Same faculty NOT at same time on same day
✅ Successful conflict avoidance (no error modal)
✅ Faculty properly distributed across times
```

**Pass/Fail:** _____

---

### TC-009: Conflict Prevention - Room

**Objective:** Verify system prevents room double-booking

**Setup:**
```
Section: Any section
Courses: Create 3 courses with varied hours
Rooms: Limit rooms (e.g., 2 lecture rooms only)
```

**Test Steps:**
1. Generate schedule
2. Check if any room has overlapping times

**Expected Result:**
```
✅ All schedules created
✅ No room double-booked at same time
✅ Rooms properly distributed or reused at non-overlapping times
```

**Pass/Fail:** _____

---

### TC-010: Conflict Prevention - Section

**Objective:** Verify section cannot have overlapping class times

**Setup:**
```
Section: Any section
Courses: Multiple courses for this section
```

**Test Steps:**
1. Generate schedule
2. Review section schedule grid

**Expected Result:**
```
✅ No time slots with multiple courses for same section
✅ Each time slot on grid shows max 1 color (1 course)
✅ No overlaps visible in schedule grid
```

**Pass/Fail:** _____

---

### TC-011: Room Type Matching - Lecture

**Objective:** Verify lectures only use lecture-type rooms

**Setup:**
```
Section: Any section
Courses: Create 2 lecture courses (3 hrs each)
Rooms: Mix of lecture and lab rooms
```

**Test Steps:**
1. Generate schedule
2. Check room assignments

**Expected Result:**
```
✅ All lecture schedules use room_type='lecture'
✅ No lecture schedule uses room_type='laboratory'
✅ Lecture rooms properly allocated
```

**Pass/Fail:** _____

---

### TC-012: Room Type Matching - Laboratory

**Objective:** Verify labs only use lab-type rooms

**Setup:**
```
Section: Any section
Courses: Create 1-2 courses with lab hours
Rooms: Mix of lecture and lab rooms
```

**Test Steps:**
1. Generate schedule
2. Check lab room assignments

**Expected Result:**
```
✅ All lab schedules use room_type='laboratory'
✅ No lab schedule uses room_type='lecture'
✅ Lab rooms properly allocated
```

**Pass/Fail:** _____

---

### TC-013: Faculty Specialization Preference

**Objective:** Verify system prefers specialist faculty

**Setup:**
```
Section: Any section
Course: Create a course
Faculty: 
  - Faculty A: Add this course to specialization
  - Faculty B: No specialization in this course
Ensure both available
```

**Test Steps:**
1. Generate schedule multiple times (regenerate 3-5 times)
2. Check faculty assignments

**Expected Result:**
```
✅ Most attempts assign Faculty A (specialist)
✅ Some attempts may use Faculty B (fallback)
✅ Specialist strongly preferred (>80% of time)
✅ Shows intelligent matching
```

**Pass/Fail:** _____

---

### TC-014: Error Handling - No Courses

**Objective:** Verify proper error when section has no courses

**Setup:**
```
Section: Create empty section (no courses assigned)
```

**Test Steps:**
1. Try to generate schedule

**Expected Result:**
```
✅ Error modal appears
✅ Error message: "No courses found for this section configuration."
✅ No schedules created
✅ Section status remains unchanged
```

**Pass/Fail:** _____

---

### TC-015: Error Handling - No Rooms

**Objective:** Verify behavior when insufficient rooms available

**Setup:**
```
Section: Section with many courses
Rooms: 0 available rooms (delete all or filter out)
```

**Test Steps:**
1. Generate schedule
2. Check results

**Expected Result:**
```
✅ Attempts to generate but may fail
✅ Should show warning notes for failed schedules
✅ Schedules created: 0 or partial
✅ Warning: "Could not auto-schedule [Course] - please schedule manually"
```

**Pass/Fail:** _____

---

### TC-016: Manual Edit After Generation

**Objective:** Verify generated schedules can be edited

**Setup:**
```
Section: Any section with generated schedules
```

**Test Steps:**
1. Generate schedule (TC-003 recommended: 3-hour course)
2. Click on a generated schedule block
3. Edit: Change day from Monday to Tuesday
4. Save changes

**Expected Result:**
```
✅ Edit modal opens for selected schedule
✅ Can change day/time/faculty/room
✅ Changes save successfully
✅ Schedule grid updates immediately
✅ Manual override works (can violate auto rules)
```

**Pass/Fail:** _____

---

### TC-017: Regenerate Clears Previous

**Objective:** Verify "Regenerate" button clears previous schedules

**Setup:**
```
Section: Generate initial schedule
```

**Test Steps:**
1. Generate schedule (note count, e.g., "5 entries")
2. Note specific schedule details
3. Click "Regenerate" button
4. Confirm if prompted
5. Compare results

**Expected Result:**
```
✅ Previous schedules cleared
✅ New schedules generated
✅ Total count may differ (5 → 4, etc. due to randomness)
✅ No duplicate schedules
✅ Old times/days no longer visible
```

**Pass/Fail:** _____

---

### TC-018: Scheduling Notes Display

**Objective:** Verify scheduling notes appear correctly in UI

**Setup:**
```
Section: Create with:
  - 1 course with 3 lecture hours (to trigger alternative note)
  - 1 course with 3 lab hours (to trigger split note)
```

**Test Steps:**
1. Generate schedule
2. Check confirmation modal
3. Open browser console (F12)
4. Review both UI and console

**Expected Result:**
```
✅ Blue "Scheduling Notes" box appears in modal
✅ Contains:
   - "MANUAL OPTION: ... Tuesday/Thursday (1.5 hrs each)"
   - "lab: 3 hours scheduled. Admin can manually split if needed."
✅ Console shows: "📌 MANUAL OPTION: ..."
✅ Console shows: "📌 [Course] lab: 3 hours..."
```

**Pass/Fail:** _____

---

### TC-019: Large Section (Stress Test)

**Objective:** Verify system handles large course loads efficiently

**Setup:**
```
Section: Create or use existing with many courses
Courses: 10+ courses with mix of lecture/lab hours
Rooms: 5-8 rooms available
Faculty: 5-10 faculty available
```

**Test Steps:**
1. Generate schedule
2. Measure time taken
3. Check total schedules created
4. Verify no critical errors

**Expected Result:**
```
✅ Completes in reasonable time (<10 seconds)
✅ Most/all courses scheduled (>90%)
✅ No database errors
✅ Response time < 10 seconds
✅ All conflicts prevented
```

**Pass/Fail:** _____

---

### TC-020: API Response Format

**Objective:** Verify API response contains correct data

**Setup:**
```
Browser console open (F12)
Network tab open
```

**Test Steps:**
1. Generate schedule
2. Check Network tab → /admin/schedule/generate/ → Response
3. Verify JSON structure

**Expected Result:**
```json
✅ Response contains:
{
  "success": true,
  "message": "Successfully generated X schedule entries",
  "schedules_created": <number>,
  "notes": [
    "note1",
    "note2",
    ...
  ],
  "section_id": <number>
}

✅ No "conflicts" field (v1 format)
✅ "notes" array properly formatted
✅ HTTP 200 status
```

**Pass/Fail:** _____

---

## Test Report Summary

### Execution Checklist

| TC # | Test Name | Status | Notes |
|------|-----------|--------|-------|
| 001 | 1-Hour Lecture | _____ | _____ |
| 002 | 2-Hour Lecture | _____ | _____ |
| 003 | 3-Hour Lecture Default | _____ | _____ |
| 004 | 3-Hour Lecture Alternative | _____ | _____ |
| 005 | 4-Hour Lecture | _____ | _____ |
| 006 | Laboratory Only | _____ | _____ |
| 007 | Mixed Lecture+Lab | _____ | _____ |
| 008 | Faculty Conflict | _____ | _____ |
| 009 | Room Conflict | _____ | _____ |
| 010 | Section Conflict | _____ | _____ |
| 011 | Lecture Room Type | _____ | _____ |
| 012 | Lab Room Type | _____ | _____ |
| 013 | Specialist Preference | _____ | _____ |
| 014 | No Courses Error | _____ | _____ |
| 015 | No Rooms Error | _____ | _____ |
| 016 | Manual Edit | _____ | _____ |
| 017 | Regenerate | _____ | _____ |
| 018 | Notes Display | _____ | _____ |
| 019 | Large Section | _____ | _____ |
| 020 | API Response | _____ | _____ |

### Results Summary

**Total Tests:** 20  
**Passed:** ___  
**Failed:** ___  
**Skipped:** ___  

**Overall Status:** ☐ PASS  ☐ FAIL  ☐ PARTIAL

---

## Bug Report Template (if needed)

```
Title: [Brief description]
Severity: 🔴 Critical / 🟡 Major / 🟢 Minor
Test Case: TC-###

Description:
[What happened]

Expected:
[What should happen]

Actual:
[What actually happened]

Steps to Reproduce:
1. ...
2. ...
3. ...

Environment:
- Django version: 5.2.5
- Python: 3.12.6
- Browser: [if UI related]

Attachments:
[Screenshots/logs if applicable]
```

---

## Notes for Testers

1. **Randomness:** Each generation may produce slightly different schedules (within same rules)
2. **Faculty availability:** No real availability checking - all faculty treated as free
3. **Time zones:** All times in 24-hour format (local server time)
4. **Reset state:** Use Regenerate to clear and restart
5. **Manual changes:** Persist immediately (no separate save button)
6. **Browser cache:** Clear if seeing old UI after updates

---

**Test Date:** _______________  
**Tester Name:** _______________  
**Signature:** _______________
