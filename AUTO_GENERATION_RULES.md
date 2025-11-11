# Auto-Generation Scheduling Algorithm Documentation

## Overview
The auto-generation system intelligently schedules courses based on lecture and laboratory hours with specific rules prioritizing student preferences and avoiding conflicts.

---

## Scheduling Rules

### 1. LECTURE SCHEDULING

#### 1-Hour Lecture
- **Schedule**: Monday only (online)
- **Time slots**: 1-hour slots (7:30-8:30, 8:30-9:30, etc.)
- **Room**: Lecture rooms
- **Note**: Online class on Monday

#### 2-Hour Lecture
- **Schedule**: Tuesday & Thursday (1 hour each)
- **Time slots**: 1-hour slots
- **Room**: Lecture rooms
- **Preference**: Tuesday-Friday (students prefer weekdays)

#### 3-Hour Lecture (Default)
- **Option 1 (AUTO)**: Monday, Wednesday, Friday (1 hour each)
  - Monday: Online (1 hour)
  - Wednesday: Lecture room (1 hour)
  - Friday: Lecture room (1 hour)
- **Option 2 (MANUAL)**: Tuesday, Thursday (1.5 hours each)
  - Use this if more concentrated schedule preferred
  - Can be manually adjusted after generation

#### 4-Hour Lecture
- **Schedule**: Monday, Tuesday, Thursday, Friday (1 hour each)
- **Time slots**: 1-hour slots
- **Room**: Lecture rooms
- **Pattern**: Avoids Wednesdays to prevent mid-week overload

---

### 2. LABORATORY SCHEDULING

