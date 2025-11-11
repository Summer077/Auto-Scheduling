# 🎓 Auto-Generate Schedule - Quick Reference Guide

## Fast Facts

| Question | Answer |
|----------|--------|
| **When is Monday used?** | Online lectures only (1-2 hours max) |
| **Best days for classes?** | Tuesday-Friday (students prefer) |
| **Can labs be on Monday?** | ❌ NO - Never on Monday |
| **How long is a lab?** | 3 hours (can be split manually) |
| **How are 3-hour lectures scheduled?** | Mon/Wed/Fri (1hr each) + TUE/THU option (1.5hr each) |
| **Can I change generated schedules?** | ✅ YES - Click any block to edit |
| **How do I regenerate?** | Click "Regenerate" button in modal (clears previous) |

---

## 📅 Default Schedules Generated

### 1-Hour Lecture Course
```
Monday 7:30-8:30  (Online, Lecture Room)
```

### 2-Hour Lecture Course
```
Tuesday   10:00-11:00 (Lecture Room)
Thursday  10:00-11:00 (Lecture Room)
```

### 3-Hour Lecture Course
```
Monday    7:30-8:30   (Online, Lecture Room)
Wednesday 9:00-10:00  (Lecture Room)
Friday    10:00-11:00 (Lecture Room)

NOTE: Can also be Tue/Thu 1.5hrs each (see modal notes)
```

### 4-Hour Lecture Course
```
Monday    7:30-8:30   (Online, Lecture Room)
Tuesday   8:30-9:30   (Lecture Room)
Thursday  9:30-10:30  (Lecture Room)
Friday    10:30-11:30 (Lecture Room)
```

### 3-Hour Laboratory
```
Tuesday 13:00-16:00 (Lab Room)

NOTE: Can be split into 1.5+1.5 hours if needed
```

---

## ⚙️ How to Generate a Schedule

### Step 1: Select Section
```
Go to: /admin/schedule/
Select: Your section from dropdown
```

### Step 2: Click Generate
```
Click: "Generate Schedule" button
Wait: For generation to complete (~2-5 seconds)
```

### Step 3: Review Results
```
See: All generated schedules in right panel
See: Blue notes modal with scheduling info
See: Success message showing count
```

### Step 4: Edit if Needed
```
Click: Any schedule block to edit
Change: Time, Day, Faculty, Room
Save: Changes applied immediately
```

### Step 5: Regenerate if Not Happy
```
Click: "Regenerate" button
Confirm: Previous schedules will be deleted
Result: Fresh schedule created
```

---

## 🎯 Schedule Generation Logic

### Lecture Hour Distribution

| Hours | Default | Alternative | Room |
|-------|---------|-------------|------|
| **1 hr** | Mon only | No option | Lecture |
| **2 hrs** | Tue + Thu (1hr each) | No option | Lecture |
| **3 hrs** | Mon + Wed + Fri (1hr each) | Tue + Thu (1.5hr each) | Lecture |
| **4 hrs** | Mon + Tue + Thu + Fri (1hr each) | No option | Lecture |

### Laboratory Guidelines

| Item | Value |
|------|-------|
| **Default Duration** | 3 hours continuous |
| **Allowed Days** | Tue, Wed, Thu, Fri (NOT Mon/Sat) |
| **Preferred Days** | Tue-Fri (tries these first) |
| **Fallback Days** | Saturday (only if needed) |
| **Room Type** | Laboratory only |
| **Can Split?** | Yes, manually after generation |

---

## 📝 Understanding Schedule Notes

When you see these notes, here's what they mean:

### 📌 Info Note (Blue Box)
```
"Course XYZ: 3 lecture hours (Tue/Thu, 1.5hr each - Option 2)"

Meaning: 
- System generated Mon/Wed/Fri version
- You can manually change to Tue/Thu version instead
- Both are valid options
```

### ✏️ Lab Split Note
```
"[Course] lab: 3 hours scheduled. Admin can manually split if needed."

Meaning:
- Lab is 3 hours continuous (default)
- You can click it and change to split sessions
- Example: 1.5hrs + 1.5hrs on different days
```

### ⚠️ Warning Note
```
"WARNING: Could not auto-schedule [Course] lab. Please schedule manually."

Meaning:
- System couldn't find a free slot automatically
- No faculty/room available in that time
- Click [+] to manually add this schedule
```

---

## ✏️ Manual Editing After Generation

### Click a Schedule to Edit
```
Action: Click any colored schedule block
Result: Edit modal opens
Fields:
  - Day: Change which day
  - Start Time: Change start hour
  - End Time: Change end hour
  - Faculty: Change professor
  - Room: Change classroom/lab
```

### Quick Examples

**Change 3-Hour Lecture from Mon/Wed/Fri to Tue/Thu**
1. Click Monday schedule
2. Delete it
3. Click Tuesday schedule for same course
4. Edit to 13:00-14:30 (1.5 hours)
5. Create new Thursday schedule 13:00-14:30

