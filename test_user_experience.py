import requests

# Fetch homepage as public user (anonymous)
r = requests.get('http://localhost:8069/?db=DenBell')

print("HTTP Status Code:", r.status_code)
print("Is old form present?:", ("<form id=\"dw-appt-form\"" in r.text or "id='dw-appt-form'" in r.text))
print("Is 'Treatment Interested In' present?:", ("Treatment Interested In" in r.text))
print("Is 'Preferred Date' present?:", ("Preferred Date" in r.text))
print("Is 'Additional Notes' present?:", ("Additional Notes" in r.text))

print("\nIs 6-Step Workflow present?:", ("dental-flow-wrapper" in r.text))
print("Is Step 1 (Welcome - New vs Returning) present?:", ("pane_step_1" in r.text and "New Patient" in r.text and "Returning Patient" in r.text))
print("Is Step 2 (Appointment Types) present?:", ("pane_step_2" in r.text and "Emergency Consultation" in r.text))
print("Is Step 3 (Dentists) present?:", ("pane_step_3" in r.text and "Devipriya" in r.text))
print("Is Step 4 (Calendar & Slots) present?:", ("pane_step_4" in r.text and "cal_days_grid" in r.text))
print("Is Step 5 (Patient Details) present?:", ("pane_step_5" in r.text and "ret_identifier_input" in r.text))
print("Is Step 6 (Review & Confirm) present?:", ("pane_step_6" in r.text and "btn_confirm_booking" in r.text))
print("Is Success Screen present?:", ("pane_step_success" in r.text))

# Check navigation links:
for line in r.text.splitlines():
    if 'Book Appointment' in line and '<a ' in line:
        print("Navbar / CTA Link:", line.strip())