#### Fixed 3-Hour Sessions
- **Cannot be on**: Monday (online-only day)
- **Preferred days**: Tuesday-Friday (students don't like Saturday)
- **Time slots**: 3-hour continuous blocks
- **Room type**: Laboratory rooms only
- **Default duration**: 3 hours
- **Can be split**: Admins can manually split into multiple sessions if needed

#### Laboratory Constraints
- ✅ Can be split by admin (e.g., 1.5hr + 1.5hr)
- ❌ Cannot be auto-assigned to Monday
- ❌ Cannot be shortened unless manually edited
- ⚠️ Will show admin notes if auto-scheduling failed

---

## Day Priority Order

1. **Monday**: Lecture-only, online, 1 hour max per course
2. **Tuesday-Friday**: Preferred for all classes (highest priority)
3. **Saturday**: Fallback only, shown as note if used (students avoid)

---

## Faculty Assignment

- **Preferred**: Faculty specialists (faculty with course in specialization)
- **Fallback**: Any available faculty if no specialists exist
- **Conflict check**: Prevents faculty from having overlapping schedules

---

## Room Assignment

### Lecture Classes
- Uses lecture-type rooms only
- Prevents double-booking

### Laboratory Classes
- Uses laboratory-type rooms only
- 3-hour continuous blocks
- Avoids Monday entirely

---

## Conflict Detection

The algorithm checks and prevents:
- ✅ **Section conflicts**: Same section cannot have overlapping times
- ✅ **Faculty conflicts**: Faculty cannot teach at overlapping times
- ✅ **Room conflicts**: Rooms cannot be booked for overlapping times
- ✅ **Day constraints**: Laboratory never on Monday
- ✅ **Room type matching**: Labs only in lab rooms, lectures in lecture rooms

---

## Algorithm Behavior

### Scheduling Notes Generated
The system generates notes in these scenarios:

1. **3-Hour Lecture Alternatives**:
   - "MANUAL OPTION: [Course Code] can also be scheduled as Tuesday/Thursday (1.5 hrs each)"

2. **Laboratory Splitting**:
   - "[Course Code] lab: 3 hours scheduled. Admin can manually split if needed."

3. **Failed Scheduling**:
   - "WARNING: Could not auto-schedule [Course Code] lab (3 hours). Please schedule manually."

### UI Notification
- ✅ Success message shows number of schedules created
- ℹ️ Notes displayed in blue info box in confirmation modal
- 📌 All notes also logged to browser console

---

## How to Use

### Auto-Generate a Schedule
1. Navigate to `/admin/schedule/` 
2. Select a section
3. Click "Generate Schedule"
4. Review the generated schedule
5. Check notes for manual options and warnings

### Manual Adjustments
After auto-generation, you can:
- ✏️ Edit any schedule block to change time/day/faculty/room
- 🔄 Regenerate if not satisfied (clears previous schedules)
- ➕ Add additional sessions manually for specific courses
- ✂️ Split laboratory sessions if desired

### Monday Online Policy
- All 1-hour lectures default to Monday (online)
- Cannot be changed by auto-generation (manual edit only)
- Helps reduce on-campus congestion

---

## Examples

### Example 1: 3-Credit Course (3 Lecture Hours)
```
AUTO-GENERATED:
- Monday 7:30-8:30 (Lecture Room) - Online
- Wednesday 9:00-10:00 (Lecture Room)
- Friday 10:00-11:00 (Lecture Room)

MANUAL ALTERNATIVE:
- Tuesday 13:00-14:30 (Lecture Room)
- Thursday 13:00-14:30 (Lecture Room)
```

### Example 2: 3-Credit Course with Lab (3 Lecture + 3 Lab Hours)
```
LECTURES (AUTO):
- Monday 7:30-8:30 (Online)
- Wednesday 8:30-9:30 (Lecture Room)
- Friday 9:30-10:30 (Lecture Room)

LABORATORY (AUTO):
- Tuesday 13:00-16:00 (Laboratory Room)
  [Admin can split into 1.5+1.5 if needed]
```

### Example 3: 2-Credit Course (2 Lecture Hours)
```
AUTO-GENERATED:
- Tuesday 10:00-11:00 (Lecture Room)
- Thursday 10:00-11:00 (Lecture Room)
```

---

## Algorithm Improvements Over Previous Version

| Feature | Previous | Current |
|---------|----------|---------|
| Monday handling | Random | Always online, lecture-only |
| Lab scheduling | Random day (could be Monday) | Never Monday, Tue-Fri preferred |
| Student preferences | None | Prioritizes Tue-Fri, avoids Sat |
| Hour distribution | Assumed 1.5-2hr blocks | Exact hour-based rules |
| 3-hour courses | Random times | Multiple intelligent options |
| Lab flexibility | Fixed 3hrs | Can split with admin note |
| Scheduling notes | None | Detailed notes for manual options |

---

## Technical Details

### Time Slot Definitions
- **1-hour slots**: 7:30-8:30, 8:30-9:30, 9:30-10:30, etc. (14 slots)
- **1.5-hour slots**: 7:30-9:00, 9:00-10:30, 10:30-12:00, etc. (8 slots)
- **2-hour slots**: 7:30-9:30, 9:30-11:30, 13:00-15:00, etc. (6 slots)
- **3-hour slots**: 7:30-10:30, 10:30-13:30, 13:00-16:00, etc. (5 slots)

### Day Numbering (0-5)
- 0 = Monday
- 1 = Tuesday
- 2 = Wednesday
- 3 = Thursday
- 4 = Friday
- 5 = Saturday

### Room Types
- `lecture` = Classroom/lecture hall
- `laboratory` = Lab/practicum room

---

## Known Limitations & Future Enhancements

### Current Limitations
- ⚠️ Does not consider faculty preference/specialization time availability
- ⚠️ Cannot check for holidays/exam days
- ⚠️ No buffer time between classes for faculty
- ⚠️ Cannot handle special time requirements (early morning/late evening only)

### Future Enhancements
- 🔮 Faculty availability calendar integration
- 🔮 Holiday and exam calendar support
- 🔮 Configurable lunch break times
- 🔮 Faculty preference for specific days
- 🔮 Load balancing (even distribution across week)
- 🔮 Student preference tracking
- 🔮 Export schedule conflicts report

---

## Support & Troubleshooting

### Issue: Laboratory not scheduled
- Check if lab rooms are available
- Check if faculty/room scheduling conflicts exist
- Manually schedule if auto-generation fails

### Issue: All courses on Tuesday-Friday
- This is normal for 2-hour courses
- Distribute manually to different days if needed

### Issue: Monday always has classes
- This is by design (1-hour lectures default to Monday online)
- Edit manually to change

### Issue: Saturday schedules generated
- This is fallback behavior when Tue-Fri fully booked
- Consider adding more rooms or time slots
- Manually move to Tue-Fri if possible

---

## Contact & Questions
For questions about the auto-generation algorithm, refer to the `generate_schedule()` function in `hello/views.py`.
