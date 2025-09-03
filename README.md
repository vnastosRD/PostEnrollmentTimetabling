# PostEnrollmentTimetabling

## Problem Description

Post-Enrollment Timetabling is a course scheduling method used mainly in universities and large educational institutions. Instead of creating the timetable first and forcing students to adapt, the PET approach collects students’ enrollment choices (courses, modules, or classes) before the timetable is generated. The scheduling system then uses these actual registrations to build a timetable that maximizes student satisfaction and resource usage.

**The problem's hard constraints are:**
* Each event must be scheduled in a timeslot and a room.
* Events with common students must be placed at different timeslots.
* A room can host at most one event in each timeslot.
* The capacity and feature requirements of each event must be met by the room that will eventually host it.
* Certain timeslot requirements may apply to specific events.
* There may be relationships of precedence between events.

**On the other hand, the soft constraints are:**
* A student attends an event at the last timeslot of a day.
* A student attends three (or more) events in a row on the same day.
* A student attends only one event in a day.
One penalty point is imposed for each of the conditions above.

## Penalty Calculation (Soft Constraints)

The total penalty is calculated as the sum of three types of violations
for all students across all days:

#### 1. Event in the last timeslot of a day
For each student `s`:
- +1 penalty for every event scheduled in the last timeslot of a day.

\[
P_{1}(s) = \sum_{e \in E_s} \mathbf{1}\{t(e) = \text{last}(d(e))\}
\]

---

#### 2. Three (or more) consecutive events in a day
For each student `s`:
- +1 penalty for every occurrence of three (or more) consecutive events
  on the same day.

\[
P_{2}(s) = \sum_{d} \sum_{\text{consecutive } (e_1,e_2,e_3) \subseteq E_s \text{ on day } d} \mathbf{1}\{\text{consecutive timeslots}\}
\]

---

#### 3. Only one event in a day
For each student `s`:
- +1 penalty if the student has exactly one event scheduled that day.

\[
P_{3}(s) = \sum_{d} \mathbf{1}\{|E_s \cap \{e : d(e) = d\}| = 1\}
\]

---

#### Total Penalty
The final penalty is the sum of all three components for all students:

\[
\text{Penalty} = \sum_{s \in S} \Big( P_{1}(s) + P_{2}(s) + P_{3}(s) \Big)
\]

## Solution Approach

## Datasets

## Statistics