**Split a 3-Hour Lab into Two Sessions**
1. Click the 3-hour lab block
2. Change it to 1.5 hours (e.g., 13:00-14:30)
3. Add new schedule for same course
4. Set to another day, 1.5 hours (e.g., Thu 15:00-16:30)

---

## ⚡ Pro Tips

### Tip 1: Monday = Online
```
✅ All Monday 1-hour lectures are online
✅ No need for classroom (or use video room)
✅ Helps reduce on-campus crowding
```

### Tip 2: Concentrate Popular Days
```
✅ System prioritizes Tue-Fri for classes
✅ Fewer on Monday (online only)
✅ Saturday is emergency fallback
```

### Tip 3: Regenerate Safely
```
✅ "Regenerate" button clears old schedule
✅ Creates completely new one
✅ Use if you don't like the first attempt
✅ No backups - make notes first if you like something!
```

### Tip 4: Lab Flexibility
```
✅ All labs start as 3 hours
✅ Split them if needed (e.g., 1.5+1.5)
✅ Different days for different sessions
✅ Same room or different rooms OK
```

### Tip 5: Check Conflicts
```
✅ System prevents:
   - Same room double-booking
   - Faculty teaching 2 classes same time
   - Same class at same time
✅ If generation fails: May be no free slots
✅ Solution: Add more rooms or time slots, regenerate
```

---

## 🆘 Troubleshooting

### Problem: Saturday schedules appearing
**Cause:** All Tue-Fri slots full
**Solution:** 
1. Add more rooms
2. Add more time slots
3. Manually spread out some courses
4. Regenerate

### Problem: Lab not scheduled
**Cause:** No lab rooms available or all booked
**Solution:**
1. Check if lab rooms exist
2. Add lab room if missing
3. Check conflicts with other courses
4. Manually schedule if needed

### Problem: Same professor teaching at same time
**Cause:** System couldn't find non-conflicting slot
**Solution:**
1. Add more faculty
2. Manually adjust some schedules
3. Reduce faculty teaching load

### Problem: 3-hour lecture on all different days
**Expected:** Mon + Wed + Fri (concentrated)
**If different:** Regenerate and try again

---

## 📊 Ideal Section Schedule Example

### Sample Section: IT101 (5 courses)

```
MONDAY (Online Day)
├─ 07:30-08:30  Intro to IT (Lecture)
├─ 08:30-09:30  Comp Ethics (Lecture)
└─ 09:30-10:30  Data Basics (Lecture)

TUESDAY
├─ 10:00-11:00  Advanced DB (Lecture 1/2)
└─ 13:00-16:00  Database Lab (3 hours)

WEDNESDAY
├─ 09:00-10:00  Intro to IT (Lecture 2/3)
├─ 10:00-11:00  Data Basics (Lecture 2/3)
└─ 13:00-14:30  Networking (Lecture 1/2)

THURSDAY
├─ 10:00-11:00  Advanced DB (Lecture 2/2)
├─ 11:00-12:00  Comp Ethics (Lecture 2/2)
└─ 13:00-14:30  Networking (Lecture 2/2)

FRIDAY
├─ 10:00-11:00  Intro to IT (Lecture 3/3)
└─ 11:00-12:00  Data Basics (Lecture 3/3)

SATURDAY
└─ Empty (students prefer no Saturday classes)
```

**Why This Works:**
- ✅ Monday has only online 1-hour lectures
- ✅ Concentrated Tue-Fri (students prefer)
- ✅ Labs on Tuesday (not Monday)
- ✅ No Saturday scheduling (high student satisfaction)
- ✅ Even distribution throughout week
- ✅ Different professors/rooms, no conflicts

---

## 🔗 Related Features

- **Schedule Editor:** Click any block to edit details
- **Faculty Management:** Assign specializations to match courses
- **Room Management:** Ensure enough lecture and lab rooms exist
- **Curriculum Management:** Courses must match section's curriculum
- **Conflict Detection:** System prevents overlapping schedules automatically

---

## 💡 Best Practices

1. **Add enough rooms before generating**
   - Need both lecture and lab rooms
   - More rooms = better schedule

2. **Assign faculty specializations**
   - Help system match professors to courses
   - Improves schedule quality

3. **Check alternative options**
   - Read notes modal completely
   - Consider manual alternatives mentioned

4. **Test regeneration**
   - System randomizes within rules
   - Each run might produce slightly different (but valid) schedule
   - Regenerate until happy

5. **Document special requirements**
   - If course needs specific time: schedule manually
   - If course needs specific professor: add specialization
   - If course needs specific room: ensure room exists

---

**Version:** 2.0 - Intelligent Hour-Based Scheduling
**Last Updated:** November 2025
**System:** ASSIST Auto-Scheduling Platform
